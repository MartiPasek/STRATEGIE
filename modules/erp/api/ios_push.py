"""APNs push notifikace pro nativní iOS appku (STRATEGIE Mobil 1.84).

PROČ: Android má `DialPollService` — foreground službu, která se á 4–20 s ptá
`/app/{app_key}/commands/pending` a na každý NOVÝ příkaz vyrobí systémovou
notifikaci. iOS trvalý background polling nedovolí, ekvivalent té služby na
iPhonu existovat nemůže. Jediná cesta, jak dostat příkaz z `fw.mobile_command`
do notifikační lišty zavřené appky, je push z APNs.

CHOVÁNÍ JE ZÁMĚRNĚ STEJNÉ JAKO NA ANDROIDU (`DialPollService.checkCommands`
a `notifyCommand`):
  - notifikuje se KAŽDÝ pending příkaz, žádný filtr podle `command_type`;
  - každý příkaz JEN JEDNOU (Android drží `shownCommandIds` v paměti služby —
    tady je ekvivalentem tabulka `fw.ios_push_sent`, protože server na rozdíl
    od telefonu obsluhuje víc zařízení a restartuje se);
  - `claude_ok` jde tiše (Android má pro něj kanál `CH_OK` s IMPORTANCE_LOW),
    ostatní typy hlasitě (CH_CLAUDE / CH_COMMAND, IMPORTANCE_HIGH);
  - do payloadu se předává `screen`, `label` a u `open_url` i `url` — stejné
    klíče, jaké Android přebaluje do intentu pro `CommandActivity`.

Zrušení notifikace u vyřízeného příkazu (Android `cancelCommandNotif`) dělá
iOS klient sám: při přechodu do popředí si stáhne pending seznam a smaže
doručené notifikace, které v něm nejsou. Server na to nepotřebuje silent push
(ten APNs navíc agresivně škrtí).

Nastavení (core/config.py → .env):
  APNS_ENABLED=1
  APNS_KEY_P8=<obsah .p8 klíče, nebo cesta k souboru>
  APNS_KEY_ID=<Key ID z developer.apple.com>
  APNS_TEAM_ID=D3Y6Y63UMA
  APNS_TOPIC=cz.strategie.mobile

Jirka + Claude, 19. 8. 2026.
"""
from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

logger = logging.getLogger(__name__)

ios_push_router = APIRouter(prefix="/api/v1/erp", tags=["ios-push"])

# Kolik sekund mezi koly odesílací smyčky. Android pollne á 3–20 s podle
# `next_poll_s`; tady jde o jeden lehký dotaz na serveru (ne z telefonu),
# takže 5 s je levné a notifikace přijde prakticky hned.
POLL_S = 5

# Starší nedoručené příkazy už nemá smysl cinkat (appka je stejně ukáže v
# seznamu). Chrání i před lavinou po delším výpadku APNs.
MAX_STARI_MIN = 60

# Kolik příkazů odbavit v jednom kole — pojistka proti zahlcení.
DAVKA = 50

_APNS_PROD = "https://api.push.apple.com"
_APNS_SANDBOX = "https://api.sandbox.push.apple.com"

# stav scheduleru (proces-lokální, stejný vzor jako landmark_sched / mirror_sched)
_PUSH_TASK = [None]
_PUSH_STOP = [False]

# cache podepsaného JWT: (token, vydáno_v). Apple vyžaduje obnovu nejdřív po
# 20 minutách a nejpozději po hodině — držíme 50 minut.
_JWT_CACHE: dict = {"token": None, "iat": 0.0}

_DDL_TOKEN = """
CREATE TABLE IF NOT EXISTS fw.ios_push_token (
    id            bigserial PRIMARY KEY,
    user_id       integer NOT NULL,
    device_token  text NOT NULL UNIQUE,
    app_key       text NOT NULL DEFAULT 'mobile',
    platform      text NOT NULL DEFAULT 'ios',
    app_version   text,
    device_id     text,
    apns_env      text,
    active        boolean NOT NULL DEFAULT true,
    last_error    text,
    last_sent_at  timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
)
"""

_DDL_SENT = """
CREATE TABLE IF NOT EXISTS fw.ios_push_sent (
    command_id   bigint NOT NULL,
    device_token text NOT NULL,
    sent_at      timestamptz NOT NULL DEFAULT now(),
    ok           boolean NOT NULL DEFAULT true,
    detail       text,
    PRIMARY KEY (command_id, device_token)
)
"""


def ensure_tables(s) -> None:
    """Idempotentní založení tabulek (ve fw. se to tak dělá i jinde — viz
    centrala_form_spec.ensure_table; alembic drží jen tenant/public)."""
    s.execute(_t(_DDL_TOKEN))
    s.execute(_t(_DDL_SENT))
    s.execute(_t("CREATE INDEX IF NOT EXISTS ix_ios_push_token_user "
                 "ON fw.ios_push_token (user_id) WHERE active"))
    s.execute(_t("CREATE INDEX IF NOT EXISTS ix_ios_push_sent_at "
                 "ON fw.ios_push_sent (sent_at)"))


# ───────────────────────────── konfigurace ─────────────────────────────

def _z_trezoru(klic: str) -> str:
    """Přečte hodnotu z fw.app_secret. Tam leží i klíč trezoru (`vault_key`),
    takže je to zavedené místo pro tajemství, která nesmí do repa ani do gitu.

    PROČ TUDY a ne jen přes .env: soukromý APNs klíč vydá Apple JEN JEDNOU a
    platí pro celý tým. V databázi je na jednom místě pro obě instance, přežije
    redeploy i výměnu stroje a je v záloze — na rozdíl od `.env`, který se musí
    ručně donést na každý server a při reinstalaci se snadno ztratí."""
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            row = s.execute(_t("SELECT sval FROM fw.app_secret WHERE skey = :k"),
                            {"k": klic}).first()
            return (row[0] or "").strip() if row else ""
        finally:
            s.close()
    except Exception as exc:
        logger.warning("[ios_push] čtení %s z fw.app_secret selhalo: %s", klic, exc)
        return ""


def _cfg():
    """Nastavení APNs. Vrací (enabled, p8, key_id, team_id, topic).

    Klíč a identifikátory se berou přednostně z .env (Settings); co tam chybí,
    dohledá se v fw.app_secret pod `apns_key_p8` / `apns_key_id`. Díky tomu
    stačí na produkci nastavit APNS_ENABLED=1 a zbytek si server načte sám."""
    try:
        from core.config import settings as _s
    except Exception:
        return (False, "", "", "", "")
    p8 = (getattr(_s, "apns_key_p8", "") or "").strip()
    # Hodnota smí být buď rovnou obsah klíče, nebo cesta k .p8 souboru.
    if p8 and not p8.startswith("-----BEGIN"):
        try:
            with open(p8, "r", encoding="utf-8") as fh:
                p8 = fh.read()
        except Exception as exc:
            logger.warning("[ios_push] APNS_KEY_P8 ukazuje na nečitelný soubor: %s", exc)
            p8 = ""
    if not p8:
        p8 = _z_trezoru("apns_key_p8")
    key_id_cfg = (getattr(_s, "apns_key_id", "") or "").strip() or _z_trezoru("apns_key_id")
    return (
        bool(getattr(_s, "apns_enabled", False)),
        p8,
        key_id_cfg,
        (getattr(_s, "apns_team_id", "") or "").strip(),
        (getattr(_s, "apns_topic", "") or "").strip(),
    )


def _jwt(p8: str, key_id: str, team_id: str) -> str:
    """Podepsaný APNs provider token (ES256). Cachovaný na 50 minut."""
    now = time.time()
    if _JWT_CACHE["token"] and (now - _JWT_CACHE["iat"]) < 50 * 60:
        return _JWT_CACHE["token"]
    import jwt as _pyjwt
    tok = _pyjwt.encode(
        {"iss": team_id, "iat": int(now)},
        p8,
        algorithm="ES256",
        headers={"kid": key_id},
    )
    if isinstance(tok, bytes):  # pyjwt < 2 vracelo bytes
        tok = tok.decode("ascii")
    _JWT_CACHE["token"] = tok
    _JWT_CACHE["iat"] = now
    return tok


# ───────────────────────────── odeslání jedné notifikace ─────────────────────────────

def _payload(cmd: dict) -> tuple[dict, bool]:
    """Z řádku fw.mobile_command složí APNs payload. Vrací (payload, tichy).

    Mapa na Android `notifyCommand`: titulek, tělo, a z payloadu klíče
    `screen` / `label` / `url`. `claude_ok` = tichá notifikace."""
    ctype = (cmd.get("command_type") or "").strip()
    title = (cmd.get("title") or "Doporučení")[:120]
    body = (cmd.get("message") or "").strip() or "Klepni pro zobrazení"
    tichy = (ctype == "claude_ok")

    aps: dict = {
        "alert": {"title": title, "body": body[:600]},
        # Android používá u tichého kanálu IMPORTANCE_LOW → iOS ekvivalent je
        # passive (nerozsvítí displej, neudělá zvuk).
        "interruption-level": "passive" if tichy else "active",
        "thread-id": "mobile-command",
    }
    if not tichy:
        aps["sound"] = "default"

    out: dict = {"aps": aps, "cmd_id": cmd.get("id"), "type": ctype}

    pl = cmd.get("payload")
    if isinstance(pl, str):
        try:
            pl = json.loads(pl)
        except Exception:
            pl = None
    if isinstance(pl, dict):
        for klic in ("screen", "label"):
            hod = (pl.get(klic) or "")
            if isinstance(hod, str) and hod.strip():
                out[klic] = hod.strip()[:80]
        if ctype == "open_url":
            url = (pl.get("url") or "")
            if isinstance(url, str) and url.strip():
                out["url"] = url.strip()[:500]
    return out, tichy


async def _odeslat(klient, jwt_tok: str, topic: str, device_token: str,
                   payload: dict, tichy: bool, sandbox: bool):
    """Jedno POST na APNs. Vrací (status_code, reason)."""
    base = _APNS_SANDBOX if sandbox else _APNS_PROD
    r = await klient.post(
        f"{base}/3/device/{device_token}",
        content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "authorization": f"bearer {jwt_tok}",
            "apns-topic": topic,
            "apns-push-type": "alert",
            # Android dává tichému kanálu PRIORITY_LOW; APNs ekvivalent je 5.
            "apns-priority": "5" if tichy else "10",
            # Ekvivalent Android `setOnlyAlertOnce` + stabilní id notifikace:
            # opakovaný push k témuž příkazu přepíše ten původní.
            "apns-collapse-id": str(payload.get("cmd_id") or "")[:64],
            "content-type": "application/json",
        },
    )
    reason = ""
    if r.status_code != 200:
        try:
            reason = (r.json() or {}).get("reason") or r.text[:200]
        except Exception:
            reason = r.text[:200]
    return r.status_code, reason


# Trvale odmítnutí — příkaz na tohle zařízení nemá smysl zkoušet znovu.
# (Seznam důvodů: Apple, "Handling notification responses from APNs".)
_TRVALE = {
    "BadDeviceToken",          # token nepatří k tomuhle prostředí/topicu
    "DeviceTokenNotForTopic",
    "Unregistered",            # appka odinstalovaná
    "TopicDisallowed",
    "BadTopic",
    "PayloadTooLarge",
    "BadCollapseId",
    "BadMessageId",
    "BadPriority",
}

# Token zařízení už je k ničemu — vypnout ho.
_MRTVY_TOKEN = {"BadDeviceToken", "DeviceTokenNotForTopic", "Unregistered"}


def _trvala_chyba(kod: int, duvod: str) -> bool:
    """Má se příkaz odepsat, nebo ho příště zkusit znovu?

    Přechodné (429 TooManyRequests, 5xx, timeout, vypršelý provider token)
    ZÁMĚRNĚ nezapisujeme do fw.ios_push_sent — kdybychom je zapsali, notifikace
    by po jednom výpadku sítě nedorazila nikdy."""
    if kod == 410:
        return True
    if kod in (0, 429) or kod >= 500:
        return False
    if duvod in ("ExpiredProviderToken", "InternalServerError", "ServiceUnavailable",
                 "TooManyRequests", "TooManyProviderTokenUpdates"):
        return False
    return duvod in _TRVALE


# ───────────────────────────── odesílací kolo ─────────────────────────────

def _neodeslane(s, limit: int) -> list[dict]:
    """Pending příkazy, které mají adresáta s aktivním iOS tokenem a ještě
    nebyly na to zařízení odeslány. Jeden dotaz = jeden pár (příkaz, token)."""
    rows = s.execute(_t("""
        SELECT c.id, c.command_type, c.title, c.message, c.payload::text AS payload,
               t.device_token, t.apns_env
        FROM fw.mobile_command c
        JOIN fw.ios_push_token t
          ON t.user_id = c.target_user_id AND t.app_key = c.app_key AND t.active
        WHERE c.status = 'pending'
          AND c.created_at > now() - make_interval(mins => :stari)
          AND NOT EXISTS (SELECT 1 FROM fw.ios_push_sent p
                           WHERE p.command_id = c.id AND p.device_token = t.device_token)
        ORDER BY c.id ASC
        LIMIT :lim
    """), {"stari": MAX_STARI_MIN, "lim": limit}).mappings().all()
    return [dict(r) for r in rows]


def _zapsat_vysledek(s, command_id, device_token: str, ok: bool, detail: str) -> None:
    s.execute(_t("""
        INSERT INTO fw.ios_push_sent (command_id, device_token, ok, detail)
        VALUES (:c, :d, :ok, :det)
        ON CONFLICT (command_id, device_token) DO UPDATE
           SET sent_at = now(), ok = EXCLUDED.ok, detail = EXCLUDED.detail
    """), {"c": command_id, "d": device_token, "ok": ok, "det": (detail or "")[:300]})


def _zneplatnit_token(s, device_token: str, duvod: str) -> None:
    """Token, který APNs odmítlo natrvalo (appka odinstalovaná, cizí topic).
    Nechává řádek kvůli auditu, jen ho vypne."""
    s.execute(_t("UPDATE fw.ios_push_token SET active = false, last_error = :e, "
                 "updated_at = now() WHERE device_token = :d"),
              {"e": duvod[:300], "d": device_token})


async def push_tick() -> dict:
    """Jedno kolo: rozešle, co je nového. Vrací souhrn (pro test endpoint)."""
    enabled, p8, key_id, team_id, topic = _cfg()
    if not (enabled and p8 and key_id and team_id and topic):
        return {"ok": False, "error": "APNs není nastaveno (APNS_* v .env)"}

    from core.database_data import get_data_session as _g
    s = _g()
    try:
        ukoly = _neodeslane(s, DAVKA)
    except Exception as exc:
        s.close()
        logger.warning("[ios_push] výběr neodeslaných selhal: %s", exc)
        return {"ok": False, "error": str(exc)}
    if not ukoly:
        s.close()
        return {"ok": True, "odeslano": 0}

    import httpx
    jwt_tok = _jwt(p8, key_id, team_id)
    odeslano = chyb = 0
    try:
        async with httpx.AsyncClient(http2=True, timeout=10.0) as klient:
            for u in ukoly:
                payload, tichy = _payload(u)
                dt = u["device_token"]
                # Vývojové buildy (Xcode/TestFlight) mají token ze sandboxu,
                # App Store z produkce. Rozlišit se to z tokenu nedá — zkusíme
                # produkci a při BadDeviceToken sandbox; výsledek si u tokenu
                # zapamatujeme, ať se druhé kolo neopakuje.
                # Zapamatované prostředí určuje jen POŘADÍ pokusů, ne jedinou
                # možnost: telefon se z TestFlightu (sandbox) přeinstaluje na
                # App Store build (produkce) se stejným device_id, a token, co
                # včera chodil do sandboxu, je dnes produkční.
                poradi = [True, False] if u.get("apns_env") == "sandbox" else [False, True]
                kod = 0
                duvod = ""
                pouzity_sandbox = False
                for sandbox in poradi:
                    try:
                        kod, duvod = await _odeslat(klient, jwt_tok, topic, dt,
                                                    payload, tichy, sandbox)
                    except Exception as exc:
                        kod, duvod = 0, str(exc)[:200]
                    pouzity_sandbox = sandbox
                    # Druhé prostředí zkoušet jen tehdy, když odmítnutí bylo
                    # právě o prostředí; jinak nemá smysl posílat dvakrát.
                    if kod == 200 or duvod not in ("BadDeviceToken", "BadEnvironmentKeyInToken"):
                        break

                if kod == 200:
                    odeslano += 1
                    _zapsat_vysledek(s, u["id"], dt, True, "")
                    s.execute(_t("UPDATE fw.ios_push_token SET last_sent_at = now(), "
                                 "apns_env = :env, last_error = NULL, updated_at = now() "
                                 "WHERE device_token = :d"),
                              {"env": ("sandbox" if pouzity_sandbox else "production"), "d": dt})
                else:
                    chyb += 1
                    s.execute(_t("UPDATE fw.ios_push_token SET last_error = :e, "
                                 "updated_at = now() WHERE device_token = :d"),
                              {"e": f"{kod} {duvod}"[:300], "d": dt})
                    if _trvala_chyba(kod, duvod):
                        # Odepsáno — zapsat, ať se to nezkouší donekonečna.
                        _zapsat_vysledek(s, u["id"], dt, False, f"{kod} {duvod}")
                        if kod == 410 or duvod in _MRTVY_TOKEN:
                            _zneplatnit_token(s, dt, f"{kod} {duvod}")
                    else:
                        # Přechodné — příští kolo to zkusí znovu.
                        if duvod == "ExpiredProviderToken" or kod == 403:
                            _JWT_CACHE["token"] = None   # vynutit nový podpis
                        logger.info("[ios_push] prikaz %s zkusim znovu (%s %s)",
                                    u["id"], kod, duvod)
        s.commit()
    except Exception as exc:
        s.rollback()
        logger.warning("[ios_push] kolo selhalo: %s", exc)
        return {"ok": False, "error": str(exc)}
    finally:
        s.close()
    if odeslano or chyb:
        logger.info("[ios_push] odeslano=%s chyb=%s", odeslano, chyb)
    return {"ok": True, "odeslano": odeslano, "chyb": chyb}


async def _push_loop():
    import asyncio as _aio
    while not _PUSH_STOP[0]:
        try:
            await _aio.sleep(POLL_S)
            await push_tick()
        except _aio.CancelledError:
            break
        except Exception as e:
            logger.warning("[ios_push_loop] %s", e)


def ios_push_sched_start():
    """Spustí odesílací smyčku. Volá lifespan — JEN na primáru, aby se pushe
    neposílaly dvakrát (stejně jako mirror/att_sync)."""
    import asyncio as _aio
    enabled, p8, key_id, team_id, topic = _cfg()
    if not enabled:
        logger.info("[ios_push] vypnuto (APNS_ENABLED není 1) — smyčka nestartuje")
        return
    if not (p8 and key_id and team_id and topic):
        logger.warning("[ios_push] APNS_ENABLED=1, ale chybí klíč/KEY_ID/TEAM_ID/TOPIC — smyčka nestartuje")
        return
    if _PUSH_TASK[0] is not None and not _PUSH_TASK[0].done():
        return
    _PUSH_STOP[0] = False
    try:
        from core.database_data import get_data_session as _g
        s = _g()
        try:
            ensure_tables(s)
            s.commit()
        finally:
            s.close()
    except Exception as exc:
        logger.warning("[ios_push] zalozeni tabulek selhalo: %s", exc)
    try:
        _PUSH_TASK[0] = _aio.create_task(_push_loop())
        logger.info("[ios_push] odesilaci smycka nastartovana (kolo a %s s, topic=%s)", POLL_S, topic)
    except Exception as e:
        logger.warning("[ios_push] start smycky selhal: %s", e)


def ios_push_sched_stop_now():
    _PUSH_STOP[0] = True
    if _PUSH_TASK[0] is not None and not _PUSH_TASK[0].done():
        _PUSH_TASK[0].cancel()


# ───────────────────────────── endpointy ─────────────────────────────

@ios_push_router.post("/app/ios/push/register")
async def ios_push_register(req: Request) -> JSONResponse:
    """iOS appka hlásí svůj APNs device token. Autentizace cookie NEBO Bearer —
    stejně jako ostatní /app/* endpointy. Adresu volá `PushNotifications.swift`
    hned po `didRegisterForRemoteNotificationsWithDeviceToken`."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from core.database_data import get_data_session as _g
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    dt = (str(body.get("device_token") or "")).strip().lower()
    # APNs token je 64 hex znaků (u některých zařízení delší) — hrubá kontrola,
    # ať se do tabulky nedostane nesmysl z jiného klienta.
    if not dt or len(dt) < 32 or len(dt) > 200 or any(c not in "0123456789abcdef" for c in dt):
        return JSONResponse({"ok": False, "error": "neplatný device_token"}, status_code=400)
    app_key = (str(body.get("app_key") or "mobile")).strip()[:40] or "mobile"
    app_version = (str(body.get("app_version") or "")).strip()[:40]
    device_id = (str(body.get("device_id") or "")).strip()[:80]

    s = _g()
    try:
        ensure_tables(s)
        s.execute(_t("""
            INSERT INTO fw.ios_push_token
                   (user_id, device_token, app_key, platform, app_version, device_id, active)
            VALUES (:u, :d, :ak, 'ios', :av, :did, true)
            ON CONFLICT (device_token) DO UPDATE
               SET user_id = EXCLUDED.user_id,
                   app_key = EXCLUDED.app_key,
                   app_version = EXCLUDED.app_version,
                   device_id = EXCLUDED.device_id,
                   active = true,
                   last_error = NULL,
                   updated_at = now()
        """), {"u": int(uid), "d": dt, "ak": app_key, "av": app_version, "did": device_id})
        # Jeden telefon = jeden uživatel. Když se na zařízení přihlásí někdo
        # jiný, starý token téhož device_id vypneme, ať mu nechodí cizí
        # notifikace (Android tenhle problém nemá, token je vázaný na párování).
        if device_id:
            s.execute(_t("UPDATE fw.ios_push_token SET active = false, updated_at = now() "
                         "WHERE device_id = :did AND device_token <> :d AND active"),
                      {"did": device_id, "d": dt})
        s.commit()
        return JSONResponse({"ok": True})
    except Exception as exc:
        s.rollback()
        logger.exception("[ios_push_register] failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        s.close()


@ios_push_router.post("/app/ios/push/unregister")
async def ios_push_unregister(req: Request) -> JSONResponse:
    """Odhlášení zařízení (odhlásil se uživatel / vypnul notifikace)."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from core.database_data import get_data_session as _g
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    dt = (str(body.get("device_token") or "")).strip().lower()
    if not dt:
        return JSONResponse({"ok": False, "error": "device_token"}, status_code=400)
    s = _g()
    try:
        ensure_tables(s)
        s.execute(_t("UPDATE fw.ios_push_token SET active = false, updated_at = now() "
                     "WHERE device_token = :d AND user_id = :u"),
                  {"d": dt, "u": int(uid)})
        s.commit()
        return JSONResponse({"ok": True})
    finally:
        s.close()


@ios_push_router.get("/app/ios/push/status")
async def ios_push_status(req: Request) -> JSONResponse:
    """Diagnostika: je APNs nastavené a mám já sám aktivní zařízení?
    Bez tajemství — vrací jen ano/ne a poslední chybu."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from core.database_data import get_data_session as _g
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    enabled, p8, key_id, team_id, topic = _cfg()
    s = _g()
    try:
        ensure_tables(s)
        rows = s.execute(_t(
            "SELECT device_token, app_version, apns_env, active, last_error, "
            "       last_sent_at, updated_at "
            "FROM fw.ios_push_token WHERE user_id = :u ORDER BY updated_at DESC LIMIT 10"),
            {"u": int(uid)}).mappings().all()
        s.commit()
        return JSONResponse({
            "ok": True,
            "apns_nastaveno": bool(enabled and p8 and key_id and team_id and topic),
            "topic": topic,
            "smycka_bezi": bool(_PUSH_TASK[0] is not None and not _PUSH_TASK[0].done()),
            "zarizeni": [{
                "token_konec": r["device_token"][-8:],
                "app_version": r["app_version"],
                "prostredi": r["apns_env"],
                "aktivni": r["active"],
                "posledni_chyba": r["last_error"],
                "posledni_odeslani": (r["last_sent_at"].isoformat() if r["last_sent_at"] else None),
            } for r in rows],
        })
    finally:
        s.close()


@ios_push_router.post("/app/ios/push/test")
async def ios_push_test(req: Request) -> JSONResponse:
    """Pošle si sám sobě zkušební notifikaci — založí `claude_msg` příkaz
    a hned protočí jedno kolo odesílání. Slouží k ověření na fyzickém iPhonu."""
    from modules.erp.api.router import _uid_from_token_or_cookie
    from core.database_data import get_data_session as _g
    uid = _uid_from_token_or_cookie(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        body = {}
    title = (str(body.get("title") or "Zkušební notifikace"))[:120]
    message = (str(body.get("message") or "Když tohle vidíš na zamčené obrazovce, APNs jede."))[:600]
    screen = (str(body.get("screen") or "")).strip()[:80]
    s = _g()
    try:
        ensure_tables(s)
        cid = s.execute(_t("""
            INSERT INTO fw.mobile_command
                   (app_key, target_user_id, command_type, title, message, payload, created_by)
            VALUES ('mobile', :u, 'claude_msg', :t, :m,
                    CASE WHEN :scr = '' THEN NULL
                         ELSE jsonb_build_object('screen', :scr) END,
                    :u)
            RETURNING id
        """), {"u": int(uid), "t": title, "m": message, "scr": screen}).scalar()
        s.commit()
    except Exception as exc:
        s.rollback()
        s.close()
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        try:
            s.close()
        except Exception:
            pass
    vysledek = await push_tick()
    return JSONResponse({"ok": True, "command_id": cid, "odeslani": vysledek})
