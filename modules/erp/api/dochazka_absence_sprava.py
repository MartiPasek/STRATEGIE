"""Správa docházky — ÚPRAVA / PŘIDÁNÍ / SMAZÁNÍ absencí přímo v přehledu.
Peťa + Claude‑26, 30. 7. 2026.

PROČ TENHLE MODUL VZNIKL
------------------------
Přehled „Správa docházky" (pohled `budoucnost` v Docházce new) uměl absence jen
ZOBRAZIT. Petra 30.7.2026: *„správa je správa proto, aby se to tam spravovalo —
pokud si někdo zadá dovolenou, musí být možnost ji tady editovat, mazat a přidávat
a pak se to automaticky musí upravit v tom záznamu."* Tenhle modul to doplňuje.

Do té doby NEEXISTOVALA ŽÁDNÁ cesta, jak založit absenci ZA JINÉHO ČLOVĚKA —
všechny zakládací endpointy (`/app/attendance/absence/request`, `/absence`,
`/ocr/start`, `/sick/start`) berou `_att_employee(s, uid)`, tedy vždy sám za sebe.

JAK JE ŘÁDEK PŘEHLEDU IDENTIFIKOVANÝ (sloupec „Číslo řádku", dodal Jirka 30.7.)
-------------------------------------------------------------------------------
  `Z:<id>`          = žádost `tenant.att_absence_request`, která ZATÍM NENÍ
                      promítnutá do dnů (dataset filtruje `materialized=false`).
  `D:<id,id,...>`   = poskládané denní záznamy `tenant.att_entry`. Jeden řádek
                      přehledu = víc dnů, proto SEZNAM čísel, ne jedno číslo.

ROZHODNUTÍ PETRY (30.7.2026)
----------------------------
1. **„Platí hned."** Co Petra ve Správě docházky zadá, platí okamžitě — nejde to
   ke schválení vedoucímu. Je to správcovský nástroj. Do auditu (`tenant.att_audit`)
   se ukládá kdo a proč; dotčený člověk dostane zprávu.
2. **Editovat jde všechno včetně Centrály**, protože Jirka telefonicky potvrdil,
   že se synchronizace plánu z Centrály vypne. DOKUD JE ALE ZAPNUTÁ, vrací
   `/meta` příznak `sync_centrala` = true a UI u řádků „plán z Centrály" varuje,
   že se změna do hodiny přepíše. Jakmile Jirka job vypne, varování samo zmizí —
   čte se živě z `fw.mirror_job`.

CO SE DĚLÁ SE ZŮSTATKY
----------------------
Do dneška se `holiday_balance` / `sick_day_balance` přepočítávaly JEN když člověk
prošel mobilní cestou `POST /app/attendance/absence`. Po `absence/decide`,
`absence/cancel` ani `fix/void` se nepřepočítalo nic. Tady se po KAŽDÉ změně volá
`_abs_recalc_balances()` — idempotentní přepočet z docházky (ne inkrement), takže
opakované spuštění nic nerozbije. Roky s `uzavreno=true` se přeskakují.

POJISTKY
--------
* Práva: `_att_can_fix` (skupina „DOCHÁZKA - OPRAVY" nebo rodič) + působnost
  `_att_fix_scope_emps` (kancelář/výroba) — shodně s `fix/void`.
* Uzamčený mzdový měsíc = TVRDÝ zákaz (409), i pro držitele zámku. Kontroluje se
  starý I nový rozsah dat. Absenční cesty tuhle kontrolu dosud NEMĚLY vůbec.
* Nikdy se needituje na tvrdo: staré denní záznamy se `superseded` (jako `fix/void`),
  nikdy se nemažou.
* Povinný důvod u úpravy a smazání (audit). U nového záznamu nepovinný.
"""
from __future__ import annotations

import datetime as _dt

from fastapi import Request
from fastapi.responses import JSONResponse

from modules.erp.api.dochazka_zak_tab import doch_zak_tab_router

_TEN = 2

# Zdroj řádku → smí se opravovat tady? (jediná výjimka je dnes plán z Centrály,
# a i ta padne, jakmile Jirka vypne synchronizaci — proto jen varování, ne zákaz.)
_SYNC_JOB = "sync_plan_nepritomnost"


# ── pomocné ──────────────────────────────────────────────────────────────────
def _parse_radek(radek_id: str):
    """„Z:123" → ('zadost', [123]) · „D:1,2,3" → ('dny', [1,2,3])."""
    t = str(radek_id or "").strip()
    if not t or ":" not in t:
        return (None, [])
    pre, rest = t.split(":", 1)
    ids = []
    for kus in rest.split(","):
        kus = kus.strip()
        if not kus:
            continue
        try:
            ids.append(int(kus))
        except ValueError:
            return (None, [])
    if not ids:
        return (None, [])
    pre = pre.strip().upper()
    if pre == "Z":
        return ("zadost", ids)
    if pre == "D":
        return ("dny", ids)
    return (None, [])


def _den(v):
    """'YYYY-MM-DD' → date (None, když prázdné/nečitelné)."""
    t = str(v or "").strip()[:10]
    if not t:
        return None
    try:
        return _dt.date.fromisoformat(t)
    except ValueError:
        return None


def _pracovni_dny(s, d_od, d_do):
    """Pracovní dny v rozsahu podle firemního kalendáře (stejně jako absence/decide)."""
    from sqlalchemy import text as _t
    rows = s.execute(_t(
        "SELECT day FROM tenant.att_calendar_day WHERE tenant_id=:t AND is_workday=true "
        "AND day>=:od AND day<=:do ORDER BY day"),
        {"t": _TEN, "od": d_od, "do": d_do}).fetchall()
    return [r[0] for r in rows]


def _zamek(s, dny):
    """Vrátí text chyby, když některý z dnů spadá do uzavřeného mzdového měsíce."""
    from modules.erp.api.router import _att_period_locked
    mesice = set()
    for d in dny:
        if d is None:
            continue
        mesice.add((d.year, d.month))
    for (r, m) in sorted(mesice):
        if _att_period_locked(s, _dt.date(r, m, 1)):
            return ("Měsíc %02d/%d je uzavřený (mzdy zpracovány) — nejdřív ho musí "
                    "odemknout Peťa nebo Šárka." % (m, r))
    return None


def _engagement(s, emp):
    """Aktuální (jinak poslední) pracovní poměr člověka — na něj visí zůstatky."""
    from sqlalchemy import text as _t
    return s.execute(_t(
        "SELECT id FROM tenant.engagement WHERE employee_id=:e AND tenant_id=:t "
        "AND (smlouva_do IS NULL OR smlouva_do>=CURRENT_DATE) "
        "ORDER BY smlouva_od DESC NULLS LAST LIMIT 1"), {"e": emp, "t": _TEN}).scalar() \
        or s.execute(_t("SELECT id FROM tenant.engagement WHERE employee_id=:e AND tenant_id=:t "
                        "ORDER BY id DESC LIMIT 1"), {"e": emp, "t": _TEN}).scalar()


class _Kousek:
    """Bezpečná obálka pro „když to nevyjde, nevadí" bloky.

    ⚠️ POUČENÍ 30.7.2026 (Peťa: „napsalo smazáno, ale nesmazalo se"):
    prosté `try/except: s.rollback()` uvnitř pomocné funkce VRÁTÍ ZPĚT CELOU
    rozdělanou transakci, tedy i práci volajícího — smazání absence se zapsalo,
    pak selhal navazující přepočet zůstatku, jeho `rollback()` smazání zahodil
    a endpoint přesto vrátil `ok`. Uživatel viděl „Smazáno 1 absencí" a v datech
    nebylo nic. Rollback v PG nejde vynechat (po chybě je transakce zablokovaná),
    takže se každý nepovinný blok jistí SAVEPOINTem = vrátí se jen on sám.
    """

    def __init__(self, s):
        self.s = s
        self.tx = None

    def __enter__(self):
        try:
            self.tx = self.s.begin_nested()
        except Exception:
            self.tx = None
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.tx is not None:
            try:
                self.tx.rollback() if exc_type else self.tx.commit()
            except Exception:
                pass
        return True  # výjimku spolkni, hlavní práce pokračuje


def _abs_recalc_balances(s, emp, roky):
    """IDEMPOTENTNÍ přepočet zůstatků z docházky (ne inkrement — spočítá se znovu).

    dovolená  → holiday_balance.cerpano_h  = SUM(hodin) záznamů typu 'vacation' v roce
    sick days → sick_day_balance.cerpano_h = SUM(hodin) záznamů typu 'sickday' v roce
      (pozn.: část „lékaře" se při čerpání ukládá rovnou JAKO 'sickday' — viz
       `_sickday_lekar_apply` — takže tenhle součet sedí i pro lékaře.)

    Roky označené `uzavreno=true` se NEPŘEPOČÍTÁVAJÍ (uzavřený rok se nesmí hnout).
    Vrací seznam popisů, co se přepočítalo (pro hlášku uživateli).
    """
    from sqlalchemy import text as _t
    out = []
    eng = _engagement(s, emp)
    if not eng:
        return out
    for rok in sorted({int(r) for r in roky if r}):
        # ── dovolená ────────────────────────────────────────────────────────
        with _Kousek(s):
            ex = s.execute(_t("SELECT narok_h, prevod_h, COALESCE(uzavreno,false) "
                              "FROM tenant.holiday_balance "
                              "WHERE tenant_id=:t AND engagement_id=:g AND rok=:r"),
                           {"t": _TEN, "g": eng, "r": rok}).first()
            if not (ex and ex[2]):
                cerp = s.execute(_t(
                    "SELECT COALESCE(SUM(en.hours),0) FROM tenant.att_entry en "
                    "JOIN tenant.att_entry_type ty ON ty.id=en.entry_type_id "
                    "WHERE en.tenant_id=:t AND en.employee_id=:e AND ty.code='vacation' "
                    "AND COALESCE(en.status,'')<>'superseded' "
                    "AND EXTRACT(YEAR FROM en.entry_date)=:r"),
                    {"t": _TEN, "e": emp, "r": rok}).scalar() or 0
                # POZOR — „zbývá" (zbytek_h) SCHVÁLNĚ NEPŘEPISUJEME (Peťa 30.7.2026).
                # Nárok na dovolenou zatím není spočítaný: v `holiday_balance` má všech
                # 79 lidí jednotných 200 h (25 dnů) bez ohledu na úvazek a nástup —
                # výplň, ne výpočet (upozornil Jirka). Dokud nárok neumí počítat, bylo by
                # „zbývá" nepravdivé číslo, na které se lidi dívají. Čerpáno naopak
                # počítáme, to je pravda z docházky. Až bude nárok hotový, stačí sem
                # vrátit dopočet zbytek_h = narok + prevod − cerpano.
                if ex:
                    s.execute(_t("UPDATE tenant.holiday_balance SET cerpano_h=:c, changed_at=now() "
                                 "WHERE tenant_id=:t AND engagement_id=:g AND rok=:r"),
                              {"c": cerp, "t": _TEN, "g": eng, "r": rok})
                else:
                    s.execute(_t("INSERT INTO tenant.holiday_balance "
                                 "(tenant_id,engagement_id,rok,narok_h,prevod_h,cerpano_h,zbytek_h) "
                                 "VALUES (:t,:g,:r,0,0,:c,NULL)"),
                              {"t": _TEN, "g": eng, "r": rok, "c": cerp})
                out.append("dovolená %d: čerpáno %.1f h" % (rok, float(cerp)))
        # ── sick days ───────────────────────────────────────────────────────
        with _Kousek(s):
            ex = s.execute(_t("SELECT narok_h, COALESCE(uzavreno,false) FROM tenant.sick_day_balance "
                              "WHERE tenant_id=:t AND engagement_id=:g AND rok=:r"),
                           {"t": _TEN, "g": eng, "r": rok}).first()
            if not (ex and ex[1]):
                cerp = s.execute(_t(
                    "SELECT COALESCE(SUM(en.hours),0) FROM tenant.att_entry en "
                    "JOIN tenant.att_entry_type ty ON ty.id=en.entry_type_id "
                    "WHERE en.tenant_id=:t AND en.employee_id=:e AND ty.code='sickday' "
                    "AND COALESCE(en.status,'')<>'superseded' "
                    "AND EXTRACT(YEAR FROM en.entry_date)=:r"),
                    {"t": _TEN, "e": emp, "r": rok}).scalar() or 0
                if ex:
                    s.execute(_t("UPDATE tenant.sick_day_balance SET cerpano_h=:c "
                                 "WHERE tenant_id=:t AND engagement_id=:g AND rok=:r"),
                              {"c": cerp, "t": _TEN, "g": eng, "r": rok})
                else:
                    s.execute(_t("INSERT INTO tenant.sick_day_balance "
                                 "(tenant_id,engagement_id,rok,narok_h,cerpano_h) "
                                 "VALUES (:t,:g,:r,16,:c)"),
                              {"t": _TEN, "g": eng, "r": rok, "c": cerp})
                out.append("sick days %d: čerpáno %.1f h" % (rok, float(cerp)))
    return out


def _kdo(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _smi(s, uid, emp=None):
    """Práva shodná s `fix/void`: editor oprav + působnost na danou osobu.
    Vrací None = OK, jinak (chyba, http kód).

    POZOR (Peťa 30.7.2026): musí respektovat i `_att_fix_scope.fix_all` — příznak
    „vidí a opravuje VŠECHNY lidi" (Peťa 18, Michaela 16), který přibyl týž den
    commitem 42876531. Bez něj tenhle modul držel starou působnost (kancelář) a
    mazání absence u člověka z výroby tiše skončilo na 403 — přesně to se stalo
    u Horkého 27.7. Kdo bude sahat na práva oprav docházky, ať to přidá i sem."""
    from modules.erp.api.router import (_att_can_fix, _att_fix_scope,
                                        _att_fix_scope_emps)
    if not _att_can_fix(s, uid):
        return ("Na opravy docházky nemáš oprávnění.", 403)
    if emp is not None:
        try:
            from modules.erp.api.router import _att_fix_all as _fa
            vse = _fa(s, uid)
        except Exception:
            vse = False
        emps = None if vse else _att_fix_scope_emps(s, _att_fix_scope(s, uid))
        if emps is not None and int(emp) not in emps:
            return ("Osoba není ve tvé působnosti (kancelář/výroba).", 403)
    return None


def _chyba(text, kod=400):
    return JSONResponse({"ok": False, "error": text}, status_code=kod)


# ── META: druhy absencí + stav synchronizace z Centrály ──────────────────────
@doch_zak_tab_router.get("/app/dochazka-abs/meta")
def dochazka_abs_meta(req: Request) -> JSONResponse:
    """Číselník druhů absencí + příznak, jestli ještě běží synchronizace plánu
    z Centrály (kvůli varování u řádků „plán z Centrály")."""
    from sqlalchemy import text as _t
    from modules.strategie_pg.application import service as _pg
    uid = _kdo(req)
    if not uid:
        return _chyba("unauthorized", 401)
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        druhy = [{"code": r[0], "label": r[1]} for r in s.execute(_t(
            "SELECT code, label FROM tenant.att_entry_type WHERE tenant_id=:t "
            "AND (category='absence' OR code='homeoffice') ORDER BY label"), {"t": _TEN}).fetchall()]
        try:
            sync = bool(s.execute(_t("SELECT enabled FROM fw.mirror_job WHERE job_key=:j"),
                                  {"j": _SYNC_JOB}).scalar())
        except Exception:
            s.rollback()
            sync = True  # když nevím, raději varuj
        return JSONResponse({"ok": True, "druhy": druhy, "sync_centrala": sync})
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


# ── PROMÍTNUTÍ ŽÁDOSTI DO DNŮ BEZ OHLEDU NA SCHVÁLENÍ ────────────────────────
# Peťa 30.7.2026: „Nastavujeme to tak, jak jsou všichni zvyklí z Centrály — nemůže
# se nám to nepropisovat kvůli schválení, když ti lidi tu dovolenou měli."
# V Centrále šla dovolená do docházky rovnou; schvalování bylo vedle, ne brána před ní.
# U nás se do 30.7. dny generovaly AŽ schválením (`/absence/decide`), takže neschválená
# žádost znamenala v docházce PRÁZDNÝ den — člověk odjel a nikde nic. Doloženo: 23 žádostí
# o dovolenou u 14 lidí (83 pracovních dnů, nejstarší z 22.6.) viselo nepromítnutých.
#
# Nově: dny se vygenerují PODLE PRAVIDEL (pracovní dny z firemního kalendáře × hodiny/den)
# hned, nezávisle na `stav`. Schválení tím neztrácí smysl — vedoucí pořád rozhoduje,
# jen už neblokuje zápis do docházky.
#
# Platí JEN pro dovolenou a sick day (Peťa 30.7.). Lékař, nemoc a OČR se zadávají
# z reálných dokladů, ne ze žádosti — ty tudy schválně NEJDOU (řeší se s Kristý).
# Co s dnem, když vedoucí žádost později zamítne, ZATÍM NEŘEŠÍME (Peťa: „až to
# někdo bude řešit") — den v docházce zůstane.
_ROVNOU_DO_DOCHAZKY = ("vacation", "sickday")


def abs_promitni_zadost(s, rid, uid=None) -> int:
    """Vygeneruje denní záznamy ze žádosti `rid`. Idempotentní — nejdřív smaže
    dřívější materializaci téže žádosti, stejně jako to dělá `/absence/decide`,
    takže opakované volání ani pozdější schválení nic nezdvojí.
    Vrací počet založených dnů (0 = typ sem nepatří / není co zapsat)."""
    from sqlalchemy import text as _t
    r = s.execute(_t(
        "SELECT employee_id, typ, datum_od, datum_do, hours_per_day, user_id, "
        "       COALESCE(materialized,false), COALESCE(stav,'') "
        "FROM tenant.att_absence_request WHERE id=:i AND tenant_id=:t"),
        {"i": rid, "t": _TEN}).first()
    if not r:
        return 0
    emp, typ, d_od, d_do, hpd, zad_uid, mat, stav = r
    if typ not in _ROVNOU_DO_DOCHAZKY:
        return 0
    if stav in ("cancelled", "rejected"):
        return 0
    ti = _typ_id(s, typ)
    if not ti:
        return 0
    # idempotence — shodně s /absence/decide
    s.execute(_t("DELETE FROM tenant.att_entry WHERE tenant_id=:t AND source_system='absence_req' "
                 "AND source_id=:i"), {"t": _TEN, "i": rid})
    # Jirka 6.8.2026 (podnět Dušan, schválila Marti-AI): `ved_schvaleno` MUSÍ jít
    # ze skutečného stavu žádosti, ne z výchozího True v `_zapis_dny`. Ten default
    # patří správcovskému zadání („co zadá správce, platí hned" — Peťa 31.7.), ale
    # sem se chodí i s obyčejnou žádostí z appky, která žádné rozhodnutí za sebou
    # nemá. Bez toho dostal ✓ ve sloupci S i den u žádosti, kterou vedoucí nikdy
    # neviděl — což je horší než prázdno, protože to vypadá jako rozhodnutí.
    # Zápis dnů dopředu ZŮSTÁVÁ (pravidlo Peti z 30.7.), mění se jen ten příznak.
    dnu = _zapis_dny(s, int(emp), typ, d_od, d_do, float(hpd or 8),
                     "absence ze žádosti", (uid or zad_uid), zdroj="absence", zad_id=rid,
                     schvaleno=(stav == "approved"))
    if dnu:
        s.execute(_t("UPDATE tenant.att_absence_request SET materialized=true "
                     "WHERE id=:i AND tenant_id=:t"), {"i": rid, "t": _TEN})
        with _Kousek(s):
            _abs_recalc_balances(s, int(emp), {d_od.year, d_do.year})
    return dnu


# ── společné jádro zápisu ────────────────────────────────────────────────────
def _typ_id(s, code):
    from sqlalchemy import text as _t
    return s.execute(_t("SELECT id FROM tenant.att_entry_type WHERE tenant_id=:t AND code=:c"),
                     {"t": _TEN, "c": code}).scalar()


def _sd_check(emp, typ_code, hpd, den=None):
    """Sick day jen CELÉ HODINY nebo PŘESNĚ PŮLDEN (Peťa 10. 8. 2026).

    Spouštěč: 5. 8. se do docházky dostal sick day na 1,35 h (drobné dopočtené
    z časů) a 10. 8. založil formulář „Úprava absence" záznam na 8,00 h místo
    1,00 h, protože měl hodiny natvrdo. Půlden je podmínka zvlášť, protože
    u sedmihodinového dne nevychází na celou hodinu (3,50 h).

    Samotné pravidlo ŽIJE V DATABÁZI (g2007.python kód=att_sd_kontrola), takže
    se dá změnit i vypnout za běhu, bez nasazování a bez restartu. Tady je jen
    pár řádků, které se ho zeptají.

    Vrací text chyby, nebo None když je vše v pořádku.
    """
    if str(typ_code or "").strip() != "sickday":
        return None
    try:
        from modules.erp.api import erp_registry as _ereg
        r = _ereg.call("att_sd_kontrola", emp, "sickday", hpd,
                       den.isoformat() if den else None) or {}
    except Exception:
        return None  # kontrola nikdy nesmí shodit samotný zápis
    if r.get("ok", True):
        return None
    return r.get("error") or "Neplatný počet hodin sick day."


def _zapis_dny(s, emp, typ_code, d_od, d_do, hpd, pozn, uid, zdroj="manual_fix", zad_id=None,
               schvaleno=True):
    """Založí absenční denní záznamy na pracovní dny rozsahu. Vrací počet dnů.
    Rámec dne 06:00 → 06:00+hodiny (stejně jako materializace schválené žádosti),
    aby s nimi uměly pracovat i „Opravy docházky" (ty odmítají záznamy bez času)."""
    from sqlalchemy import text as _t
    ti = _typ_id(s, typ_code)
    if not ti:
        return 0
    dny = _pracovni_dny(s, d_od, d_do)
    if not dny:
        return 0
    # ── POJISTKA PROTI DVOJÍMU ZAPSÁNÍ TÉŽE ABSENCE (Peťa 6. 8. 2026) ──────────
    # Zadání Peti: „i kdyby vyskočilo 18 notifikací na schválení, má proběhnout jen
    # příznak schválení, ne zakládat nové řádky."
    # Co se stalo 24. 7. 2026: Čiviš (522) podal třikrát po sobě tutéž žádost
    # o dovolenou na jeden den (#35, #36, #37). Vedoucí je 5. 8. všechny schválil
    # a vznikly TŘI záznamy po 8 h = 24 h za jediný den. Nafoukla se mu tím
    # absence, a tím i FPD a přesčas (16,34 h místo 0,34 h → příplatek 4 908 Kč
    # místo ~100 Kč). Ve mzdách by to prošlo.
    # Proč to staré chování nezachytilo: materializace žádosti maže jen SVOJE
    # dřívější řádky (source_id = tato žádost), takže tři různé žádosti si
    # navzájem nepřekážely.
    # Pravidlo: den PŘESKOČÍME, pokud by se součet hodin téhož druhu absence za
    # ten den dostal NAD denní úvazek. Půldny (4 + 4 = 8) tím zůstávají možné —
    # blokuje se až to, co dohromady nedává smysl (8 + 8 = 16).
    try:
        # denní úvazek člověka (kolik hodin absence se za den vůbec vejde);
        # když ho neznáme, bereme 8 h
        _limit = s.execute(_t(
            "SELECT COALESCE(MAX(g.uvazek_tyden_h),40)/5.0 FROM tenant.engagement g "
            "WHERE g.employee_id=:e AND COALESCE(g.is_current,false)=true"),
            {"e": emp}).scalar()
        _limit = float(_limit or 8.0)
        if _limit <= 0:
            _limit = 8.0
        _obsazeno = {}
        for _r in s.execute(_t(
            "SELECT entry_date, COALESCE(SUM(hours),0) FROM tenant.att_entry "
            "WHERE tenant_id=:t AND employee_id=:e AND entry_type_id=:ti "
            "  AND entry_date = ANY(:dny) "
            "  AND status IS DISTINCT FROM 'superseded' "
            "  AND status IS DISTINCT FROM 'announced' "
            + ("  AND COALESCE(source_id,-1) <> :zid " if zad_id else "") +
            "GROUP BY entry_date"),
                dict({"t": _TEN, "e": emp, "ti": ti, "dny": list(dny)},
                     **({"zid": zad_id} if zad_id else {}))).fetchall():
            _obsazeno[_r[0]] = float(_r[1] or 0)
        if _obsazeno:
            dny = [d for d in dny
                   if _obsazeno.get(d, 0.0) + float(hpd) <= _limit + 0.001]
        if not dny:
            return 0
    except Exception:
        pass  # pojistka nikdy nesmí shodit samotný zápis
    konec_min = min(1439, 360 + int(round(float(hpd) * 60)))
    konec = "%02d:%02d:00" % (konec_min // 60, konec_min % 60)
    # `ved_schvaleno` = zaškrtnutí „Schváleno" v okně (Peťa 31.7.2026). Co zadává
    # správce, platí rovnou — v přehledu se to hned ukáže s ✓ ve sloupci S.
    par = [{"e": emp, "d": d, "ti": ti, "h": float(hpd), "u": uid, "et": konec,
            "n": (pozn or "")[:250], "src": zdroj, "ss": ("absence_req" if zad_id else None),
            "si": zad_id, "sch": bool(schvaleno)} for d in dny]
    s.execute(_t(
        "INSERT INTO tenant.att_entry (tenant_id,employee_id,entry_date,entry_type_id,hours,"
        "started_at,ended_at,status,source,source_system,source_id,is_active,note,"
        "ved_schvaleno,created_by_id,created_at,updated_at) "
        "VALUES (%d,:e,:d,:ti,:h,:d + time '06:00',:d + CAST(:et AS time),"
        "'confirmed',:src,:ss,:si,false,:n,:sch,:u,now(),now())" % _TEN), par)
    return len(dny)


def _znic_dny(s, ids, emp, uid, actor, duvod):
    """Zneplatní denní záznamy (superseded, NIKDY DELETE) + audit — jako `fix/void`.
    Vrací seznam dotčených dat (kvůli přepočtu zůstatků a kontrole zámku)."""
    from sqlalchemy import text as _t
    from modules.erp.api.router import _att_fix_audit
    data = []
    for eid in ids:
        row = s.execute(_t(
            "SELECT e.employee_id, e.entry_date, COALESCE(e.note,''), COALESCE(e.status,''), "
            "       COALESCE(e.source_system,''), COALESCE(e.source_id,0) "
            "FROM tenant.att_entry e WHERE e.id=:i AND e.tenant_id=:t"),
            {"i": eid, "t": _TEN}).first()
        if not row or row[3] == "superseded":
            continue
        data.append(row[1])
        tag = "🛠 SPRÁVA DOCHÁZKY (" + actor + "): " + duvod
        # local_lock=true je POVINNÝ (Jirka 30.7.2026, commit b05c15ed, schválila Marti‑AI
        # msg 11842). Bez něj synchronizace ze staré Centrály (_sync_ec_dochazka_recent,
        # běží po ~5 min) zneplatněný řádek OŽIVÍ — a když vedle něj už stojí opravená
        # verze, vznikne den se DVĚMA platnými záznamy = dvojité hodiny do mzdových
        # podkladů. Zámek říká synchronizaci „tenhle řádek je opravený, nesahej na něj";
        # respektuje ho jak UPDATE, tak wipe DELETE.
        s.execute(_t(
            "UPDATE tenant.att_entry SET status='superseded', is_active=false, local_lock=true, "
            " updated_at=now(), "
            " note = CASE WHEN COALESCE(note,'')='' THEN :tg ELSE note || ' / ' || :tg END "
            "WHERE id=:i AND tenant_id=:t"), {"i": eid, "t": _TEN, "tg": tag})
        # navázaný úsek ve výrobě (kdyby existoval) — stejná kaskáda jako fix/void
        with _Kousek(s):
            s.execute(_t("UPDATE tenant.vyroba_work SET is_active=false, updated_at=now() "
                         "WHERE att_entry_id=:i AND tenant_id=:t"), {"i": eid, "t": _TEN})
        _att_fix_audit(s, "void", eid, emp, uid, actor, old_note=row[2], new_note=tag,
                       detail="Správa docházky — absence", old_date=row[1])
        # když záznam vznikl ze schválené žádosti, zruš i tu žádost (jinak zůstane
        # viset jako approved+materialized — stará nekonzistence, viz docstring)
        if row[4] == "absence_req" and row[5]:
            with _Kousek(s):
                zbyva = s.execute(_t(
                    "SELECT count(*) FROM tenant.att_entry WHERE tenant_id=:t AND source_system='absence_req' "
                    "AND source_id=:z AND COALESCE(status,'')<>'superseded'"),
                    {"t": _TEN, "z": row[5]}).scalar() or 0
                if not zbyva:
                    s.execute(_t("UPDATE tenant.att_absence_request SET stav='cancelled', "
                                 "materialized=false, status_text=:st, decided_by_user_id=:u, "
                                 "decided_at=now() WHERE id=:z AND tenant_id=:t"),
                              {"z": row[5], "t": _TEN, "u": uid,
                               "st": ("Zrušeno ve Správě docházky (" + actor + "): " + duvod)[:500]})
    return data


# ── ÚPRAVA ───────────────────────────────────────────────────────────────────
@doch_zak_tab_router.post("/app/dochazka-abs/save")
async def dochazka_abs_save(req: Request) -> JSONResponse:
    """Úprava absence z přehledu. `radek_id` = „Z:<id>" nebo „D:<id,id,…>".
    Mění se: druh, období od–do, hodin/den, poznámka. Povinný důvod (audit)."""
    from sqlalchemy import text as _t
    from modules.erp.api.router import _att_fix_audit, _att_fix_notify, _user_jmeno
    from modules.strategie_pg.application import service as _pg
    uid = _kdo(req)
    if not uid:
        return _chyba("unauthorized", 401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    kind, ids = _parse_radek((b or {}).get("radek_id"))
    if not kind:
        return _chyba("Neznámé číslo řádku — obnov přehled a zkus to znovu.")
    duvod = str((b or {}).get("reason") or "").strip()[:300]
    if not duvod:
        return _chyba("Důvod úpravy je povinný (kvůli auditu).")
    typ = str((b or {}).get("typ") or "").strip()[:40]
    d_od, d_do = _den((b or {}).get("datum_od")), _den((b or {}).get("datum_do"))
    pozn = str((b or {}).get("poznamka") or "").strip()[:250]
    try:
        hpd = float((b or {}).get("hodin_den") or 8)
    except (TypeError, ValueError):
        hpd = 8.0
    if not (d_od and d_do):
        return _chyba("Vyplň období od–do.")
    if d_do < d_od:
        return _chyba("Datum „do“ nesmí být dřív než „od“.")
    if not typ:
        return _chyba("Vyber druh absence.")
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        if not _typ_id(s, typ):
            return _chyba("Neznámý druh absence.")
        # ── A) nepromítnutá žádost ──────────────────────────────────────────
        if kind == "zadost":
            zid = ids[0]
            r = s.execute(_t("SELECT employee_id, datum_od, datum_do, typ, COALESCE(note,'') "
                             "FROM tenant.att_absence_request WHERE id=:i AND tenant_id=:t"),
                          {"i": zid, "t": _TEN}).first()
            if not r:
                return _chyba("Žádost nenalezena.", 404)
            emp = int(r[0])
            bad = _smi(s, uid, emp)
            if bad:
                return _chyba(bad[0], bad[1])
            chyba_sd = _sd_check(emp, typ, hpd, d_od)
            if chyba_sd:
                return _chyba(chyba_sd)
            zam = _zamek(s, [r[1], r[2], d_od, d_do])
            if zam:
                return _chyba(zam, 409)
            s.execute(_t("UPDATE tenant.att_absence_request SET typ=:ty, datum_od=:od, datum_do=:do, "
                         "hours_per_day=:h, note=:n WHERE id=:i AND tenant_id=:t"),
                      {"ty": typ, "od": d_od, "do": d_do, "h": hpd, "n": pozn or None,
                       "i": zid, "t": _TEN})
            actor = _user_jmeno(s, uid)
            _att_fix_audit(s, "absence_edit", None, emp, uid, actor,
                           old_note="%s %s–%s" % (r[3], r[1], r[2]),
                           new_note="%s %s–%s" % (typ, d_od, d_do),
                           detail="Správa docházky — úprava žádosti #%d: %s" % (zid, duvod),
                           old_date=r[1])
            zust = _abs_recalc_balances(s, emp, {r[1].year, r[2].year, d_od.year, d_do.year})
            s.commit()
            try:
                _att_fix_notify(s, emp, uid, actor, "Úprava absence",
                                "%s upravil(a) tvou absenci: %s %s–%s. Důvod: %s"
                                % (actor, typ, d_od.strftime("%d.%m."), d_do.strftime("%d.%m.%Y"), duvod))
                s.commit()
            except Exception:
                s.rollback()
            return JSONResponse({"ok": True, "typ": "zadost", "id": zid, "zustatky": zust})
        # ── B) denní záznamy ────────────────────────────────────────────────
        rows = s.execute(_t("SELECT id, employee_id, entry_date FROM tenant.att_entry "
                            "WHERE tenant_id=:t AND id = ANY(:ids)"),
                         {"t": _TEN, "ids": ids}).fetchall()
        if not rows:
            return _chyba("Záznamy nenalezeny — obnov přehled.", 404)
        emps = {int(r[1]) for r in rows}
        if len(emps) != 1:
            return _chyba("Řádek míchá víc lidí — obnov přehled a zkus to znovu.")
        emp = emps.pop()
        bad = _smi(s, uid, emp)
        if bad:
            return _chyba(bad[0], bad[1])
        chyba_sd = _sd_check(emp, typ, hpd, d_od)
        if chyba_sd:
            return _chyba(chyba_sd)
        stare = [r[2] for r in rows]
        zam = _zamek(s, stare + [d_od, d_do])
        if zam:
            return _chyba(zam, 409)
        actor = _user_jmeno(s, uid)
        _znic_dny(s, [int(r[0]) for r in rows], emp, uid, actor, duvod)
        dnu = _zapis_dny(s, emp, typ, d_od, d_do, hpd,
                         (pozn or "") + (" · " if pozn else "") + "úprava: " + duvod, uid,
                         schvaleno=bool((b or {}).get("schvaleno", True)))
        roky = {d.year for d in stare} | {d_od.year, d_do.year}
        zust = _abs_recalc_balances(s, emp, roky)
        s.commit()
        try:
            _att_fix_notify(s, emp, uid, actor, "Úprava absence",
                            "%s upravil(a) tvou absenci: %s %s–%s (%d dnů). Důvod: %s"
                            % (actor, typ, d_od.strftime("%d.%m."), d_do.strftime("%d.%m.%Y"), dnu, duvod))
            s.commit()
        except Exception:
            s.rollback()
        return JSONResponse({"ok": True, "typ": "dny", "dnu": dnu, "zustatky": zust})
    except Exception as exc:  # noqa: BLE001
        try:
            s.rollback()
        except Exception:
            pass
        return _chyba(str(exc)[:200], 500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


# ── NOVÁ ABSENCE (za kohokoli) ───────────────────────────────────────────────
@doch_zak_tab_router.post("/app/dochazka-abs/new")
async def dochazka_abs_new(req: Request) -> JSONResponse:
    """Založí absenci ZA JINÉHO ČLOVĚKA — rovnou platnou (rozhodnutí Petry 30.7.:
    „platí hned"). Vznikne schválená žádost + denní záznamy, takže se to v přehledu
    ukáže se zdrojem „schválená žádost" a jde to dál normálně upravit i smazat."""
    from sqlalchemy import text as _t
    from modules.erp.api.router import _att_fix_audit, _att_fix_notify, _user_jmeno
    from modules.strategie_pg.application import service as _pg
    uid = _kdo(req)
    if not uid:
        return _chyba("unauthorized", 401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    cislo = str((b or {}).get("cislo_zam") or "").strip()
    typ = str((b or {}).get("typ") or "").strip()[:40]
    d_od, d_do = _den((b or {}).get("datum_od")), _den((b or {}).get("datum_do"))
    pozn = str((b or {}).get("poznamka") or "").strip()[:250]
    try:
        hpd = float((b or {}).get("hodin_den") or 8)
    except (TypeError, ValueError):
        hpd = 8.0
    schvaleno = bool((b or {}).get("schvaleno", True))
    if not cislo:
        return _chyba("Vyber pracovníka.")
    if not (d_od and d_do):
        return _chyba("Vyplň období od–do.")
    if d_do < d_od:
        return _chyba("Datum „do“ nesmí být dřív než „od“.")
    if not typ:
        return _chyba("Vyber druh absence.")
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        if not _typ_id(s, typ):
            return _chyba("Neznámý druh absence.")
        r = s.execute(_t("SELECT id, user_id FROM tenant.att_employee "
                         "WHERE tenant_id=:t AND cislo_zam::text=:c ORDER BY id LIMIT 1"),
                      {"t": _TEN, "c": cislo}).first()
        if not r:
            return _chyba("Pracovník s číslem %s není v evidenci docházky." % cislo, 404)
        emp, zam_uid = int(r[0]), r[1]
        chyba_sd = _sd_check(emp, typ, hpd, d_od)
        if chyba_sd:
            return _chyba(chyba_sd)
        bad = _smi(s, uid, emp)
        if bad:
            return _chyba(bad[0], bad[1])
        zam = _zamek(s, [d_od, d_do])
        if zam:
            return _chyba(zam, 409)
        if not _pracovni_dny(s, d_od, d_do):
            return _chyba("V zadaném období není žádný pracovní den.")
        actor = _user_jmeno(s, uid)
        zid = s.execute(_t(
            "INSERT INTO tenant.att_absence_request (tenant_id,employee_id,user_id,typ,datum_od,"
            "datum_do,hours_per_day,note,stav,status_text,decided_by_user_id,decided_at,"
            "materialized,created_at) "
            "VALUES (:t,:e,:u,:ty,:od,:do,:h,:n,:stv,:st,:by,now(),true,now()) RETURNING id"),
            {"t": _TEN, "e": emp, "u": (zam_uid or uid), "ty": typ, "od": d_od, "do": d_do,
             "h": hpd, "n": pozn or None, "by": uid,
             "stv": ("approved" if schvaleno else "pending"),
             "st": ("Zadáno ve Správě docházky (" + actor + ")"
                    + ("" if schvaleno else " — čeká na schválení"))[:500]}).scalar()
        dnu = _zapis_dny(s, emp, typ, d_od, d_do, hpd, pozn or "zadáno ve Správě docházky",
                         uid, zdroj="absence", zad_id=zid, schvaleno=schvaleno)
        _att_fix_audit(s, "absence_add", None, emp, uid, actor,
                       new_note="%s %s–%s (%d dnů)" % (typ, d_od, d_do, dnu),
                       detail="Správa docházky — nová absence #%s" % zid, old_date=d_od)
        zust = _abs_recalc_balances(s, emp, {d_od.year, d_do.year})
        s.commit()
        try:
            _att_fix_notify(s, emp, uid, actor, "Zapsaná absence",
                            "%s ti zapsal(a) absenci: %s %s–%s (%d dnů)."
                            % (actor, typ, d_od.strftime("%d.%m."), d_do.strftime("%d.%m.%Y"), dnu))
            s.commit()
        except Exception:
            s.rollback()
        return JSONResponse({"ok": True, "id": zid, "dnu": dnu, "zustatky": zust})
    except Exception as exc:  # noqa: BLE001
        try:
            s.rollback()
        except Exception:
            pass
        return _chyba(str(exc)[:200], 500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


# ── SMAZÁNÍ ──────────────────────────────────────────────────────────────────
@doch_zak_tab_router.post("/app/dochazka-abs/delete")
async def dochazka_abs_delete(req: Request) -> JSONResponse:
    """Smaže absenci z přehledu. Nikdy netrhá data z databáze — denní záznamy se
    zneplatní (superseded, vratné), žádost se označí jako zrušená. Povinný důvod."""
    from sqlalchemy import text as _t
    from modules.erp.api.router import _att_fix_audit, _att_fix_notify, _user_jmeno
    from modules.strategie_pg.application import service as _pg
    uid = _kdo(req)
    if not uid:
        return _chyba("unauthorized", 401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    kind, ids = _parse_radek((b or {}).get("radek_id"))
    if not kind:
        return _chyba("Neznámé číslo řádku — obnov přehled a zkus to znovu.")
    duvod = str((b or {}).get("reason") or "").strip()[:300]
    if not duvod:
        return _chyba("Důvod smazání je povinný (kvůli auditu).")
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        if kind == "zadost":
            zid = ids[0]
            r = s.execute(_t("SELECT employee_id, datum_od, datum_do, typ "
                             "FROM tenant.att_absence_request "
                             "WHERE id=:i AND tenant_id=:t"), {"i": zid, "t": _TEN}).first()
            if not r:
                return _chyba("Žádost nenalezena.", 404)
            emp = int(r[0])
            bad = _smi(s, uid, emp)
            if bad:
                return _chyba(bad[0], bad[1])
            zam = _zamek(s, [r[1], r[2]])
            if zam:
                return _chyba(zam, 409)
            actor = _user_jmeno(s, uid)
            dny = s.execute(_t("SELECT id FROM tenant.att_entry WHERE tenant_id=:t "
                               "AND source_system='absence_req' AND source_id=:z "
                               "AND COALESCE(status,'')<>'superseded'"),
                            {"t": _TEN, "z": zid}).fetchall()
            if dny:
                _znic_dny(s, [int(x[0]) for x in dny], emp, uid, actor, duvod)
            # RUŠÍ SE CELÁ SKUPINA STEJNÝCH ŽÁDOSTÍ (Peťa 31.7.2026).
            # Přehled slučuje shodné žádosti (týž člověk + druh + období) do JEDNOHO
            # řádku — Duspivová měla 21.7. „lékař" ČTYŘIKRÁT (appka je založila
            # v jedné minutě). Zrušení jedné proto vypadalo, že se nic nestalo:
            # na její místo se hned posunula další. Uživatel vidí jeden řádek a čeká,
            # že zmizí, takže rušíme všechny jeho sourozence.
            # (Vznik duplicit v appce je samostatná věc — patří Jirkovi/Kristý.)
            _txt = ("Zrušeno ve Správě docházky (" + actor + "): " + duvod)[:500]
            _n = s.execute(_t(
                "UPDATE tenant.att_absence_request SET stav='cancelled', materialized=false, "
                "status_text=:st, decided_by_user_id=:u, decided_at=now() "
                "WHERE tenant_id=:t AND employee_id=:e AND typ=:ty "
                "  AND datum_od=:od AND datum_do=:do "
                "  AND COALESCE(materialized,false)=false "
                "  AND COALESCE(stav,'') NOT IN ('cancelled','rejected')"),
                {"t": _TEN, "e": emp, "ty": r[3], "od": r[1], "do": r[2],
                 "u": uid, "st": _txt}).rowcount or 0
            if not _n:   # kdyby skupinový zápis nic nechytil, zruš aspoň vybranou
                s.execute(_t("UPDATE tenant.att_absence_request SET stav='cancelled', "
                             "materialized=false, status_text=:st, decided_by_user_id=:u, "
                             "decided_at=now() WHERE id=:i AND tenant_id=:t"),
                          {"i": zid, "t": _TEN, "u": uid, "st": _txt})
            _att_fix_audit(s, "absence_del", None, emp, uid, actor,
                           old_note="%s–%s" % (r[1], r[2]),
                           detail="Správa docházky — zrušení žádosti #%d: %s" % (zid, duvod),
                           old_date=r[1])
            zust = _abs_recalc_balances(s, emp, {r[1].year, r[2].year})
            s.commit()
            # POJISTKA (Peťa 30.7.2026): NIKDY nehlásit „smazáno", dokud to není
            # opravdu v datech. Dřív endpoint vrátil ok i když se změna cestou
            # ztratila (rollback v přepočtu zůstatku) — uživatel viděl zelenou
            # hlášku a řádek zůstal. Radši ověřit čtením než věřit návratovce.
            _ov = s.execute(_t("SELECT stav FROM tenant.att_absence_request "
                               "WHERE id=:i AND tenant_id=:t"),
                            {"i": zid, "t": _TEN}).scalar()
            if _ov != "cancelled":
                return _chyba("Smazání se neuložilo (stav zůstal „%s“). Zkus to prosím "
                              "znovu a pokud to bude znovu, pošli tuhle hlášku Claudovi."
                              % (_ov or "?"), 500)
            try:
                _att_fix_notify(s, emp, uid, actor, "Zrušená absence",
                                "%s zrušil(a) tvou absenci %s–%s. Důvod: %s"
                                % (actor, r[1].strftime("%d.%m."), r[2].strftime("%d.%m.%Y"), duvod))
                s.commit()
            except Exception:
                s.rollback()
            return JSONResponse({"ok": True, "typ": "zadost", "id": zid, "zustatky": zust})
        rows = s.execute(_t("SELECT id, employee_id, entry_date FROM tenant.att_entry "
                            "WHERE tenant_id=:t AND id = ANY(:ids)"),
                         {"t": _TEN, "ids": ids}).fetchall()
        if not rows:
            return _chyba("Záznamy nenalezeny — obnov přehled.", 404)
        emps = {int(r[1]) for r in rows}
        if len(emps) != 1:
            return _chyba("Řádek míchá víc lidí — obnov přehled a zkus to znovu.")
        emp = emps.pop()
        bad = _smi(s, uid, emp)
        if bad:
            return _chyba(bad[0], bad[1])
        zam = _zamek(s, [r[2] for r in rows])
        if zam:
            return _chyba(zam, 409)
        actor = _user_jmeno(s, uid)
        data = _znic_dny(s, [int(r[0]) for r in rows], emp, uid, actor, duvod)
        zust = _abs_recalc_balances(s, emp, {d.year for d in data} or {rows[0][2].year})
        s.commit()
        try:
            _att_fix_notify(s, emp, uid, actor, "Zrušená absence",
                            "%s zrušil(a) tvou absenci (%d dnů). Důvod: %s" % (actor, len(data), duvod))
            s.commit()
        except Exception:
            s.rollback()
        return JSONResponse({"ok": True, "typ": "dny", "dnu": len(data), "zustatky": zust})
    except Exception as exc:  # noqa: BLE001
        try:
            s.rollback()
        except Exception:
            pass
        return _chyba(str(exc)[:200], 500)
    finally:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass
