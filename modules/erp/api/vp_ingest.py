"""
VP (vedoucí projektu) ingest — projects@ (tenant.mail_message) → tenant.vp_poptavka.

Nervový systém vedoucích projektu (Marti 2.7.2026, návrh docs/vp_projekty_ingest_design.md,
konzultace Marti-AI). Fáze 2: dedup + založení raw záznamu. Triáž (AI klasifikace
typ/zákazník/shrnutí) + thread grouping = fáze 3.

OPRAVA 31.7.2026 (C23, schváleno Martim): původní verze četla z `mailboxes`/
`email_inbox` — to je JINÝ systém (grant-based mailboxy AI person, viz
modules/notifications/application/mailbox_service.py; jediný živý řádek je
marti-ai@). Sběrná schránka projects@ je od začátku integrovaná stejným
mechanismem jako lidské schránky (Eliška, faktury@): `public.users.ews_email`
+ EWS mirror do `tenant.mail_message` (mail_mirror.py). Přepojeno na tento
zdroj — žádné čekání na IT, data (2280+ e-mailů) jsou živá už teď.

OPRAVA 31.7.2026 č.2 (Marti): `tenant.vp_domain_whitelist` se týká JEN
autonomního ODESÍLÁNÍ pošty (budoucí gate, zatím nepoužito — @@PP REPLY je
draft-only, nic se neposílá samo). Na PŘÍJEM se whitelist nevztahuje — AI čte
a zakládá záznamy ze všech příchozích e-mailů bez filtrace domény. Filtr
odstraněn ze `sync_vp_poptavky()`.

Bezpečné pustit i kdyby schránka nebyla nalezena — vrací no-op (ok=False,
reason).
"""
from __future__ import annotations

import json

from sqlalchemy import text as _t

from core.database_data import get_data_session
from core.logging import get_logger

logger = get_logger("vp_ingest")

# public.users.ews_email sběrné schránky VP (ověřeno 31.7.2026: user_id=111,
# "projects@ (sběrná schránka VP)", živě mirrorováno do tenant.mail_message).
VP_MAIL_EWS_UPN = "projects@eurosoft-control.cz"
DEFAULT_TENANT = 2  # EUROSOFT

# Fáze 3 — triáž (AI klasifikace). Levný model (Haiku), loguje se do llm_calls.
VP_TRIAGE_MODEL = "claude-haiku-4-5-20251001"
VP_TRIAGE_SYSTEM = (
    "Jsi triage asistent pro vedoucí projektu (VP) ve firmě EUROSOFT — výroba "
    "elektrických rozváděčů na zakázku + programování PLC software. Dostaneš jeden "
    "příchozí e-mail (předmět + tělo). Klasifikuj ho a vytěž strukturovaná data. "
    "Vrať POUZE validní JSON (bez markdownu, bez komentářů) s klíči: "
    "typ — 'poptavka' (nová zakázková poptávka / RFQ / dotaz na cenu či realizaci od "
    "zákazníka), 'provozni' (běžná provozní/koordinační korespondence k existující "
    "zakázce), nebo 'ostatni' (spam, newsletter, interní nesouvisející); "
    "zakaznik — název firmy nebo osoby odesílatele (nebo null); "
    "predmet — krátce čeho se týká, max 100 znaků; "
    "shrnuti — 1–2 věty česky, co odesílatel chce; "
    "jistota — celé číslo 0–100, jak jistá je klasifikace typu. "
    "Buď konzervativní: pokud si poptávkou nejsi jistý, zvol 'provozni' nebo 'ostatni'."
)


def _domain_of(email: str | None) -> str | None:
    """Rezervováno pro budoucí gate autonomního ODESÍLÁNÍ (vp_domain_whitelist);
    na příjem se nepoužívá (Marti 31.7.2026 — AI čte všechny příchozí maily)."""
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1].strip().lower().rstrip(">").strip()


def _vp_user_id(s, upn: str = VP_MAIL_EWS_UPN) -> int | None:
    row = s.execute(
        _t("SELECT id FROM public.users WHERE lower(ews_email)=lower(:u)"),
        {"u": upn},
    ).first()
    return row[0] if row else None


def sync_vp_poptavky(tenant_id: int = DEFAULT_TENANT, limit: int = 200) -> dict:
    """
    Projde nové příchozí maily sběrné schránky projects@ (tenant.mail_message,
    stejný EWS mirror jako u lidských schránek) a založí raw záznamy do
    tenant.vp_poptavka (stav='nova', typ='neurcen' — triáž doplní fáze 3) pro
    VŠECHNY příchozí maily — bez filtrace domény (Marti 31.7.2026: whitelist
    domén se týká jen autonomního odesílání, ne příjmu). Idempotentní: dedup
    přes message_id (= mail_message.ews_item_id).
    """
    s = get_data_session()
    try:
        uid = _vp_user_id(s)
        if not uid:
            return {"ok": False, "reason": "schranka projects@ (tenant.mail_message) nenalezena",
                    "ews_upn": VP_MAIL_EWS_UPN}

        rows = s.execute(
            _t("""
                SELECT m.id, m.ews_item_id AS message_id, m.od_email AS from_email,
                       m.od_jmeno AS from_name, m.komu AS to_email, m.predmet AS subject,
                       m.datum AS received_at
                FROM tenant.mail_message m
                WHERE m.user_id = :uid AND m.slozka = 'dorucene'
                  AND NOT EXISTS (
                        SELECT 1 FROM tenant.vp_poptavka p
                        WHERE p.tenant_id = :t AND p.message_id = m.ews_item_id)
                ORDER BY m.id
                LIMIT :lim
            """),
            {"uid": uid, "t": tenant_id, "lim": limit},
        ).mappings().all()

        created = 0
        for r in rows:
            s.execute(
                _t("""
                    INSERT INTO tenant.vp_poptavka
                      (tenant_id, source_email_id, message_id, smer, from_email,
                       from_name, to_email, subject, received_at, typ, stav)
                    VALUES
                      (:t, :sid, :msg, 'in', :fe, :fn, :te, :subj, :rec,
                       'neurcen', 'nova')
                    ON CONFLICT (tenant_id, message_id)
                        WHERE message_id IS NOT NULL DO NOTHING
                """),
                {"t": tenant_id, "sid": r["id"], "msg": r["message_id"],
                 "fe": r["from_email"], "fn": r["from_name"], "te": r["to_email"],
                 "subj": r["subject"], "rec": r["received_at"]},
            )
            created += 1

        s.commit()
        logger.info("VP ingest | user_id=%s | nova=%s", uid, created)
        return {"ok": True, "user_id": uid, "nova": created}
    finally:
        s.close()


def info(tenant_id: int = DEFAULT_TENANT) -> dict:
    """Přehled stavu VP poptávek + whitelist + zda je schránka nalezena."""
    s = get_data_session()
    try:
        uid = _vp_user_id(s)
        by_stav = {
            row[0]: row[1]
            for row in s.execute(
                _t("SELECT stav, count(*) FROM tenant.vp_poptavka "
                   "WHERE tenant_id=:t GROUP BY stav"),
                {"t": tenant_id},
            )
        }
        wl = [
            {"domain": r[0], "kind": r[1]}
            for r in s.execute(
                _t("SELECT domain, kind FROM tenant.vp_domain_whitelist "
                   "WHERE tenant_id=:t AND active ORDER BY domain"),
                {"t": tenant_id},
            )
        ]
        return {"ok": True, "mailbox_pripojen": uid is not None,
                "ews_upn": VP_MAIL_EWS_UPN, "user_id": uid,
                "poptavky_dle_stavu": by_stav, "whitelist": wl}
    finally:
        s.close()


# ── Fáze 3: triáž (AI klasifikace) ──────────────────────────────────────────

def triage_text(subject: str | None, body: str | None,
                conversation_id: int | None = None,
                tenant_id: int = DEFAULT_TENANT) -> dict:
    """
    Klasifikuje jeden e-mail přes levný model (Haiku) → dict
    {typ, zakaznik, predmet, shrnuti, jistota}. Loguje se do llm_calls
    (kind='vp_triage'). Čistá funkce — nesahá na DB (jde testovat ad-hoc textem).
    """
    import anthropic
    from core.config import settings

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    content = (
        f"PŘEDMĚT: {subject or '(bez předmětu)'}\n\n"
        f"TĚLO:\n{(body or '')[:6000]}"
    )
    from modules.conversation.application import telemetry_service as _tel
    resp = _tel.call_llm_with_trace(
        client,
        conversation_id=conversation_id,
        kind="vp_triage",
        model=VP_TRIAGE_MODEL,
        max_tokens=400,
        system=VP_TRIAGE_SYSTEM,
        messages=[{"role": "user", "content": content}],
        tenant_id=tenant_id,
    )
    raw = (resp.content[0].text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)

    typ = str(data.get("typ") or "neurcen").strip().lower()
    if typ not in ("poptavka", "provozni", "ostatni"):
        typ = "neurcen"
    try:
        jist = int(data.get("jistota") or 0)
    except (TypeError, ValueError):
        jist = 0
    return {
        "typ": typ,
        "zakaznik": (data.get("zakaznik") or None),
        "predmet": (str(data.get("predmet"))[:500] if data.get("predmet") else None),
        "shrnuti": (data.get("shrnuti") or None),
        "jistota": max(0, min(100, jist)),
    }


def triage_pending(tenant_id: int = DEFAULT_TENANT, limit: int = 25) -> dict:
    """
    Vezme nezpracované záznamy (typ='neurcen', stav='nova'), doplní tělo z
    tenant.mail_message, klasifikuje a uloží typ/zákazník/předmět/shrnutí/jistotu.
    Idempotentní — jednou klasifikovaný záznam (typ != 'neurcen') přeskočí.
    """
    s = get_data_session()
    try:
        rows = s.execute(
            _t("""
                SELECT p.id, p.subject, m.telo_text AS body
                FROM tenant.vp_poptavka p
                LEFT JOIN tenant.mail_message m ON m.id = p.source_email_id
                WHERE p.tenant_id = :t AND p.typ = 'neurcen' AND p.stav = 'nova'
                ORDER BY p.id
                LIMIT :lim
            """),
            {"t": tenant_id, "lim": limit},
        ).mappings().all()

        done = 0
        errors: list[str] = []
        for r in rows:
            try:
                cls = triage_text(r["subject"], r["body"], tenant_id=tenant_id)
                s.execute(
                    _t("""
                        UPDATE tenant.vp_poptavka
                        SET typ=:typ, zakaznik=:zak, predmet=:pred,
                            shrnuti=:shr, jistota=:jist, updated_at=now()
                        WHERE id=:id
                    """),
                    {"typ": cls["typ"], "zak": cls["zakaznik"], "pred": cls["predmet"],
                     "shr": cls["shrnuti"], "jist": cls["jistota"], "id": r["id"]},
                )
                s.commit()
                done += 1
            except Exception as e:  # noqa: BLE001
                s.rollback()
                errors.append(f"{r['id']}: {type(e).__name__}: {str(e)[:120]}")
        logger.info("VP triage | zpracovano=%s | chyby=%s", done, len(errors))
        return {"ok": True, "zpracovano": done, "chyby": errors[:5]}
    finally:
        s.close()


# ── Fáze 5: cockpit (monitoring) ────────────────────────────────────────────

def list_poptavky(tenant_id: int = DEFAULT_TENANT, stav: str | None = None,
                  typ: str | None = None, limit: int = 300) -> dict:
    """Seznam VP poptávek pro cockpit (nejnovější první). Timestamp jako text
    (JSON-safe). Volitelné filtry stav/typ."""
    s = get_data_session()
    try:
        where = ["tenant_id = :t"]
        params: dict = {"t": tenant_id, "lim": limit}
        if stav:
            where.append("stav = :stav")
            params["stav"] = stav
        if typ:
            where.append("typ = :typ")
            params["typ"] = typ
        rows = s.execute(
            _t(
                "SELECT id, "
                "to_char(COALESCE(received_at, created_at),'YYYY-MM-DD HH24:MI') AS kdy, "
                "typ, stav, zakaznik, predmet, shrnuti, from_email, subject, jistota, "
                "prideleno_user_id, zakazka_ref "
                "FROM tenant.vp_poptavka WHERE " + " AND ".join(where) +
                " ORDER BY COALESCE(received_at, created_at) DESC NULLS LAST LIMIT :lim"
            ),
            params,
        ).mappings().all()
        return {"ok": True, "poptavky": [dict(r) for r in rows]}
    finally:
        s.close()

