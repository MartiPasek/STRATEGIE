"""BOZP a PO cockpit — modul pro správu a řízení (Claude 2.7.2026, pro Míšu/Marti).

Multi-tenant. Řídící dokumenty (registr), registr rizik, periodické povinnosti
(revize/kontroly/školení/lékařské prohlídky s termíny + upomínky), úrazy.
Dokumenty žijí v RO zóně (D:\\Data\\ZZ_Marti-AI RO\\BOZP_PO\\...), tady je jejich
evidence + řízení termínů. Vzor: iso_cockpit.py.

Tabulky (tenant.*, založené bridge-approvalem #891):
  bozp_dokument / bozp_riziko / bozp_povinnost / bozp_uraz
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

bozp_router = APIRouter(prefix="/api/v1/erp", tags=["bozp-cockpit"])


def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _uid(request):
    try:
        return int(request.headers.get("X-User-Id") or request.query_params.get("uid") or 0)
    except Exception:
        return 0


def _tid(request, s, uid):
    t = request.query_params.get("tenant")
    if t:
        try:
            return int(t)
        except Exception:
            pass
    r = s.execute(_t("SELECT last_active_tenant_id AS t FROM public.users WHERE id=:i"), {"i": uid}).first()
    return (r.t if r and r.t else 2)


# ── Seed řídících dokumentů (28 uklizených v RO, 2.7.2026) ──────────────
_SEED_DOCS = [
    ("BOZP", "01_Smernice", "Provozní bezpečnostní předpis", "BOZP/01_Smernice_a_predpisy/BOZP_provozni_bezpecnostni_predpis.docx", None, None),
    ("BOZP", "01_Smernice", "Místní řád skladu", "BOZP/01_Smernice_a_predpisy/BOZP_mistni_rad_skladu_v1_20200213.doc", "v1", "2020-02-13"),
    ("BOZP", "01_Smernice", "Směrnice – pořizování strojů a zařízení", "BOZP/01_Smernice_a_predpisy/BOZP_smernice_porizovani_stroju_v1_20220819.doc", "v1", "2022-08-19"),
    ("BOZP", "01_Smernice", "Vnitřní předpis – zkušebna", "BOZP/01_Smernice_a_predpisy/BOZP_vnitrni_predpis_zkusebna_v2_20240522.doc", "v2", "2024-05-22"),
    ("BOZP", "01_Smernice", "Zákaz alkoholu a návykových látek", "BOZP/01_Smernice_a_predpisy/BOZP_zakaz_alkoholu_navykovych_latek_v1_20240522.doc", "v1", "2024-05-22"),
    ("BOZP", "10_Metrologie", "Metrologický řád organizace", "BOZP/10_Metrologie/BOZP_metrologicky_rad_v1_20201209.doc", "v1", "2020-12-09"),
    ("BOZP", "10_Metrologie", "Seznam měřidel", "BOZP/10_Metrologie/BOZP_seznam_meridel_v7_20190321.docx", "v7", "2019-03-21"),
    ("BOZP", "02_Registr_rizik", "Registr rizik 2025", "BOZP/02_Registr_rizik/BOZP_registr_rizik_2025.pdf", "2025", "2025-01-01"),
    ("BOZP", "02_Registr_rizik", "Kategorizace prací a pracovišť", "BOZP/02_Registr_rizik/BOZP_kategorizace_praci_v2_20201013.pdf", "v2", "2020-10-13"),
    ("BOZP", "03_Skoleni", "Školení BOZP", "BOZP/03_Skoleni_a_doklady/BOZP_skoleni_v4_20240820.doc", "v4", "2024-08-20"),
    ("BOZP", "03_Skoleni", "Správné odpovědi na testy BOZP a PO", "BOZP/03_Skoleni_a_doklady/BOZP_PO_spravne_odpovedi_testy.xlsx", None, None),
    ("BOZP", "03_Skoleni", "Test k ověření znalostí BOZP", "BOZP/03_Skoleni_a_doklady/BOZP_test_znalosti.doc", None, None),
    ("BOZP", "03_Skoleni", "Doklad o školení – administrativa/projekce", "BOZP/03_Skoleni_a_doklady/BOZP_doklad_skoleni_administrativa_v4_20260629.docx", "v4", "2026-06-29"),
    ("BOZP", "03_Skoleni", "Doklad o školení – elektromontér/zámečník", "BOZP/03_Skoleni_a_doklady/BOZP_doklad_skoleni_elektromonter_zamecnik_v4_20260629.docx", "v4", "2026-06-29"),
    ("BOZP", "04_OOPP", "Směrnice OOPP", "BOZP/04_OOPP/BOZP_smernice_OOPP.doc", None, None),
    ("BOZP", "04_OOPP", "Osobní ochranné pomůcky", "BOZP/04_OOPP/BOZP_OOPP_20190429.doc", None, "2019-04-29"),
    ("BOZP", "05_Lekarske_prohlidky", "Termíny lékařských prohlídek", "BOZP/05_Lekarske_prohlidky/BOZP_terminy_lekarskych_prohlidek_20180128.doc", None, "2018-01-28"),
    ("BOZP", "05_Lekarske_prohlidky", "Kategorizace – lékařské prohlídky", "BOZP/05_Lekarske_prohlidky/BOZP_kategorizace_lekarske_prohlidky.doc", None, None),
    ("BOZP", "05_Lekarske_prohlidky", "Smlouva s lékařem (PLP)", "BOZP/05_Lekarske_prohlidky/BOZP_smlouva_s_lekarem_20181206.pdf", None, "2018-12-06"),
    ("BOZP", "05_Lekarske_prohlidky", "Obsah lékárničky", "BOZP/05_Lekarske_prohlidky/BOZP_obsah_lekarnicky_v5_20240613.doc", "v5", "2024-06-13"),
    ("BOZP", "06_Urazy", "Kniha úrazů a drobných poranění", "BOZP/06_Urazy_a_nehody/BOZP_kniha_urazu_v3_20180119.doc", "v3", "2018-01-19"),
    ("BOZP", "06_Urazy", "Traumatologický plán", "BOZP/06_Urazy_a_nehody/BOZP_traumatologicky_plan.doc", None, None),
    ("BOZP", "07_Kontroly_revize", "Termíny kontrol a revizí (BOZP a PO)", "BOZP/07_Kontroly_a_revize/BOZP_PO_terminy_kontrol_a_revizi.doc", None, None),
    ("BOZP", "07_Kontroly_revize", "Záznam z prověrky BOZP 2025", "BOZP/07_Kontroly_a_revize/BOZP_zaznam_z_proverky_2025.pdf", "2025", "2025-01-01"),
    ("BOZP", "07_Kontroly_revize", "Protokol o kontrole vázacích prostředků", "BOZP/07_Kontroly_a_revize/BOZP_protokol_kontrola_vazaci_prostredky_v7_20251121.doc", "v7", "2025-11-21"),
    ("PO", "02_Pozarni_hlidka", "Požární hlídka", "PO/02_Pozarni_hlidka/PO_pozarni_hlidka_v2_20201109.doc", "v2", "2020-11-09"),
    ("PO", "03_Skoleni_PO", "Doklad o školení PO – zaměstnanci", "PO/03_Skoleni_PO/PO_doklad_skoleni_zamestnancu.doc", None, None),
    ("PO", "04_Zastupitelnost", "PO – zastupitelnost", "PO/04_Zastupitelnost/PO_zastupitelnost.doc", None, None),
]


def _ensure_seeded(s, tenant_id):
    n = s.execute(_t("SELECT count(*) c FROM tenant.bozp_dokument WHERE tenant_id=:t"), {"t": tenant_id}).first().c
    if n == 0:
        for oblast, kat, nazev, cesta, verze, datum in _SEED_DOCS:
            s.execute(_t("""INSERT INTO tenant.bozp_dokument(tenant_id,oblast,kategorie,nazev,soubor_ro,verze,datum_verze,vlastnik)
                            VALUES(:t,:o,:k,:n,:c,:v,:d,'Míša Hladíková')"""),
                      {"t": tenant_id, "o": oblast, "k": kat, "n": nazev, "c": cesta, "v": verze, "d": datum})
        s.commit()


@bozp_router.get("/app/bozp/overview")
async def bozp_overview(request: Request):
    uid = _uid(request)
    s = _sess()
    try:
        tid = _tid(request, s, uid)
        try:
            _ensure_seeded(s, tid)
        except Exception as ex:
            return JSONResponse({"ok": False, "tables_missing": True,
                                 "error": "Tabulky modulu čekají na schválení (#891). Detail: " + str(ex)[:120]})
        docs = [dict(x._mapping) for x in s.execute(_t("""
            SELECT id,oblast,kategorie,nazev,soubor_ro,verze,to_char(datum_verze,'DD.MM.YYYY') AS datum,platnost_do
            FROM tenant.bozp_dokument WHERE tenant_id=:t ORDER BY oblast,kategorie,nazev"""), {"t": tid})]
        rizika = [dict(x._mapping) for x in s.execute(_t("""
            SELECT id,oblast,pracoviste,cinnost,nebezpeci,dopad,pravdepodobnost,uroven,opatreni,odpovedny,
                   to_char(termin,'DD.MM.YYYY') AS termin,stav
            FROM tenant.bozp_riziko WHERE tenant_id=:t ORDER BY uroven DESC NULLS LAST,id"""), {"t": tid})]
        povinnosti = [dict(x._mapping) for x in s.execute(_t("""
            SELECT id,oblast,typ,predmet,perioda_mesice,to_char(posledni,'DD.MM.YYYY') AS posledni,
                   to_char(dalsi_termin,'DD.MM.YYYY') AS dalsi_termin,dalsi_termin AS dt,odpovedny,stav
            FROM tenant.bozp_povinnost WHERE tenant_id=:t ORDER BY dalsi_termin NULLS LAST,id"""), {"t": tid})]
        urazy = [dict(x._mapping) for x in s.execute(_t("""
            SELECT id,to_char(datum,'DD.MM.YYYY') AS datum,osoba,popis,stav
            FROM tenant.bozp_uraz WHERE tenant_id=:t ORDER BY datum DESC NULLS LAST,id"""), {"t": tid})]
        # upomínky: povinnosti s termínem do 60 dnů nebo po termínu
        po_term = s.execute(_t("""SELECT count(*) c FROM tenant.bozp_povinnost
            WHERE tenant_id=:t AND dalsi_termin IS NOT NULL AND dalsi_termin < CURRENT_DATE"""), {"t": tid}).first().c
        blizi = s.execute(_t("""SELECT count(*) c FROM tenant.bozp_povinnost
            WHERE tenant_id=:t AND dalsi_termin >= CURRENT_DATE AND dalsi_termin < CURRENT_DATE + 60"""), {"t": tid}).first().c
        tn = s.execute(_t("SELECT tenant_name AS name FROM public.tenants WHERE id=:t"), {"t": tid}).first()
        return JSONResponse({"ok": True, "tenant": (tn.name if tn else tid),
                             "dokumenty": docs, "rizika": rizika, "povinnosti": povinnosti, "urazy": urazy,
                             "upominky": {"po_termine": po_term, "blizi_se": blizi},
                             "pocty": {"dokumenty": len(docs), "rizika": len(rizika),
                                       "povinnosti": len(povinnosti), "urazy": len(urazy)}})
    finally:
        s.close()


@bozp_router.post("/app/bozp/riziko")
async def bozp_add_riziko(request: Request):
    b = await request.json()
    uid = _uid(request)
    s = _sess()
    try:
        tid = _tid(request, s, uid)
        dop = b.get("dopad"); prav = b.get("pravdepodobnost")
        uroven = (int(dop) * int(prav)) if (dop and prav) else None
        s.execute(_t("""INSERT INTO tenant.bozp_riziko(tenant_id,oblast,pracoviste,cinnost,nebezpeci,dopad,
                        pravdepodobnost,uroven,opatreni,odpovedny,termin)
                        VALUES(:t,:o,:pr,:c,:n,:d,:p,:u,:op,:od,:te)"""),
                  {"t": tid, "o": b.get("oblast", "BOZP"), "pr": b.get("pracoviste"), "c": b.get("cinnost"),
                   "n": b.get("nebezpeci"), "d": dop, "p": prav, "u": uroven, "op": b.get("opatreni"),
                   "od": b.get("odpovedny"), "te": b.get("termin") or None})
        s.commit()
        return JSONResponse({"ok": True})
    finally:
        s.close()


@bozp_router.post("/app/bozp/povinnost")
async def bozp_add_povinnost(request: Request):
    b = await request.json()
    uid = _uid(request)
    s = _sess()
    try:
        tid = _tid(request, s, uid)
        s.execute(_t("""INSERT INTO tenant.bozp_povinnost(tenant_id,oblast,typ,predmet,perioda_mesice,posledni,
                        dalsi_termin,odpovedny,stav,doklad_ro,poznamka)
                        VALUES(:t,:o,:ty,:p,:pm,:po,:dt,:od,:st,:dr,:pz)"""),
                  {"t": tid, "o": b.get("oblast", "BOZP"), "ty": b.get("typ"), "p": b.get("predmet"),
                   "pm": b.get("perioda_mesice") or None, "po": b.get("posledni") or None,
                   "dt": b.get("dalsi_termin") or None, "od": b.get("odpovedny"),
                   "st": b.get("stav", "planovano"), "dr": b.get("doklad_ro"), "pz": b.get("poznamka")})
        s.commit()
        return JSONResponse({"ok": True})
    finally:
        s.close()


@bozp_router.post("/app/bozp/uraz")
async def bozp_add_uraz(request: Request):
    b = await request.json()
    uid = _uid(request)
    s = _sess()
    try:
        tid = _tid(request, s, uid)
        s.execute(_t("""INSERT INTO tenant.bozp_uraz(tenant_id,datum,osoba,popis,zaznam_ro,stav)
                        VALUES(:t,:da,:os,:po,:zr,:st)"""),
                  {"t": tid, "da": b.get("datum") or None, "os": b.get("osoba"), "po": b.get("popis"),
                   "zr": b.get("zaznam_ro"), "st": b.get("stav", "evidovano")})
        s.commit()
        return JSONResponse({"ok": True})
    finally:
        s.close()
