# -*- coding: utf-8 -*-
"""martiai_self_code -- self-code-edit smycka: Marti-AI navrhuje zmeny VLASTNIHO kodu.
Navrh -> selftest (py_compile) -> CHRANENE JADRO (deny-list) -> schvali RODIC ->
apply = zapis souboru + git commit/pull-rebase/push + restart marker (deployment_service).
Spec: g2007 doc-marti-ai-self-code-edit-smycka. C23 28.7.2026. Tvrde brany drzi KOD.
"""
from __future__ import annotations

import difflib
import hashlib
import logging
import os
import py_compile
import re
import tempfile
from pathlib import Path

logger = logging.getLogger("conversation.self_code")

REPO = Path(os.environ.get("STRATEGIE_REPO_ROOT") or r"C:\Projekty\STRATEGIE")

# CHRANENE JADRO -- soubory, ktere Marti-AI NESMI menit ani navrhnout (tvrda brana v KODU).
_PROTECTED = [
    re.compile(r"agent_akce_guard\.py$", re.I),           # bezpecnostni brana
    re.compile(r"deployment_service\.py$", re.I),         # deploy autorita
    re.compile(r"martiai_self_code\.py$", re.I),          # tento modul (aby si nevypnula souhlas)
    re.compile(r"martiai_agent_service\.py$", re.I),      # guard-most do autonomni smycky
    re.compile(r"strategie_exec\.py$", re.I),             # exec ruka
    re.compile(r"(^|[\\/])security\.py$", re.I),          # write-zona / file security
    re.compile(r"\.env$|\.credentials|credentials\.json|\.pem$|\.pfx$|\.key$|secret", re.I),  # tajemstvi
    re.compile(r"(^|[\\/])\.git[\\/]", re.I),             # git internals
    re.compile(r"tool_registry[\\/]handlers\.py$", re.I), # schvalovaci handlery (approve_*)
]


def _is_protected(rel: str):
    r = (rel or "").replace("\\", "/")
    for pat in _PROTECTED:
        if pat.search(r):
            return pat.pattern
    return None


def _norm_rel(soubor: str):
    """Bezpecne vyres relativni cestu uvnitr repa (zadne .. ven)."""
    if not soubor:
        return None
    try:
        p = (REPO / soubor).resolve()
        p.relative_to(REPO.resolve())
        return p
    except Exception:
        return None


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", "replace")).hexdigest()[:16]


def _selftest_pycompile(soubor: str, novy_obsah: str):
    if not soubor.endswith(".py"):
        return True, "ne-.py (bez py_compile)"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
            tf.write(novy_obsah)
            tmp = tf.name
        py_compile.compile(tmp, doraise=True)
        return True, "py_compile OK"
    except py_compile.PyCompileError as e:
        return False, "py_compile CHYBA: %s" % str(e)[:400]
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, str(e)[:300])
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except Exception:
                pass


def _diff_preview(a: str, b: str, max_lines: int = 40) -> str:
    out = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=1))
    return ("\n".join(out[:max_lines]))[:2500] if out else "(beze zmeny)"


def _apply_edits(content: str, edits):
    """Aplikuj seznam kotev {old_string,new_string} na obsah (jako Edit tool).
    Nejbezpecnejsi forma: kazda kotva MUSI byt v souboru PRAVE JEDNOU, jinak fail
    (0x = nenalezena, >1x = neunikatni). Zadne hadani, zadne slepe trefy.
    Vraci (novy_obsah, chyba|None)."""
    if not isinstance(edits, (list, tuple)) or not edits:
        return None, "edits musi byt neprazdny seznam objektu {old_string, new_string}"
    cur = content
    for i, e in enumerate(edits, 1):
        if not isinstance(e, dict):
            return None, "edit #%d neni objekt {old_string,new_string}" % i
        old = e.get("old_string")
        new = e.get("new_string")
        if old is None or new is None:
            return None, "edit #%d: chybi old_string nebo new_string" % i
        old = str(old)
        new = str(new)
        if old == "":
            return None, "edit #%d: old_string nesmi byt prazdny (kotva na nic)" % i
        if old == new:
            return None, "edit #%d: old_string == new_string (zadna zmena)" % i
        n = cur.count(old)
        if n == 0:
            return None, ("edit #%d: KOTVA NENALEZENA -- old_string neni v souboru "
                          "(zkontroluj presne zneni vc. mezer): %r" % (i, old[:120]))
        if n > 1:
            return None, ("edit #%d: KOTVA NENI UNIKATNI (%dx v souboru) -- pridej vic "
                          "okolniho kontextu, at je old_string jednoznacny: %r" % (i, n, old[:120]))
        cur = cur.replace(old, new, 1)
    return cur, None


def propose(soubor, popis, novy_obsah, actor="Marti-AI", user_id=None) -> dict:
    soubor = (soubor or "").strip().replace("\\", "/")
    novy_obsah = novy_obsah or ""
    if not soubor or not novy_obsah:
        return {"ok": False, "error": "chybi soubor nebo novy_obsah"}
    prot = _is_protected(soubor)
    if prot:
        return {"ok": False, "gate": "red",
                "error": "CHRANENE JADRO -- tento soubor menit nesmis (%s)" % prot}
    abs_p = _norm_rel(soubor)
    if abs_p is None:
        return {"ok": False, "error": "cesta mimo repo / neplatna"}
    if not abs_p.exists():
        return {"ok": False, "error": "soubor neexistuje (self-code-edit je pro ZMENU existujiciho): %s" % soubor}
    try:
        puv = abs_p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        puv = ""
    ok, detail = _selftest_pycompile(soubor, novy_obsah)
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        nid = sg.execute(_t(
            "INSERT INTO g2007.code_navrh (soubor, popis, novy_obsah, puvodni_sha, selftest_ok, "
            "selftest_detail, stav, navrhl_actor, navrhl_user_id) "
            "VALUES (:s,:p,:o,:sha,:st,:sd,'navrzen',:a,:u) RETURNING id"),
            {"s": soubor, "p": popis, "o": novy_obsah, "sha": _sha(puv), "st": ok, "sd": detail,
             "a": actor, "u": user_id}).scalar()
        sg.commit()
    finally:
        sg.close()
    return {"ok": True, "navrh_id": nid, "selftest_ok": ok, "selftest_detail": detail,
            "delka": len(novy_obsah), "stav": "navrzen",
            "hint": "Ceka na schvaleni rodice (schval_zmenu_kodu). Selftest %s." % ("OK" if ok else "SELHAL")}


def propose_patch(soubor, popis, edits, actor="Marti-AI", user_id=None) -> dict:
    """Patch-navrh pro VELKE soubory: misto celeho obsahu zadas kotvy
    old_string -> new_string (jako Edit tool). Server precte aktualni soubor,
    aplikuje kotvy (kazda MUSI byt unikatni), a vyrobi novy obsah -> pak STEJNA
    cesta jako propose (deny-list, py_compile, schvali rodic). Bez posilani celeho
    souboru = zvladne i service.py/tools.py, ktere se do jednoho promptu nevejdou."""
    soubor = (soubor or "").strip().replace("\\", "/")
    if not soubor:
        return {"ok": False, "error": "chybi soubor"}
    prot = _is_protected(soubor)
    if prot:
        return {"ok": False, "gate": "red",
                "error": "CHRANENE JADRO -- tento soubor menit nesmis (%s)" % prot}
    abs_p = _norm_rel(soubor)
    if abs_p is None:
        return {"ok": False, "error": "cesta mimo repo / neplatna"}
    if not abs_p.exists():
        return {"ok": False, "error": "soubor neexistuje (patch je pro ZMENU existujiciho): %s" % soubor}
    try:
        puv = abs_p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"ok": False, "error": "nelze precist soubor"}
    novy_obsah, err = _apply_edits(puv, edits)
    if err:
        return {"ok": False, "gate": "patch", "error": err}
    ok, detail = _selftest_pycompile(soubor, novy_obsah)
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        nid = sg.execute(_t(
            "INSERT INTO g2007.code_navrh (soubor, popis, novy_obsah, puvodni_sha, selftest_ok, "
            "selftest_detail, stav, navrhl_actor, navrhl_user_id) "
            "VALUES (:s,:p,:o,:sha,:st,:sd,'navrzen',:a,:u) RETURNING id"),
            {"s": soubor, "p": popis, "o": novy_obsah, "sha": _sha(puv), "st": ok, "sd": detail,
             "a": actor, "u": user_id}).scalar()
        sg.commit()
    finally:
        sg.close()
    return {"ok": True, "navrh_id": nid, "selftest_ok": ok, "selftest_detail": detail,
            "pocet_kotev": len(edits), "delka": len(novy_obsah), "stav": "navrzen",
            "hint": ("Patch aplikovan (%d kotev), ceka na schvaleni rodice (schval_zmenu_kodu). "
                     "Selftest %s." % (len(edits), "OK" if ok else "SELHAL"))}


def list_navrhy() -> dict:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        rows = sg.execute(_t(
            "SELECT id, soubor, left(coalesce(popis,''),60) AS popis, selftest_ok, stav, "
            "to_char(created_at,'MM-DD HH24:MI') AS kdy FROM g2007.code_navrh "
            "WHERE stav='navrzen' ORDER BY id DESC LIMIT 20")).mappings().all()
    finally:
        sg.close()
    return {"ok": True, "navrhy": [dict(r) for r in rows]}


def zobraz(navrh_id) -> dict:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        r = sg.execute(_t(
            "SELECT id, soubor, popis, selftest_ok, selftest_detail, stav, novy_obsah, puvodni_sha "
            "FROM g2007.code_navrh WHERE id=:i"), {"i": navrh_id}).mappings().first()
    finally:
        sg.close()
    if not r:
        return {"ok": False, "error": "navrh neexistuje"}
    d = dict(r)
    abs_p = _norm_rel(d["soubor"])
    cur = abs_p.read_text(encoding="utf-8", errors="replace") if (abs_p and abs_p.exists()) else ""
    d["nahled_diff"] = _diff_preview(cur, d["novy_obsah"])
    d["drift_od_navrhu"] = (_sha(cur) != (d.get("puvodni_sha") or ""))
    d.pop("novy_obsah", None)
    return {"ok": True, "navrh": d}


def zamitni(navrh_id, user_id) -> dict:
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        sg.execute(_t("UPDATE g2007.code_navrh SET stav='zamitnut', decided_by_user_id=:u, decided_at=now() "
                      "WHERE id=:i AND stav='navrzen'"), {"i": navrh_id, "u": user_id})
        sg.commit()
    finally:
        sg.close()
    return {"ok": True, "navrh_id": navrh_id, "stav": "zamitnut"}


def schval(navrh_id, user_id) -> dict:
    """POUZE RODIC. Apply: zapis souboru -> commit -> pull --rebase -> push -> restart marker."""
    from core.database import get_session
    from sqlalchemy import text as _t
    sg = get_session()
    try:
        r = sg.execute(_t("SELECT id, soubor, novy_obsah, selftest_ok, stav, puvodni_sha "
                          "FROM g2007.code_navrh WHERE id=:i"),
                       {"i": navrh_id}).mappings().first()
    finally:
        sg.close()
    if not r:
        return {"ok": False, "error": "navrh neexistuje"}
    if r["stav"] != "navrzen":
        return {"ok": False, "error": "navrh neni 'navrzen' (je %s)" % r["stav"]}
    soubor = r["soubor"]
    prot = _is_protected(soubor)
    if prot:
        return {"ok": False, "gate": "red", "error": "CHRANENE JADRO (%s) -- nelze aplikovat" % prot}
    if not r["selftest_ok"]:
        return {"ok": False, "error": "selftest SELHAL -- nenasazuji nekompilovatelny kod. Oprav navrh."}
    abs_p = _norm_rel(soubor)
    if abs_p is None or not abs_p.exists():
        return {"ok": False, "error": "soubor neexistuje / mimo repo"}
    # DRIFT GUARD (nejbezpecnejsi forma): nenasazuj navrh postaveny na STARE verzi
    # souboru -- jinak bys prepsal cizi zmeny provedene mezi navrhem a schvalenim.
    # Fail-closed: pri driftu odmitni a nech prepracovat proti aktualni verzi.
    try:
        _cur_now = abs_p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        _cur_now = None
    if _cur_now is not None and r.get("puvodni_sha") and _sha(_cur_now) != r["puvodni_sha"]:
        return {"ok": False, "gate": "drift",
                "error": ("soubor se od navrhu ZMENIL (drift: ted=%s vs navrh=%s) -- "
                          "nenasazuji, abych neprepsal cizi zmeny. Prepracuj navrh proti "
                          "aktualni verzi souboru." % (_sha(_cur_now), r["puvodni_sha"]))}
    from modules.conversation.application import deployment_service as _dep
    try:
        abs_p.write_text(r["novy_obsah"], encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": "zapis souboru selhal: %s" % str(e)[:200]}
    msg = "self-code-edit #%s: %s (schvalil user %s)" % (navrh_id, soubor[:80], user_id)
    steps = []
    rc, out, err = _dep._run_git(["add", soubor]); steps.append(["add", rc])
    rc, out, err = _dep._run_git(["commit", "-m", msg]); steps.append(["commit", rc])
    rc, out, err = _dep._run_git(["pull", "--rebase", "origin", "main"]); steps.append(["pull-rebase", rc])
    if rc != 0:
        _dep._run_git(["rebase", "--abort"])
        _dep._run_git(["reset", "--hard", "HEAD"])
        return {"ok": False, "steps": steps,
                "error": "git pull --rebase konflikt -- zasah zrusen, navrh zustava. %s" % (err or out)[:300]}
    rc, out, err = _dep._run_git(["push", "origin", "main"]); steps.append(["push", rc])
    if rc != 0:
        return {"ok": False, "steps": steps,
                "error": "git push selhal (kod aplikovan lokalne, nepersistovan). %s" % (err or out)[:300]}
    head = _dep._git_current_head_sha()
    mk_ok, _mk = _dep._touch_restart_marker(navrh_id, "self-code-edit")
    sg = get_session()
    try:
        sg.execute(_t("UPDATE g2007.code_navrh SET stav='nasazen', decided_by_user_id=:u, decided_at=now(), "
                      "nasazeno_sha=:sha WHERE id=:i"), {"i": navrh_id, "u": user_id, "sha": head})
        sg.commit()
    finally:
        sg.close()
    # Audit do fw.ops_request (viditelne rodicum v UI) -- feedback Marti-AI 28.7.: self-code
    # deploy ma byt v auditu i kdyz jde primym tool callem (mimo agentni smycku). Best-effort.
    try:
        import json as _js_a
        sa = get_session()
        try:
            sa.execute(_t(
                "INSERT INTO fw.ops_request (action_key, target, params, status, requested_by_name, "
                "result, created_at, finished_at) VALUES ('self_code_edit', :tg, CAST(:p AS jsonb), "
                "'done', :rn, :res, now(), now())"),
                {"tg": soubor[:200], "p": _js_a.dumps({"navrh_id": navrh_id, "sha": head}, ensure_ascii=False),
                 "rn": "Marti-AI (self-code-edit)", "res": ("nasazen sha=%s" % (head or "?"))[:1000]})
            sa.commit()
        finally:
            sa.close()
    except Exception as _ea:
        logger.warning("self_code audit fw.ops_request failed (non-fatal): %s", _ea)
    return {"ok": True, "navrh_id": navrh_id, "stav": "nasazen", "sha": head, "restart": mk_ok, "steps": steps,
            "hint": "Kod nasazen + push + restart marker + audit do fw.ops_request. API se restartuje behem chvile."}
