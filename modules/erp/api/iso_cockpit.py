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
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import text as _t

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
    (9, "Technika", "Restore drill záloh", "Otestovat obnovu zálohy, zaznamenat RTO/RPO → DOC-11", "Claude+Marti", "DOC-11", False),
    (10, "Technika", "CVE sken závislostí", "Spustit pip-audit, vyřešit nálezy dle SLA", "Claude+Marti", None, False),
    (11, "Dodavatelé", "DPA s dodavateli", "Uzavřít zpracovatelské smlouvy se sub-processory → DOC-12", "Kristý (ISMS)", "DOC-12", False),
    (12, "Fyzická", "Attestace fyzické bezpečnosti", "Doložit od EUROSOFT / DC ČMIS", "Marti", None, False),
]


# ── pomocné (lazy import z router.py, ať není cirkulární) ──
def _sess():
    from core.database_data import get_data_session
    return get_data_session()


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _is_parent(uid):
    from modules.erp.api.router import is_marti_parent
    return bool(uid) and is_marti_parent(uid)


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
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        _ensure_seeded(s, tid)
        tasks = s.execute(_t("""SELECT id,poradi,faze,nazev,popis,vlastnik,stav,doc_kod,vyzaduje_podpis,
            to_char(done_at,'DD.MM.YYYY HH24:MI') AS done_kdy
            FROM tenant.iso_task WHERE tenant_id=:t ORDER BY poradi"""), {"t": tid}).mappings().all()
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
                "tasks": [dict(x) for x in tasks], "docs": docs,
                "soa": {"apl_ano": cs["apl_ano"], "apl_ne": cs["apl_ne"], "total": cs["total"], "stav": doc06},
                "tisax": {"appl": tx["appl"], "hotovo": tx["hot"], "moduly": tx["moduly"], "is_coverage": is_cov, "verze": "VDA ISA 6.0.3"},
                "progress": {"hotovo": done, "celkem": len(tasks)}}
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
    """Stáhnout/zobrazit obsah dokumentu (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
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
    fn = os.path.basename(full)
    return FileResponse(full, filename=fn)


def _controls_payload(s, tenant_id):
    rows = s.execute(_t("""SELECT id,kod,oblast,nazev,apl,stav,zduvodneni,dukaz
        FROM tenant.iso_control WHERE tenant_id=:t ORDER BY poradi"""), {"t": tenant_id}).mappings().all()
    return [dict(r) for r in rows]


@iso_router.get("/app/iso/controls")
def iso_controls(req: Request):
    """SoA — 93 kontrol Annex A pro tenant (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        _ensure_seeded(s, tid)
        return {"ok": True, "controls": _controls_payload(s, tid)}
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
    """TISAX (VDA ISA 6.0.3) položky pro tenant (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        _ensure_seeded(s, tid)
        return {"ok": True, "verze": "VDA ISA 6.0.3", "tisax": _tisax_payload(s, tid)}
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
    return FileResponse(full, filename=os.path.basename(full))


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
    """Nahrané dokumenty (evidence) ze STRATEGIE pro tenant (parent)."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
        return {"ok": True, "evidence": _evidence_payload(s, tid)}
    finally:
        s.close()


@iso_router.get("/app/iso/evidence-doc/{doc_id}")
def iso_evidence_doc(doc_id: int, req: Request):
    """Otevřít nahraný dokument (parent), jen z vlastního tenantu."""
    uid = _uid(req)
    if not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    s = _sess()
    try:
        tid = _tenant(req, uid, s)
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


# ════════════════════════ ADMIN (certifikační firma — přehled zákazníků) ════════════════════════

@iso_router.get("/app/iso/admin/overview")
def iso_admin_overview(req: Request):
    """Multi-tenant přehled: zákazníci (tenanti) s ISMS + progres každého.
    Produktový pohled pro certifikační firmu. Marti 21.6.2026."""
    uid = _uid(req)
    if not _is_parent(uid):
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
            FROM public.tenants t WHERE t.status='active' ORDER BY t.id"""), {}).mappings().all()
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
    if not _is_parent(uid):
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
