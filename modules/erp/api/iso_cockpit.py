"""ISO 27001 cockpit — elektronické vedení ISMS (Marti 21.6.2026).

Univerzální, multi-tenant modul: každý zákazník = tenant, ISMS se naseeduje
z template (standardní sada dokumentů + kroky kritické cesty), cockpit provede
uživatele kroky, dokumenty jsou elektronické záznamy, e-podpis klikem (SES) +
audit (kdo/kdy/IP/zařízení). Auditorský web přístup read-only přes tokenovaný
odkaz. Cíl: i jako produkt pro certifikační firmu a digitalizaci ISO 27001.

Tabulky: tenant.iso_document / iso_task / iso_signature / iso_auditor_access /
iso_access_log (založeno 21.6., bridge #492).
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from sqlalchemy import text as _t


def _esc_html(s):
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _docx_to_html(full):
    """docx → HTML pro zobrazení v prohlížeči (mammoth, fallback python-docx)."""
    try:
        import mammoth
        with open(full, "rb") as f:
            h = mammoth.convert_to_html(f).value
        if h:
            return h
    except Exception:
        pass
    try:
        import docx as _docx
        from docx.oxml.ns import qn as _qn
        from docx.text.paragraph import Paragraph as _P
        from docx.table import Table as _Tb
        d = _docx.Document(full)
        out = []
        for ch in d.element.body.iterchildren():
            if ch.tag == _qn("w:p"):
                p = _P(ch, d)
                t = (p.text or "").strip()
                if not t:
                    continue
                st = (p.style.name or "").lower() if p.style else ""
                if "heading 1" in st or st == "title":
                    out.append("<h1>%s</h1>" % _esc_html(t))
                elif "heading 2" in st:
                    out.append("<h2>%s</h2>" % _esc_html(t))
                elif "heading" in st:
                    out.append("<h3>%s</h3>" % _esc_html(t))
                else:
                    out.append("<p>%s</p>" % _esc_html(t))
            elif ch.tag == _qn("w:tbl"):
                tb = _Tb(ch, d)
                out.append("<table>")
                for row in tb.rows:
                    out.append("<tr>" + "".join("<td>%s</td>" % _esc_html(c.text) for c in row.cells) + "</tr>")
                out.append("</table>")
        return "\n".join(out)
    except Exception:
        return None


def _wrap_doc_html(title, body):
    return ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>body{font:15px/1.6 -apple-system,Segoe UI,Roboto,system-ui;"
            "max-width:860px;margin:0 auto;padding:18px 18px 120px;color:#111;background:#fff}"
            "table{border-collapse:collapse;margin:8px 0;width:100%%}td,th{border:1px solid #aab;padding:4px 8px;"
            "vertical-align:top;font-size:13px}h1{font-size:22px}h2{font-size:18px;margin-top:20px}h3{font-size:15px}"
            "@media print{.noprint{display:none}}</style>"
            "<div class=noprint style='margin-bottom:12px'><button onclick='window.print()' "
            "style='padding:8px 14px;border:0;border-radius:8px;background:#1f3864;color:#fff;font-weight:700;cursor:pointer'>"
            "\U0001f5a8 Tisk</button></div>%s") % (_esc_html(title), body)


def _serve_file(full):
    """Zobraz dokument v prohlížeči: docx→HTML, pdf inline, ostatní stáhnout."""
    low = full.lower()
    if low.endswith(".docx"):
        h = _docx_to_html(full)
        if h is not None:
            return HTMLResponse(_wrap_doc_html(os.path.basename(full), h))
    if low.endswith(".pdf"):
        try:
            with open(full, "rb") as f:
                data = f.read()
            return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": "inline"})
        except Exception:
            pass
    return FileResponse(full, filename=os.path.basename(full))

try:
    from modules.erp.api.iso_controls_catalog import CONTROLS as _CONTROLS
except Exception:
    _CONTROLS = []
try:
    from modules.erp.api.iso_tisax_catalog import TISAX as _TISAX
except Exception:
    _TISAX = []

iso_router = APIRouter(prefix="/api/v1/erp", tags=["iso-cockpit"])

_REPO = os.environ.get("STRATEGIE_REPO_ROOT", r"C:\Projekty\STRATEGIE")
_DOC_DIR_REL = os.path.join("docs", "ISO27001")
_DEFAULT_TENANT = 12  # STRATEGIE - System s.r.o. (první referenční zákazník)

# ── Template: standardní sada ISMS dokumentů (kod, název, kategorie, pořadí, podpis, soubor) ──
_DOC_TPL = [
    ("DOC-00", "Seznam dokumentů ISMS", "ramec", 0, False, "DOC-00_Seznam_dokumentu_ISMS.docx"),
    ("DOC-01", "Rozsah ISMS", "ramec", 1, False, "DOC-01_Rozsah_ISMS.docx"),
    ("DOC-02", "Politika informační bezpečnosti", "politika", 2, True, "DOC-02_Politika_informacni_bezpecnosti.docx"),
    ("DOC-03", "Role a odpovědnosti", "ramec", 3, False, "DOC-03_Role_a_odpovednosti.docx"),
    ("DOC-04", "Metodika řízení rizik", "ramec", 4, False, "DOC-04_Metodika_rizeni_rizik.docx"),
    ("DOC-05", "Registr rizik", "zaznam", 5, False, "DOC-05_Registr_rizik.docx"),
    ("DOC-06", "Prohlášení o aplikovatelnosti (SoA)", "zaznam", 6, True, "DOC-06_Prohlaseni_o_aplikovatelnosti_SoA.docx"),
    ("DOC-07", "Plán ošetření rizik", "zaznam", 7, False, "DOC-07_Plan_osetreni_rizik.docx"),
    ("DOC-08", "Cíle informační bezpečnosti", "ramec", 8, True, "DOC-08_Cile_informacni_bezpecnosti.docx"),
    ("DOC-09", "Politika řízení přístupu", "politika", 9, True, "DOC-09_Politika_rizeni_pristupu.docx"),
    ("DOC-10", "Řízení incidentů", "politika", 10, True, "DOC-10_Rizeni_incidentu.docx"),
    ("DOC-11", "Zálohování a kontinuita", "politika", 11, True, "DOC-11_Zalohovani_a_kontinuita.docx"),
    ("DOC-12", "Bezpečnost dodavatelů", "politika", 12, True, "DOC-12_Bezpecnost_dodavatelu.docx"),
    ("DOC-13", "Akceptovatelné použití a bezpečnost lidí", "politika", 13, True, "DOC-13_Akceptovatelne_pouziti_a_bezpecnost_lidi.docx"),
    ("DOC-14", "Bezpečný vývoj a změny", "politika", 14, True, "DOC-14_Bezpecny_vyvoj_a_zmeny.docx"),
    ("DOC-15", "Evidence aktiv a klasifikace", "politika", 15, True, "DOC-15_Evidence_aktiv_a_klasifikace.docx"),
    ("DOC-16", "Program interního auditu", "zaznam", 16, False, "DOC-16_Program_internino_auditu.docx"),
    ("DOC-17", "Přezkoumání vedením", "zaznam", 17, True, "DOC-17_Prezkoumani_vedenim.docx"),
    ("DOC-18", "Neshody a nápravná opatření", "zaznam", 18, False, "DOC-18_Neshody_a_napravna_opatreni.docx"),
]

# ── Template: kroky kritické cesty (pořadí, fáze, název, popis, vlastník, doc_kod, podpis) ──
_TASK_TPL = [
    (1, "Plánování", "Naplnit registr rizik", "Upravit dopad/pravděpodobnost, doplnit rizika → DOC-05", "Kristý (ISMS)", "DOC-05", False),
    (2, "Plánování", "Odůvodnit SoA", "U každého opatření potvrdit stav a důkaz; podepsat → DOC-06", "Kristý (ISMS)", "DOC-06", True),
    (3, "Plánování", "Plán ošetření rizik", "U středních/vysokých rizik opatření + termín → DOC-07", "Kristý (ISMS)", "DOC-07", False),
    (4, "Vedení", "Schválit politiky (podpis vedení)", "Vedení elektronicky podepíše politiky (DOC-02, DOC-09..15)", "Vedení (Marti)", "DOC-02", True),
    (5, "Podpora", "Školení týmu", "Proškolit tým + elektronické potvrzení účasti", "Kristý (ISMS)", "DOC-13", True),
    (6, "Hodnocení", "Provést interní audit", "Projít checklist kap. 4-10, zapsat zjištění; podpis auditora → DOC-16", "Kristý (ISMS)", "DOC-16", True),
    (7, "Hodnocení", "Přezkoumání vedením", "Management review — vstupy/výstupy, zápis; podpis → DOC-17", "Vedení (Marti)", "DOC-17", True),
    (8, "Zlepšování", "Nápravná opatření", "Neshody z auditu → opatření + termín → DOC-18", "Kristý (ISMS)", "DOC-18", False),
    (9, "Obnova (DR)", "Plán obnovy — vyzkoušet a rozjet (restore drill)", "Michal dle iso27001_plan_obnovy_michal.md: restore drill, RTO/RPO, záznam → DOC-11", "Michal (obnova)", "DOC-11", False),
    (10, "Technika", "CVE sken závislostí", "Spustit pip-audit, vyřešit nálezy dle SLA", "Claude+Marti", None, False),
    (11, "Dodavatelé", "DPA s dodavateli", "Uzavřít zpracovatelské smlouvy se sub-processory → DOC-12", "Kristý (ISMS)", "DOC-12", False),
    (12, "Fyzická", "Attestace fyzické bezpečnosti", "Doložit od EUROSOFT / DC ČMIS", "Marti", None, False),
]

# Lidský průvodce ke krokům: poradi -> (kdo, popis lidsky, navod krok-za-krokem).
# Override při renderu (nemusíme migrovat DB). Realistické vlastnictví: datová/
# systémová práce = Marti + Claude; nezávislá kontrola (audit) = Kristý; podpis =
# vedení; obnova = Michal.
_TASK_GUIDE = {
    1: ("Mísa (TISAX)", "Projít seznam rizik a u každého říct, jak je vážné a pravděpodobné.",
        "Vede Mísa (manažerka kvality a bezpečnosti). Marti + Claude připraví předdraft, Mísa ho projde a doladí: u každého rizika řekne, jak je vážné a pravděpodobné."),
    2: ("Mísa (TISAX)", "U 93 opatření potvrdit stav a důkaz, pak podpis.",
        "Vede Mísa. U 93 bezpečnostních opatření je už vyplněný stav a důkaz (připravili jsme). Mísa projde, u sporných potvrdí a podepíše. Většina je hotová."),
    3: ("Mísa (TISAX)", "U vážnějších rizik dopsat, jak je ošetříme a do kdy.",
        "Vede Mísa. Navazuje na registr rizik: u vážnějších rizik se dopíše, jak je ošetříme a do kdy. Podklady připraví Claude."),
    4: ("Vedení (Marti)", "Vedení elektronicky podepíše hotové politiky (klik).",
        "Top management (jednatel) musí politiky schválit — to je věc vedení, nedá se delegovat. Politiky jsou napsané; Marti je projde a podepíše kliknutím (DOC-02 a DOC-09 až 15)."),
    5: ("Mísa (TISAX)", "Krátce proškolit lidi a zapsat, kdo se zúčastnil.",
        "Vede Mísa (Šárka pomůže s lidmi). Krátké proškolení v základech (hesla, phishing, ochrana dat), klidně online. Pak zapsat, kdo byl."),
    6: ("Mísa (TISAX)", "⭐ Klíčové: projít audit checklist a zapsat zjištění.",
        "Vede Mísa — má za sebou TISAX a interním auditům rozumí. Projde připravený checklist (kapitoly 4–10) a zapíše zjištění. Podklady má od nás."),
    7: ("Vedení (Marti)", "Krátká schůzka vedení → zápis → podpis.",
        "Přezkoumání vedením musí dělat top management (norma 9.3) — proto Marti. Krátká schůzka: stav bezpečnosti, rizika, cíle, zdroje → zápis a podpis. Podklady připraví Mísa s Claudem."),
    8: ("Mísa (TISAX)", "Co se najde v auditu, k tomu dopsat nápravu a termín.",
        "Vede Mísa. Co se najde při interním auditu, k tomu se dopíše nápravné opatření a termín. Claude pomůže se zápisem."),
    9: ("Michal", "⭐ Klíčové pro Michala: vyzkoušet obnovu ze zálohy.",
        "Vede Michal — je zodpovědný za plán obnovy a má přístup k serverům. Podle návodu vyzkouší obnovu dat ze zálohy, ověří, že fungují, a změří časy (RTO/RPO). Návod má připravený."),
    10: ("Automaticky (Claude)", "Běží automaticky týdně, nálezy řeší IT.",
         "Běží samo. Sken zranitelností jede každý týden; když se něco najde, vyřeší se aktualizací (Claude + Marti). Nikdo nemusí nic dělat."),
    11: ("Mísa (TISAX)", "S dodavateli dat uzavřít smlouvy o ochraně dat (DPA).",
         "Vede Mísa. S dodavateli, kteří zpracovávají naše data, se uzavřou smlouvy o ochraně údajů (DPA). Šablonu máme připravenou."),
    12: ("Mísa (TISAX)", "Doložit fyzické zabezpečení (serverovna / datacentrum).",
         "Vede Mísa (bezpečnost dat). Doloží se fyzické zabezpečení — potvrzení od EUROSOFT (serverovna) a datacentra ČMIS, kde běží servery."),
}


# ── pomocné (lazy import z router.py, ať není cirkulární) ──
def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _strict_parent(uid):
    """Jen rodič (cert-firma admin / multi-zákazník)."""
    from modules.erp.api.router import is_marti_parent
    return bool(uid) and is_marti_parent(uid)


def _is_parent(uid):
    """Přístup do cockpitu ISMS = rodič NEBO člen fw.iso_access (např. Michal).
    Nedělá z nikoho 'rodiče' (žádná cross-tenant práva) — jen vpustí do modulu."""
    if not uid:
        return False
    from modules.erp.api.router import is_marti_parent
    if is_marti_parent(uid):
        return True
    try:
        from core.database_data import get_data_session as _g
        from sqlalchemy import text as _tt
        s = _g()
        try:
            return bool(s.execute(_tt("SELECT 1 FROM fw.iso_access WHERE user_id=:u LIMIT 1"), {"u": uid}).first())
        finally:
            s.close()
    except Exception:
        return False


def _is_member(uid, tid):
    """Aktivní člen tenantu = smí číst (RO). RW = jen _is_parent (rodič / iso_access)."""
    if not uid or not tid:
        return False
    try:
        from core.database_data import get_data_session as _g
        from sqlalchemy import text as _tt
        s = _g()
        try:
            return bool(s.execute(_tt(
                "SELECT 1 FROM public.user_tenants WHERE user_id=:u AND tenant_id=:t "
                "AND membership_status IN ('active','invited') LIMIT 1"), {"u": uid, "t": tid}).first())
        finally:
            s.close()
    except Exception:
        return False


def _user_name(s, uid):
    try:
        r = s.execute(_t("SELECT COALESCE(first_name,'')||' '||COALESCE(last_name,'') AS j FROM public.users WHERE id=:i"), {"i": uid}).first()
        return (r.j.strip() if r and r.j else ("user %s" % uid))
    except Exception:
        return "user %s" % uid


def _tenant(req, uid, s):
    q = req.query_params.get("tenant")
    if q:
        try:
            return int(q)
        except Exception:
            pass
    try:
        r = s.execute(_t("SELECT last_active_tenant_id FROM public.users WHERE id=:i"), {"i": uid}).first()
        if r and r.last_active_tenant_id:
            return int(r.last_active_tenant_id)
    except Exception:
        pass
    return _DEFAULT_TENANT


def _client_ip(req):
    return (req.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (req.client.host if req.client else "") or "")


def _ensure_seeded(s, tenant_id):
    """Naseeduje ISMS pro tenant z template, pokud je prázdný (idempotentní)."""
    n = s.execute(_t("SELECT count(*) c FROM tenant.iso_document WHERE tenant_id=:t"), {"t": tenant_id}).first().c
    if n == 0:
        for kod, nazev, kat, por, sig, soub in _DOC_TPL:
            s.execute(_t("""INSERT INTO tenant.iso_document(tenant_id,kod,nazev,kategorie,poradi,vyzaduje_podpis,soubor_path)
                VALUES(:t,:k,:n,:kat,:p,:sig,:soub) ON CONFLICT (tenant_id,kod) DO NOTHING"""),
                {"t": tenant_id, "k": kod, "n": nazev, "kat": kat, "p": por, "sig": sig,
                 "soub": os.path.join(_DOC_DIR_REL, soub)})
    m = s.execute(_t("SELECT count(*) c FROM tenant.iso_task WHERE tenant_id=:t"), {"t": tenant_id}).first().c
    if m == 0:
        for por, faze, nazev, popis, vl, dk, sig in _TASK_TPL:
            s.execute(_t("""INSERT INTO tenant.iso_task(tenant_id,poradi,faze,nazev,popis,vlastnik,doc_kod,vyzaduje_podpis)
                VALUES(:t,:p,:f,:n,:po,:vl,:dk,:sig)"""),
                {"t": tenant_id, "p": por, "f": faze, "n": nazev, "po": popis, "vl": vl, "dk": dk, "sig": sig})
    c = s.execute(_t("SELECT count(*) c FROM tenant.iso_control WHERE tenant_id=:t"), {"t": tenant_id}).first().c
    if c == 0 and _CONTROLS:
        for i, (kod, oblast, nazev, apl, stav, zduv, dukaz) in enumerate(_CONTROLS):
            s.execute(_t("""INSERT INTO tenant.iso_control(tenant_id,kod,oblast,nazev,apl,stav,zduvodneni,dukaz,poradi)
                VALUES(:t,:k,:o,:n,:a,:s,:z,:d,:p) ON CONFLICT (tenant_id,kod) DO NOTHING"""),
                {"t": tenant_id, "k": kod, "o": oblast, "n": nazev, "a": apl, "s": stav, "z": zduv, "d": dukaz, "p": i})
    tx = s.execute(_t("SELECT count(*) c FROM tenant.tisax_item WHERE tenant_id=:t"), {"t": tenant_id}).first().c
    if tx == 0 and _TISAX:
        for i, (modul, kod, nazev, appl, isomap) in enumerate(_TISAX):
            stav = "probiha" if modul == "Information Security" else "ceka"
            s.execute(_t("""INSERT INTO tenant.tisax_item(tenant_id,modul,kod,nazev,applicable,stav,iso_map,poradi)
                VALUES(:t,:m,:k,:n,:a,:s,:im,:p) ON CONFLICT (tenant_id,kod) DO NOTHING"""),
                {"t": tenant_id, "m": modul, "k": kod, "n": nazev, "a": appl, "s": stav, "im": isomap, "p": i})
    s.commit()


def _log(s, tenant_id, kdo, akce, doc_kod, ip):
    try:
        s.execute(_t("INSERT INTO tenant.iso_access_log(tenant_id,kdo,akce,doc_kod,ip) VALUES(:t,:k,:a,:d,:i)"),
                  {"t": tenant_id, "k": kdo, "a": akce, "d": doc_kod, "i": ip})
        s.commit()
    except Exception:
        pass


def _docs_payload(s, tenant_id):
    rows = s.execute(_t("""SELECT kod,nazev,kategorie,verze,stav,poradi,vyzaduje_podpis
        FROM tenant.iso_document WHERE tenant_id=:t ORDER BY poradi"""), {"t": tenant_id}).mappings().all()
    sigs = s.execute(_t("""SELECT doc_kod, jmeno, role, to_char(signed_at,'DD.MM.YYYY HH24:MI') AS kdy
        FROM tenant.iso_signature WHERE tenant_id=:t AND doc_kod IS NOT NULL ORDER BY signed_at"""), {"t": tenant_id}).mappings().all()
    by = {}
    for sg in sigs:
        by.setdefault(sg["doc_kod"], []).append({"jmeno": sg["jmeno"], "role": sg["role"], "kdy": sg["kdy"]})
    out = []
    for d in rows:
        dd = dict(d); dd["podpisy"] = by.get(d["kod"], [])
        out.append(dd)
    return out


# ════════════════════════ COCKPIT (parent / Kristý) ════════════════════════

@iso_router.get("/app/iso/overview")
def iso_overview(req: Request):
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        ro = not _is_parent(uid)
        _ensure_seeded(s, tid)
        tasks = [dict(x) for x in s.execute(_t("""SELECT id,poradi,faze,nazev,popis,vlastnik,stav,doc_kod,vyzaduje_podpis,
            to_char(done_at,'DD.MM.YYYY HH24:MI') AS done_kdy
            FROM tenant.iso_task WHERE tenant_id=:t ORDER BY poradi"""), {"t": tid}).mappings().all()]
        for x in tasks:  # lidský průvodce — vlastník/popis/návod z katalogu (bez migrace DB)
            g = _TASK_GUIDE.get(x["poradi"])
            if g:
                x["vlastnik"], x["popis"], x["navod"] = g[0], g[1], g[2]
            else:
                x["navod"] = ""
        docs = _docs_payload(s, tid)
        tn = s.execute(_t("SELECT tenant_name AS name FROM public.tenants WHERE id=:t"), {"t": tid}).first()
        done = sum(1 for x in tasks if x["stav"] == "hotovo")
        cs = s.execute(_t("""SELECT count(*) FILTER (WHERE apl) AS apl_ano,
            count(*) FILTER (WHERE NOT apl) AS apl_ne, count(*) AS total
            FROM tenant.iso_control WHERE tenant_id=:t"""), {"t": tid}).mappings().first()
        doc06 = next((d["stav"] for d in docs if d["kod"] == "DOC-06"), "navrh")
        tx = s.execute(_t("""SELECT count(*) FILTER (WHERE applicable) AS appl,
            count(*) FILTER (WHERE applicable AND stav='hotovo') AS hot,
            count(DISTINCT modul) FILTER (WHERE applicable) AS moduly
            FROM tenant.tisax_item WHERE tenant_id=:t"""), {"t": tid}).mappings().first()
        is_cov = cs["apl_ano"] and round(100.0 * (s.execute(_t(
            "SELECT count(*) c FROM tenant.iso_control WHERE tenant_id=:t AND apl AND stav IN ('HOTOVO','ROZPRACOVÁNO')"),
            {"t": tid}).first().c) / cs["apl_ano"]) or 0
        return {"ok": True, "tenant_id": tid, "tenant_name": (tn.name if tn else str(tid)),
                "tasks": tasks, "docs": docs,
                "soa": {"apl_ano": cs["apl_ano"], "apl_ne": cs["apl_ne"], "total": cs["total"], "stav": doc06},
                "tisax": {"appl": tx["appl"], "hotovo": tx["hot"], "moduly": tx["moduly"], "is_coverage": is_cov, "verze": "VDA ISA 6.0.3"},
                "progress": {"hotovo": done, "celkem": len(tasks)}, "ro": ro}
    finally:
        s.close()


@iso_router.post("/app/iso/task-done")
async def iso_task_done(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        stav = "hotovo" if b.get("done", True) else "ceka"
        s.execute(_t("""UPDATE tenant.iso_task SET stav=:st, done_at=CASE WHEN :st='hotovo' THEN now() ELSE NULL END,
            done_by=CASE WHEN :st='hotovo' THEN :u ELSE NULL END WHERE id=:id AND tenant_id=:t"""),
            {"st": stav, "u": uid, "id": int(b["task_id"]), "t": tid})
        s.commit()
        _log(s, tid, _user_name(s, uid), "task_%s" % stav, None, _client_ip(req))
        return {"ok": True}
    finally:
        s.close()


@iso_router.post("/app/iso/sign")
async def iso_sign(req: Request):
    """SES e-podpis dokumentu (klik). Vloží podpis + nastaví dokument 'schvaleno' +
    auto-dokončí navázaný krok. Audit kdo/kdy/IP/zařízení."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    doc_kod = b.get("doc_kod")
    role = (b.get("role") or "schvalovatel").strip()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        jmeno = _user_name(s, uid)
        ip = _client_ip(req)
        zar = (req.headers.get("user-agent") or "")[:300]
        podpis_text = "Elektronicky podepsal %s dne %s (SES)" % (jmeno, datetime.now().strftime("%d.%m.%Y %H:%M"))
        s.execute(_t("""INSERT INTO tenant.iso_signature(tenant_id,doc_kod,user_id,jmeno,role,typ,podpis_text,ip,zarizeni)
            VALUES(:t,:d,:u,:j,:r,'SES',:pt,:ip,:z)"""),
            {"t": tid, "d": doc_kod, "u": uid, "j": jmeno, "r": role, "pt": podpis_text, "ip": ip, "z": zar})
        if doc_kod:
            s.execute(_t("UPDATE tenant.iso_document SET stav='schvaleno', updated_at=now() WHERE tenant_id=:t AND kod=:d"),
                      {"t": tid, "d": doc_kod})
            # auto-dokončení navázaného kroku, který vyžaduje podpis
            s.execute(_t("""UPDATE tenant.iso_task SET stav='hotovo', done_at=now(), done_by=:u
                WHERE tenant_id=:t AND doc_kod=:d AND vyzaduje_podpis=true AND stav<>'hotovo'"""),
                {"u": uid, "t": tid, "d": doc_kod})
        s.commit()
        _log(s, tid, jmeno, "podpis", doc_kod, ip)
        return {"ok": True, "podpis": podpis_text}
    finally:
        s.close()


@iso_router.get("/app/iso/doc/{kod}")
def iso_doc_file(kod: str, req: Request):
    """Stáhnout/zobrazit obsah dokumentu (parent nebo člen = RO)."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        r = s.execute(_t("SELECT soubor_path,nazev FROM tenant.iso_document WHERE tenant_id=:t AND kod=:k"),
                      {"t": tid, "k": kod}).first()
        if not r or not r.soubor_path:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        _log(s, tid, _user_name(s, uid), "view_doc", kod, _client_ip(req))
        return _serve_doc(r.soubor_path)
    finally:
        s.close()


def _serve_doc(soubor_path):
    # bezpečnost: jen soubory pod docs/ISO27001/
    full = os.path.normpath(os.path.join(_REPO, soubor_path))
    base = os.path.normpath(os.path.join(_REPO, _DOC_DIR_REL))
    if not full.startswith(base) or not os.path.isfile(full):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return _serve_file(full)


def _controls_payload(s, tenant_id):
    rows = s.execute(_t("""SELECT id,kod,oblast,nazev,apl,stav,zduvodneni,dukaz
        FROM tenant.iso_control WHERE tenant_id=:t ORDER BY poradi"""), {"t": tenant_id}).mappings().all()
    return [dict(r) for r in rows]


# (kod, název, perioda(text), perioda_dny(0=průběžně), popis, vazba)
# (kod, nazev, perioda, dny, popis, vazba, kdo, navod, doc_key)
_CADENCE = [
    ("cve", "Sken zranitelností (CVE)", "týdně", 7, "Kontrola závislostí proti známým zranitelnostem (pip-audit).", "A.8.8",
     "Automaticky (Claude + Marti)",
     "Běží sám každý týden — nic nedělejte. Výsledek je v kartě „Zranitelnosti“ výše; když se najdou opravitelné, IT naplánuje aktualizaci.", "cve"),
    ("access_review", "Přezkum přístupových práv", "čtvrtletně", 90, "Kdo má k čemu přístup — odebrat nadbytečné.", "A.5.18",
     "Mísa (TISAX)",
     "Projděte seznam uživatelů a jejich přístupy (kdo má k čemu právo). Odeberte nadbytečné a u lidí, co odešli, zrušte účty. Pak klikněte „Provedeno“.", ""),
    ("restore_drill", "Test obnovy ze zálohy (restore drill)", "čtvrtletně", 90, "Reálně vyzkoušet obnovu dat, změřit RTO/RPO.", "A.5.30 / A.8.13",
     "Michal",
     "Podle návodu obnovte data ze zálohy na testovacím místě, ověřte, že fungují, a změřte, jak dlouho to trvalo (RTO) a kolik dat by se mohlo ztratit (RPO). Zapište výsledek.", "michal"),
    ("secrets", "Rotace a kontrola hesel / tajemství", "průběžně", 0, "Správa hesel v šifrovaném trezoru, rotace klíčů a přístupů.", "A.5.17 / A.8.24",
     "Michal (správa hesel)",
     "Za pořádek v heslech zodpovídá Michal. Hesla patří do šifrovaného trezoru (karta výše), ne do papírů a e-mailů. Průběžná věc — není potřeba odškrtávat.", ""),
    ("internal_audit", "Interní audit ISMS", "ročně", 365, "Projít systém řízení (kap. 4–10), zapsat zjištění.", "A.9.2",
     "Mísa (TISAX)",
     "Otevřete připravený checklist (kapitoly 4–10), projděte body, zapište zjištění a nápravy. Pak „Provedeno“.", "handoff"),
    ("mgmt_review", "Přezkoumání vedením (management review)", "ročně", 365, "Vedení vyhodnotí stav, rizika, cíle a zdroje.", "A.9.3",
     "Vedení (Marti)",
     "Vedení se krátce sejde, projde stav bezpečnosti, rizika, cíle a zdroje a rozhodne další kroky. Stačí krátký zápis.", "dorazeni"),
    ("risk_review", "Revize rizik (registr rizik)", "ročně", 365, "Aktualizovat hrozby, dopady, opatření.", "A.6.1.2",
     "Mísa (TISAX)",
     "Otevřete registr rizik, aktualizujte hrozby, dopady a opatření a znovu je odsouhlaste.", "handoff"),
    ("training", "Školení bezpečnosti", "ročně", 365, "Proškolit lidi, doložit záznam.", "A.6.3",
     "Mísa (TISAX)",
     "Krátce proškolte lidi v základech (hesla, phishing, ochrana dat) a doložte záznam, kdo se zúčastnil.", ""),
    ("supplier_review", "Revize a hodnocení dodavatelů", "ročně", 365, "Zkontrolovat sub-processory, DPA, certifikace.", "A.5.22",
     "Mísa (TISAX)",
     "Projděte dodavatele a sub-processory, jejich smlouvy o ochraně dat (DPA) a certifikace.", "dodavatele"),
    ("policy_review", "Aktualizace politik a dokumentace", "ročně", 365, "Projít a znovu schválit politiky.", "A.5.1",
     "Mísa (TISAX)",
     "Projděte politiky a dokumenty, aktualizujte zastaralé a znovu je schvalte podpisem v přehledu dokumentů.", "dorazeni"),
    ("bcp_test", "Test plánu kontinuity (BCP)", "ročně", 365, "Ověřit, že firma přežije výpadek.", "A.5.29 / A.5.30",
     "Michal",
     "Vyzkoušejte scénář výpadku (např. serveru) a ověřte, že firma dokáže pokračovat. Zapište výsledek.", "dr"),
]


@iso_router.get("/app/iso/vault-overview")
def iso_vault_overview(req: Request):
    """Pořádek v heslech (firemní přehled, BEZ obsahu) — největší reálná bolest firem.
    Kolik lidí už používá šifrovaný trezor a kolik hesel je bezpečně uloženo."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        r = s.execute(_t("""SELECT count(DISTINCT user_id) AS lidi, count(*) AS hesla
            FROM tenant.user_secret WHERE tenant_id=:t"""), {"t": tid}).mappings().first()
        ppl = s.execute(_t("SELECT count(*) c FROM public.user_tenants WHERE tenant_id=:t AND membership_status IN ('active','invited')"),
                        {"t": tid}).first()
        return {"ok": True, "lidi": r["lidi"], "hesla": r["hesla"], "lidi_celkem": (ppl.c if ppl else None)}
    finally:
        s.close()


def _cadence_compute(s, tid):
    """Stav kalendáře bezpečnosti pro tenant (sdílené endpointem i připomínkami)."""
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    runs = {r.kod: r.last_done for r in s.execute(_t(
        "SELECT kod, last_done FROM tenant.iso_cadence_run WHERE tenant_id=:t"), {"t": tid}).all()}
    cve_last = s.execute(_t("SELECT max(created_at) AS m FROM fw.cve_run")).scalar()
    out = []
    for kod, nazev, perioda, dny, popis, vazba, kdo, navod, doc in _CADENCE:
        last = cve_last if kod == "cve" else runs.get(kod)
        stav = "prubezne"
        due_s = None
        dleft = None
        if dny > 0:
            if not last:
                stav = "nikdy"
            else:
                due = last + _dt.timedelta(days=dny)
                dleft = (due - now).days
                due_s = due.strftime("%d.%m.%Y")
                if dleft < 0:
                    stav = "po_terminu"
                elif dleft <= max(2, int(dny * 0.2)):
                    stav = "blizi"
                else:
                    stav = "ok"
        out.append({"kod": kod, "nazev": nazev, "perioda": perioda, "popis": popis, "vazba": vazba,
                    "kdo": kdo, "navod": navod, "doc": doc,
                    "last": (last.strftime("%d.%m.%Y") if last else None), "due": due_s,
                    "dleft": dleft, "stav": stav, "auto": (kod == "cve")})
    return out


@iso_router.get("/app/iso/cadence")
def iso_cadence(req: Request):
    """Aktivní kalendář bezpečnosti — co se kdy naposledy udělalo, kdy je to příště,
    a barevný stav (aktuální / blíží se / po termínu). Modul jako živý hlídač."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        return {"ok": True, "cadence": _cadence_compute(s, tid)}
    finally:
        s.close()


@iso_router.post("/app/iso/cadence-done")
async def iso_cadence_done(req: Request):
    """Zaznamenat, že pravidelná kontrola byla právě provedena (resetuje termín)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    kod = (b.get("kod") or "").strip()
    if not kod:
        return JSONResponse({"ok": False, "error": "kod chybí"}, status_code=400)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        s.execute(_t("""INSERT INTO tenant.iso_cadence_run(tenant_id,kod,last_done,by_uid,updated_at)
            VALUES(:t,:k,now(),:u,now())
            ON CONFLICT (tenant_id,kod) DO UPDATE SET last_done=now(), by_uid=:u, updated_at=now()"""),
            {"t": tid, "k": kod, "u": uid})
        s.commit()
        _log(s, tid, _user_name(s, uid), "cadence_done", kod, _client_ip(req))
        return {"ok": True}
    finally:
        s.close()


_ISO_REM_STATE = {"last_date": None}


def _iso_reminders_run(force=False):
    """Proaktivní hlídač (volá lifespan 1×/den i ruční spuštění):
    1) auto-CVE sken, pokud poslední byl před ≥7 dny,
    2) digest e-mail rodičům o kontrolách po termínu / blížících se (anti-spam: max 1×/3 dny per subjekt)."""
    import datetime as _dt
    today = _dt.date.today().isoformat()
    if not force and _ISO_REM_STATE.get("last_date") == today:
        return {"ok": True, "skipped": True}
    _ISO_REM_STATE["last_date"] = today
    now = _dt.datetime.now(_dt.timezone.utc)
    res = {"ok": True, "cve_ran": False, "digestu": 0}
    # 1) auto-CVE
    try:
        s = _sess()
        try:
            cve_last = s.execute(_t("SELECT max(created_at) AS m FROM fw.cve_run")).scalar()
        finally:
            s.close()
        if (not cve_last) or ((now - cve_last).days >= 7):
            _cve_scan_exec(None)
            res["cve_ran"] = True
    except Exception:
        pass
    # 2) digest termínů
    try:
        s = _sess()
        try:
            tenants = [r[0] for r in s.execute(_t("SELECT DISTINCT tenant_id FROM tenant.iso_task")).all()]
            # Marti 24.6.2026: digest chodí ZODPOVĚDNÝM (Míša = ISO/TISAX,
            # Michal Šik = plán obnovy), KOPIE rodičům (Marti + Kristý).
            digest_to = _users_emails(s, (16, 19))   # Míša + Michal Šik
            digest_cc = _users_emails(s, (1, 11))    # Marti + Kristý
            if not digest_to:
                digest_to = _parent_emails(s)        # fallback, kdyby zodpovědní neměli e-mail
            for tid in tenants:
                items = _cadence_compute(s, tid)
                over = [i for i in items if i["stav"] in ("po_terminu", "nikdy")]
                soon = [i for i in items if i["stav"] == "blizi"]
                if not (over or soon):
                    continue
                dg = s.execute(_t("SELECT last_done FROM tenant.iso_cadence_run WHERE tenant_id=:t AND kod='_digest'"),
                               {"t": tid}).scalar()
                if dg and (now - dg).days < 3:
                    continue  # nedávno posláno — nespamovat
                tn = s.execute(_t("SELECT tenant_name FROM public.tenants WHERE id=:t"), {"t": tid}).first()
                tnm = tn.tenant_name if tn else tid
                body = ("<p>Dobrý den, tady váš průvodce bezpečností (%s). 🌳</p>"
                        "<p>Nic se neděje — jen vás v klidu provázím, ať na nic společně nezapomeneme. "
                        "Tohle je seznam věcí, které nás <b>ještě čekají</b> na cestě k certifikaci. "
                        "Není to úkol na dnes a není to všechno na jednoho — klidně po jedné, vlastním tempem.</p>"
                        "<p><b>Ještě nás čeká:</b></p><ul>") % tnm
                for i in over + soon:
                    body += "<li>○ %s — <i style='color:#888'>má na starosti: %s</i></li>" % (i["nazev"], i.get("kdo") or "—")
                body += ("</ul><p>Jak na to: v přehledu u každé položky je tlačítko "
                         "<b>„✓ Provedeno“</b> — jak se věc udělá, odškrtne se a já vás přestanu na ni upozorňovat. "
                         "Kdo má co na starosti a návody najdete přímo v přehledu.</p>"
                         "<p>👉 <a href='%s/iso?tenant=%s'>Otevřít přehled bezpečnosti</a></p>"
                         "<p>Ozvu se zase, až bude vhodná chvíle. Hezký den!</p>") % (_PORTAL, tid)
                for em in digest_to:
                    _notify_email(s, tid, em, "🌳 Váš průvodce bezpečností — co nás ještě čeká (%s)" % tnm, body,
                                  cc=[c for c in digest_cc if c != em])
                s.execute(_t("""INSERT INTO tenant.iso_cadence_run(tenant_id,kod,last_done,updated_at)
                    VALUES(:t,'_digest',now(),now())
                    ON CONFLICT (tenant_id,kod) DO UPDATE SET last_done=now(), updated_at=now()"""), {"t": tid})
                s.commit()
                res["digestu"] += 1
        finally:
            s.close()
    except Exception:
        pass
    return res


@iso_router.post("/app/iso/reminders-run")
async def iso_reminders_run_ep(req: Request):
    """Ruční spuštění kontroly termínů + auto-CVE (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    return _iso_reminders_run(force=True)


def _cve_scan_exec(by_uid):
    """Spustí pip-audit, uloží do fw.cve_run, vrátí dict. Sdílené endpointem i auto-během."""
    import subprocess as _sp, sys as _sys, json as _j
    try:
        r = _sp.run([_sys.executable, "-m", "pip_audit", "-f", "json", "--progress-spinner", "off"],
                    capture_output=True, text=True, timeout=300, cwd=_REPO)
    except _sp.TimeoutExpired:
        return {"ok": False, "error": "timeout (sken trval příliš dlouho)"}
    except Exception as e:
        return {"ok": False, "error": "spuštění selhalo: %s" % e}
    out = (r.stdout or "").strip()
    err = (r.stderr or "")
    if "No module named" in err and "pip_audit" in err:
        return {"ok": False, "error": "pip-audit není nainstalován na serveru",
                "install": "Na cloud APP spusť: python -m poetry add --group dev pip-audit  → pak restart API."}
    try:
        data = _j.loads(out)
    except Exception:
        return {"ok": False, "error": "nelze přečíst výstup skenu", "detail": (err[-300:] or out[-200:] or "?")}
    deps = data.get("dependencies", []) if isinstance(data, dict) else (data or [])
    found = 0
    fixable = 0
    lines = []
    for d in deps:
        for v in (d.get("vulns") or d.get("vulnerabilities") or []):
            found += 1
            fx = v.get("fix_versions") or []
            if fx:
                fixable += 1
            lines.append("%s %s: %s%s" % (d.get("name"), d.get("version"), v.get("id"),
                                          (" (fix %s)" % fx[0] if fx else " (bez opravy)")))
    summary = "\n".join(lines[:40]) if lines else "Žádné známé zranitelnosti v závislostech. ✅"
    s = _sess()
    try:
        s.execute(_t("INSERT INTO fw.cve_run(found,fixable,summary,ok,by_uid) VALUES(:f,:x,:s,true,:u)"),
                  {"f": found, "x": fixable, "s": summary, "u": by_uid})
        s.commit()
    finally:
        s.close()
    return {"ok": True, "found": found, "fixable": fixable, "summary": summary}


@iso_router.post("/app/iso/cve-run")
def iso_cve_run(req: Request):
    """Spustí kontrolu zranitelností závislostí (pip-audit) + uloží výsledek."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    res = _cve_scan_exec(uid)
    return res if res.get("ok") else JSONResponse(res)


@iso_router.get("/app/iso/cve-last")
def iso_cve_last(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        r = s.execute(_t("""SELECT found, fixable, summary, ok,
            to_char(created_at,'DD.MM.YYYY HH24:MI') AS kdy FROM fw.cve_run ORDER BY id DESC LIMIT 1""")).mappings().first()
        return {"ok": True, "last": (dict(r) if r else None)}
    finally:
        s.close()


@iso_router.get("/app/iso/controls")
def iso_controls(req: Request):
    """SoA — 93 kontrol Annex A pro tenant (parent nebo člen = RO)."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        _ensure_seeded(s, tid)
        return {"ok": True, "controls": _controls_payload(s, tid), "ro": (not _is_parent(uid))}
    finally:
        s.close()


@iso_router.post("/app/iso/control-update")
async def iso_control_update(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        fields, params = [], {"id": int(b["id"]), "t": tid}
        for k in ("apl", "stav", "zduvodneni", "dukaz"):
            if k in b:
                fields.append("%s=:%s" % (k, k)); params[k] = b[k]
        if fields:
            s.execute(_t("UPDATE tenant.iso_control SET %s, updated_at=now() WHERE id=:id AND tenant_id=:t" % ",".join(fields)), params)
            s.commit()
            _log(s, tid, _user_name(s, uid), "control_update", b.get("kod"), _client_ip(req))
        return {"ok": True}
    finally:
        s.close()


def _tisax_payload(s, tenant_id):
    rows = s.execute(_t("""SELECT id,modul,kod,nazev,applicable,stav,iso_map,poznamka
        FROM tenant.tisax_item WHERE tenant_id=:t ORDER BY poradi"""), {"t": tenant_id}).mappings().all()
    return [dict(r) for r in rows]


@iso_router.get("/app/iso/tisax")
def iso_tisax(req: Request):
    """TISAX (VDA ISA 6.0.3) položky pro tenant (parent nebo člen = RO)."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        _ensure_seeded(s, tid)
        return {"ok": True, "verze": "VDA ISA 6.0.3", "tisax": _tisax_payload(s, tid), "ro": (not _is_parent(uid))}
    finally:
        s.close()


@iso_router.post("/app/iso/tisax-update")
async def iso_tisax_update(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        fields, params = [], {"id": int(b["id"]), "t": tid}
        for k in ("applicable", "stav", "poznamka"):
            if k in b:
                fields.append("%s=:%s" % (k, k)); params[k] = b[k]
        if fields:
            s.execute(_t("UPDATE tenant.tisax_item SET %s, updated_at=now() WHERE id=:id AND tenant_id=:t" % ",".join(fields)), params)
            s.commit()
            _log(s, tid, _user_name(s, uid), "tisax_update", b.get("kod"), _client_ip(req))
        return {"ok": True}
    finally:
        s.close()


_DOC_STORE_ROOT = os.environ.get("STRATEGIE_DOC_STORE") or r"D:\Data\STRATEGIE\Dokumenty"


def _serve_storage(storage_path):
    """Servíruje soubor z úložiště dokumentů STRATEGIE (jen pod Dokumenty root)."""
    if not storage_path:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    full = os.path.normpath(storage_path)
    root = os.path.normpath(_DOC_STORE_ROOT)
    if not full.startswith(root) or not os.path.isfile(full):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return _serve_file(full)


def _evidence_payload(s, tenant_id):
    """Nahrané dokumenty STRATEGIE pro tenant (jen ISO/TISAX/bezpečnostní projekty)."""
    rows = s.execute(_t("""SELECT d.id, d.name, d.file_type, COALESCE(p.name,'') AS projekt
        FROM public.documents d LEFT JOIN public.projects p ON p.id=d.project_id
        WHERE d.tenant_id=:t AND (p.name ILIKE '%tisax%' OR p.name ILIKE '%iso%' OR p.name ILIKE '%bezpe%')
        ORDER BY p.name, d.name"""), {"t": tenant_id}).mappings().all()
    out = []
    for r in rows:
        nm = r["name"] or ""
        parts = nm.split("/")
        out.append({"id": r["id"], "nazev": parts[-1], "folder": "/".join(parts[1:-1]),
                    "projekt": r["projekt"], "typ": r["file_type"]})
    return out


@iso_router.get("/app/iso/evidence")
def iso_evidence(req: Request):
    """Nahrané dokumenty (evidence) ze STRATEGIE pro tenant (parent nebo člen = RO)."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        return {"ok": True, "evidence": _evidence_payload(s, tid)}
    finally:
        s.close()


@iso_router.get("/app/iso/evidence-doc/{doc_id}")
def iso_evidence_doc(doc_id: int, req: Request):
    """Otevřít nahraný dokument (parent nebo člen = RO), jen z vlastního tenantu."""
    uid = _uid(req)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        if not (_is_parent(uid) or _is_member(uid, tid)):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        r = s.execute(_t("SELECT storage_path FROM public.documents WHERE id=:i AND tenant_id=:t"),
                      {"i": int(doc_id), "t": tid}).first()
        if not r:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        _log(s, tid, _user_name(s, uid), "view_evidence", str(doc_id), _client_ip(req))
        return _serve_storage(r.storage_path)
    finally:
        s.close()


# ════════════════════════ AUDITORSKÝ PŘÍSTUP (parent správa) ════════════════════════

@iso_router.post("/app/iso/auditor/create")
async def iso_auditor_create(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        tok = secrets.token_urlsafe(24)
        th = hashlib.sha256(tok.encode()).hexdigest()
        dny = int(b.get("dny") or 30)
        s.execute(_t("""INSERT INTO tenant.iso_auditor_access(tenant_id,token_hash,auditor_jmeno,auditor_email,platnost_do,vytvoril)
            VALUES(:t,:h,:j,:e,:pd,:u)"""),
            {"t": tid, "h": th, "j": (b.get("jmeno") or "").strip(), "e": (b.get("email") or "").strip(),
             "pd": datetime.utcnow() + timedelta(days=dny), "u": uid})
        s.commit()
        _log(s, tid, _user_name(s, uid), "auditor_create", None, _client_ip(req))
        # plaintext token jen teď (drží se jen hash)
        return {"ok": True, "token": tok, "odkaz": "/iso-audit/%s" % tok, "platnost_dny": dny}
    finally:
        s.close()


@iso_router.get("/app/iso/auditor/list")
def iso_auditor_list(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        rows = s.execute(_t("""SELECT id,auditor_jmeno,auditor_email,to_char(platnost_do,'DD.MM.YYYY') AS do,revoked,
            to_char(created_at,'DD.MM.YYYY') AS od FROM tenant.iso_auditor_access WHERE tenant_id=:t ORDER BY created_at DESC"""),
            {"t": tid}).mappings().all()
        return {"ok": True, "auditori": [dict(x) for x in rows]}
    finally:
        s.close()


@iso_router.post("/app/iso/auditor/revoke")
async def iso_auditor_revoke(req: Request):
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        s.execute(_t("UPDATE tenant.iso_auditor_access SET revoked=true WHERE id=:id AND tenant_id=:t"),
                  {"id": int(b["id"]), "t": tid})
        s.commit()
        return {"ok": True}
    finally:
        s.close()


def _auditor_tenant(s, token):
    """Validuje token → vrátí tenant_id nebo None."""
    if not token:
        return None
    th = hashlib.sha256(token.encode()).hexdigest()
    r = s.execute(_t("""SELECT tenant_id FROM tenant.iso_auditor_access
        WHERE token_hash=:h AND revoked=false AND (platnost_do IS NULL OR platnost_do > now()) LIMIT 1"""),
        {"h": th}).first()
    return r.tenant_id if r else None


@iso_router.get("/app/iso/audit/{token}/data")
def iso_audit_data(token: str, req: Request):
    """Read-only data pro auditorský portál (bez loginu, jen platný token)."""
    s = _sess()
    try:
        tid = _auditor_tenant(s, token)
        if not tid:
            return JSONResponse({"ok": False, "error": "invalid_or_expired"}, status_code=403)
        _log(s, tid, "auditor", "portal_view", None, _client_ip(req))
        tn = s.execute(_t("SELECT tenant_name AS name FROM public.tenants WHERE id=:t"), {"t": tid}).first()
        return {"ok": True, "tenant_name": (tn.name if tn else str(tid)),
                "docs": _docs_payload(s, tid), "controls": _controls_payload(s, tid),
                "evidence": _evidence_payload(s, tid)}
    finally:
        s.close()


@iso_router.get("/app/iso/audit/{token}/doc/{kod}")
def iso_audit_doc(token: str, kod: str, req: Request):
    """Read-only obsah dokumentu pro auditora (platný token)."""
    s = _sess()
    try:
        tid = _auditor_tenant(s, token)
        if not tid:
            return JSONResponse({"ok": False, "error": "invalid_or_expired"}, status_code=403)
        r = s.execute(_t("SELECT soubor_path FROM tenant.iso_document WHERE tenant_id=:t AND kod=:k"),
                      {"t": tid, "k": kod}).first()
        if not r or not r.soubor_path:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        _log(s, tid, "auditor", "view_doc", kod, _client_ip(req))
        return _serve_doc(r.soubor_path)
    finally:
        s.close()


@iso_router.get("/app/iso/audit/{token}/evidence-doc/{doc_id}")
def iso_audit_evidence_doc(token: str, doc_id: int, req: Request):
    """Read-only nahraný dokument pro auditora (platný token, jen z daného tenantu)."""
    s = _sess()
    try:
        tid = _auditor_tenant(s, token)
        if not tid:
            return JSONResponse({"ok": False, "error": "invalid_or_expired"}, status_code=403)
        r = s.execute(_t("SELECT storage_path FROM public.documents WHERE id=:i AND tenant_id=:t"),
                      {"i": int(doc_id), "t": tid}).first()
        if not r:
            return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
        _log(s, tid, "auditor", "view_evidence", str(doc_id), _client_ip(req))
        return _serve_storage(r.storage_path)
    finally:
        s.close()


def _auditor_access_row(s, token):
    if not token:
        return None
    th = hashlib.sha256(token.encode()).hexdigest()
    return s.execute(_t("""SELECT id, tenant_id, auditor_jmeno FROM tenant.iso_auditor_access
        WHERE token_hash=:h AND revoked=false AND (platnost_do IS NULL OR platnost_do > now()) LIMIT 1"""),
        {"h": th}).first()


@iso_router.post("/app/iso/audit/{token}/feedback")
async def iso_audit_feedback(token: str, req: Request):
    """Auditor / certifikační firma píše přímo do portálu (bez e-mailu) → naše DB."""
    b = await req.json()
    s = _sess()
    try:
        row = _auditor_access_row(s, token)
        if not row:
            return JSONResponse({"ok": False, "error": "invalid_or_expired"}, status_code=403)
        typ = (b.get("typ") or "otazka").strip()
        if typ not in _KB_TYPY:
            typ = "otazka"
        txt = (b.get("text") or "").strip()
        if not txt:
            return JSONResponse({"ok": False, "error": "prázdný text"}, status_code=400)
        s.execute(_t("""INSERT INTO tenant.doc_feedback(tenant_id,doc_key,sekce,typ,text,jmeno,zdroj,auditor_access_id)
            VALUES(:t,:dk,:sek,:ty,:tx,:j,'auditor',:aid)"""),
            {"t": row.tenant_id, "dk": (b.get("doc_key") or "")[:80], "sek": (b.get("sekce") or "")[:200],
             "ty": typ, "tx": txt[:4000], "j": row.auditor_jmeno or "auditor", "aid": row.id})
        s.commit()
        _log(s, row.tenant_id, "auditor:%s" % (row.auditor_jmeno or "?"), "feedback", b.get("doc_key"), _client_ip(req))
        body = ("<p>🔔 <b>Auditor %s</b> napsal v portálu (%s):</p><blockquote>%s</blockquote>"
                "<p>Reagujte v cockpitu: <a href='%s/iso'>%s/iso</a></p>") % (
            row.auditor_jmeno or "auditor", typ, txt[:1000], _PORTAL, _PORTAL)
        for em in _parent_emails(s):
            _notify_email(s, row.tenant_id, em, "🔔 Auditor napsal v portálu — %s" % (row.auditor_jmeno or ""), body)
        return {"ok": True}
    finally:
        s.close()


@iso_router.get("/app/iso/audit/{token}/feedback")
def iso_audit_feedback_list(token: str, req: Request):
    """Auditor vidí svoje dotazy + naše odpovědi (obousměrně, bez e-mailu)."""
    s = _sess()
    try:
        row = _auditor_access_row(s, token)
        if not row:
            return JSONResponse({"ok": False, "error": "invalid_or_expired"}, status_code=403)
        rows = s.execute(_t("""SELECT id, doc_key, typ, text, stav, odpoved,
            to_char(created_at,'DD.MM.YYYY HH24:MI') AS kdy FROM tenant.doc_feedback
            WHERE auditor_access_id=:aid ORDER BY created_at DESC LIMIT 100"""), {"aid": row.id}).mappings().all()
        return {"ok": True, "feedback": [dict(r) for r in rows]}
    finally:
        s.close()


# ════════════════════════ ADMIN (certifikační firma — přehled zákazníků) ════════════════════════

@iso_router.get("/app/iso/admin/overview")
def iso_admin_overview(req: Request):
    """Multi-tenant přehled: zákazníci (tenanti) s ISMS + progres každého.
    Produktový pohled pro certifikační firmu. Marti 21.6.2026."""
    uid = _uid(req)
    if not _strict_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        rows = s.execute(_t("""
            SELECT t.id, t.tenant_name,
              (SELECT count(*) FROM tenant.iso_task k WHERE k.tenant_id=t.id) AS kroky,
              (SELECT count(*) FROM tenant.iso_task k WHERE k.tenant_id=t.id AND k.stav='hotovo') AS kroky_hot,
              (SELECT count(*) FROM tenant.iso_document d WHERE d.tenant_id=t.id) AS docs,
              (SELECT count(*) FROM tenant.iso_document d WHERE d.tenant_id=t.id AND d.stav='schvaleno') AS docs_ok,
              (SELECT count(*) FROM tenant.iso_signature g WHERE g.tenant_id=t.id) AS podpisy,
              (SELECT count(*) FROM tenant.iso_control c WHERE c.tenant_id=t.id) AS kontroly
            FROM public.tenants t WHERE t.status='active' AND COALESCE(t.tenant_type,'')<>'personal'
            ORDER BY t.id"""), {}).mappings().all()
        zak, bez = [], []
        for r in rows:
            d = dict(r)
            (zak if d["docs"] > 0 else bez).append(d)
        return {"ok": True, "zakaznici": zak, "bez_isms": bez}
    finally:
        s.close()


@iso_router.post("/app/iso/admin/init")
async def iso_admin_init(req: Request):
    """Inicializovat ISMS pro zákazníka (tenant) z univerzální šablony."""
    uid = _uid(req)
    if not _strict_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    s = _sess()
    try:
        tid = int(b["tenant"])
        _ensure_seeded(s, tid)
        _log(s, tid, _user_name(s, uid), "isms_init", None, _client_ip(req))
        return {"ok": True, "tenant": tid}
    finally:
        s.close()


# ════════════════════════ DOKUMENTACE (KB) + FEEDBACK PRO VŠECHNY ════════════════════════

_KB_DOCS = {
    "tutorial": ("docs/infrastruktura_tutorial.md", "Tutoriál infrastruktury (od nuly)"),
    "michal": ("docs/iso27001_plan_obnovy_michal.md", "Plán obnovy — pokyny pro Michala"),
    "harmonizace": ("docs/iso_tisax_harmonizace_2026.md", "Harmonizace ISO ↔ TISAX"),
    "dorazeni": ("docs/iso27001_dorazeni_2026.md", "ISO 27001 — plán dorážení"),
    "handoff": ("docs/iso27001_vedeni_certifikace.md", "ISO 27001 & TISAX — vedení certifikace (Mísa)"),
    "inventar": ("docs/iso27001_inventar_aktiv_dataflow.md", "Inventář aktiv + data-flow"),
    "dr": ("docs/iso27001_dr_plan_rto_rpo.md", "Plán obnovy DR (RTO/RPO)"),
    "cve": ("docs/iso27001_cve_sprava_zranitelnosti.md", "Správa zranitelností (CVE)"),
    "dodavatele": ("docs/iso27001_dodavatele_dpa.md", "Dodavatelé + DPA"),
    "vize": ("docs/iso_vize_pro_misu.md", "Vize ISO & TISAX — vedení certifikace a spolupráce"),
    "banka_pruvodce": ("docs/Banka_ucetnictvi_pruvodce_Petra.md", "🏦 Banka — průvodce účtováním a párováním plateb"),
    "skola": ("docs/Skola.md", "🗓️ Nerudovka — rozvrhová agenda (kompletní obraz pro řešení z CMS)"),
}
_KB_TYPY = {"otazka", "nerozumim", "spatne", "nesouhlas", "doplnit"}
_PORTAL = os.environ.get("STRATEGIE_PUBLIC_URL") or "https://strategie-ai.com"


def _email_for_user(s, uid):
    try:
        r = s.execute(_t("""SELECT contact_value FROM public.user_contacts
            WHERE user_id=:u AND contact_type='email' AND COALESCE(status,'active')<>'archived'
            ORDER BY is_primary DESC NULLS LAST LIMIT 1"""), {"u": uid}).first()
        return r.contact_value if r else None
    except Exception:
        return None


def _parent_emails(s):
    try:
        rows = s.execute(_t("""SELECT DISTINCT c.contact_value FROM public.users u
            JOIN public.user_contacts c ON c.user_id=u.id AND c.contact_type='email'
            WHERE u.is_marti_parent=true AND COALESCE(c.status,'active')<>'archived'""")).all()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def _users_emails(s, ids):
    """E-maily konkrétních uživatelů (podle id). Drží pořadí ids."""
    try:
        rows = s.execute(_t("""SELECT c.user_id, c.contact_value FROM public.user_contacts c
            WHERE c.user_id = ANY(:ids) AND c.contact_type='email'
            AND COALESCE(c.status,'active')<>'archived'"""), {"ids": list(ids)}).all()
        by = {}
        for uid, em in rows:
            if em and uid not in by:
                by[uid] = em
        return [by[i] for i in ids if i in by]
    except Exception:
        return []


def _notify_email(s, tenant_id, to_email, subject, body_html, cc=None):
    """E-mail jako pojistka (lidé žijí v e-mailu) — s proklikem do portálu. Worker pošle.
    cc = list e-mailů (uloží se jako JSON do email_outbox.cc)."""
    if not to_email:
        return
    import json as _j
    cc_val = _j.dumps([c for c in cc if c]) if cc else None
    try:
        s.execute(_t("""INSERT INTO public.email_outbox(persona_id, from_identity, tenant_id, to_email,
            cc, subject, body, purpose, status, created_at)
            VALUES(1,'persona',:t,:to,:cc,:subj,:body,'doc_feedback','pending',now())"""),
            {"t": tenant_id, "to": to_email, "cc": cc_val, "subj": subject[:990], "body": body_html})
        s.commit()
    except Exception:
        pass


@iso_router.get("/app/kb/list")
def kb_list(req: Request):
    """Seznam dostupných dokumentů (pro všechny přihlášené)."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    return {"ok": True, "docs": [{"key": k, "title": v[1]} for k, v in _KB_DOCS.items()]}


@iso_router.get("/app/kb/raw/{key}")
def kb_raw(key: str, req: Request):
    """Zdrojový markdown dokumentu (pro všechny přihlášené) — renderuje se v appce."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    item = _KB_DOCS.get(key)
    if not item:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    full = os.path.normpath(os.path.join(_REPO, item[0]))
    base = os.path.normpath(os.path.join(_REPO, "docs"))
    if not full.startswith(base) or not os.path.isfile(full):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    try:
        with open(full, encoding="utf-8", errors="replace") as f:
            md = f.read()
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return {"ok": True, "key": key, "title": item[1], "md": md}


@iso_router.post("/app/kb/feedback")
async def kb_feedback(req: Request):
    """Kdokoliv přihlášený: dotaz / nerozumím / špatně / nesouhlas / doplnit → do DB."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    b = await req.json()
    typ = (b.get("typ") or "otazka").strip()
    if typ not in _KB_TYPY:
        typ = "otazka"
    txt = (b.get("text") or "").strip()
    if not txt:
        return JSONResponse({"ok": False, "error": "prázdný text"}, status_code=400)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        s.execute(_t("""INSERT INTO tenant.doc_feedback(tenant_id,doc_key,sekce,typ,text,user_id,jmeno)
            VALUES(:t,:dk,:sek,:ty,:tx,:u,:j)"""),
            {"t": tid, "dk": (b.get("doc_key") or "")[:80], "sek": (b.get("sekce") or "")[:200],
             "ty": typ, "tx": txt[:4000], "u": uid, "j": _user_name(s, uid)})
        s.commit()
        jm = _user_name(s, uid)
        body = ("<p><b>%s</b> napsal(a) v portálu (%s) — dokument <b>%s</b>:</p><blockquote>%s</blockquote>"
                "<p>Otevřete a odpovězte v portálu: <a href='%s/iso'>%s/iso</a></p>") % (
            jm, typ, (b.get("doc_key") or "?"), txt[:1000], _PORTAL, _PORTAL)
        for em in _parent_emails(s):
            _notify_email(s, tid, em, "Nový dotaz v portálu (dokumentace) — %s" % jm, body)
        return {"ok": True}
    finally:
        s.close()


@iso_router.get("/app/kb/feedback")
def kb_feedback_list(req: Request):
    """Přehled feedbacku (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        rows = s.execute(_t("""SELECT id, doc_key, sekce, typ, text, jmeno, stav, odpoved, zdroj,
            to_char(created_at,'DD.MM.YYYY HH24:MI') AS kdy FROM tenant.doc_feedback
            ORDER BY (stav='nove') DESC, (zdroj='auditor') DESC, created_at DESC LIMIT 300""")).mappings().all()
        return {"ok": True, "feedback": [dict(r) for r in rows]}
    finally:
        s.close()


@iso_router.post("/app/kb/feedback/reply")
async def kb_feedback_reply(req: Request):
    """Odpovědět / vyřešit feedback (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    b = await req.json()
    odp = (b.get("odpoved") or "").strip()[:4000]
    s = _sess()
    try:
        fid = int(b["id"])
        row = s.execute(_t("""SELECT tenant_id, user_id, zdroj, auditor_access_id, doc_key, text
            FROM tenant.doc_feedback WHERE id=:id"""), {"id": fid}).first()
        s.execute(_t("""UPDATE tenant.doc_feedback SET odpoved=:o, odpovedel_id=:u,
            stav='vyrizeno', resolved_at=now() WHERE id=:id"""), {"o": odp, "u": uid, "id": fid})
        s.commit()
        # e-mail tazateli s proklikem do portálu (pojistka — lidé žijí v e-mailu)
        if row:
            if row.zdroj == "auditor" and row.auditor_access_id:
                ar = s.execute(_t("SELECT auditor_email FROM tenant.iso_auditor_access WHERE id=:i"),
                               {"i": row.auditor_access_id}).first()
                if ar and ar.auditor_email:
                    body = ("<p>Odpověděli jsme na vaši zprávu v auditorském portálu:</p>"
                            "<blockquote>%s</blockquote><p><b>Naše odpověď:</b> %s</p>"
                            "<p>Vše vidíte ve svém auditorském portálu (odkaz, který jste obdrželi).</p>") % (
                        (row.text or "")[:600], odp)
                    _notify_email(s, row.tenant_id, ar.auditor_email, "Odpověď v auditorském portálu", body)
            elif row.user_id:
                em = _email_for_user(s, row.user_id)
                if em:
                    link = "%s/dokument?key=%s" % (_PORTAL, row.doc_key or "tutorial")
                    body = ("<p>Odpověděli jsme na váš dotaz v portálu:</p><blockquote>%s</blockquote>"
                            "<p><b>Odpověď:</b> %s</p><p>Otevřít v portálu: <a href='%s'>%s</a></p>") % (
                        (row.text or "")[:600], odp, link, link)
                    _notify_email(s, row.tenant_id, em, "Odpověď na váš dotaz (portál STRATEGIE)", body)
        return {"ok": True}
    finally:
        s.close()
