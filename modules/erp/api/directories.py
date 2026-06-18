"""Systém adresářů pro dokumenty — Fáze A (Marti 18.6.2026, dle EC_OrgAdresare).

Konfigurace (tenant.dir_config) + resolver (typ entity + ID → kořen + podsložka)
+ storage adapter (EUROSOFT UNC přes MCP rw/ro namespace, cloud lokální FS)
+ ACL enforcement v adapteru + append-only audit (tenant.dir_access_log).

Závazné závěry konzultace Marti-AI v docs/adresare_dokumentu_v2.md.
"""
from __future__ import annotations

import base64
import json as _json
import os
import posixpath

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text as _t

dir_router = APIRouter(prefix="/api/v1/erp", tags=["directories"])

_TENANT = 2
_CLOUD_ROOT = os.environ.get("STRATEGIE_DOCS_ROOT", "").strip() or r"C:\StrategieDocs"
_SUBFOLDER_RULES = {"id", "cislo_zakazky", "poradove_cislo", "cislo_org", "user_id", "none"}


# ── pomocné: session + identita (lazy import z router, ať není cirkulární) ──
def _sess():
    from modules.erp.api.router import _att_session
    return _att_session()


def _uid(req):
    from modules.erp.api.router import _uid_from_token_or_cookie
    return _uid_from_token_or_cookie(req)


def _is_parent(uid):
    from modules.erp.api.router import is_marti_parent
    return bool(is_marti_parent(uid))


def _hr_can(s, uid):
    from modules.erp.api.router import _hr_can_manage
    return bool(_hr_can_manage(s, uid))


def _amb(req):
    from modules.erp.api.router import _is_amb_session
    return bool(_is_amb_session(req))


# ── ACL (vynucováno zde, ne jen v UI) ───────────────────────────────────────
def _acl_allow(s, uid, scope, *, entity_user_id=None, write=False, parent_override=False):
    """Vrať (ok: bool, reason: str). Pro HTTP aktéra (user). Persona (Marti-AI)
    má vlastní hranice v její tool vrstvě — viz docs."""
    parent = _is_parent(uid)
    if scope in ("business", "sablona"):
        # business R/W: rodič nebo aktivní ERP člen
        from modules.erp.api.router import _is_active_eurosoft_member
        return (parent or _is_active_eurosoft_member(uid)), ("" if (parent or _is_active_eurosoft_member(uid)) else "not_member")
    if scope == "hr":
        return (_hr_can(s, uid)), ("" if _hr_can(s, uid) else "hr_only")
    if scope == "self":
        ok = parent or (entity_user_id is not None and int(entity_user_id) == int(uid))
        return ok, ("" if ok else "self_only")
    if scope == "parent":
        return parent, ("" if parent else "parent_only")
    if scope == "confidential":
        ok = parent and (parent_override or not write)
        return ok, ("" if ok else "confidential_gate")
    return parent, ("" if parent else "denied")


def _audit(s, *, uid, scope, dir_config_id, entity_id, path, action, ok, err=""):
    """Append-only zápis do tenant.dir_access_log. business → jen write; jinak i read."""
    try:
        if scope == "business" and action in ("read", "list"):
            return  # běžný provoz business čtení nelogujeme (dle Marti-AI Q5)
        s.execute(_t(
            "INSERT INTO tenant.dir_access_log (tenant_id, actor_type, actor_id, dir_config_id, "
            "entity_id, resolved_path, action, acl_scope, ok, error_message) "
            "VALUES (:t,'user',:u,:c,:e,:p,:a,:sc,:ok,:err)"),
            {"t": _TENANT, "u": uid, "c": dir_config_id, "e": str(entity_id or ""),
             "p": path or "", "a": action, "sc": scope or "", "ok": ok, "err": (err or "")[:2000]})
        s.commit()
    except Exception:
        try:
            s.rollback()
        except Exception:
            pass


# ── Resolver ────────────────────────────────────────────────────────────────
def _load_config(s, sys_name, series=""):
    row = s.execute(_t(
        "SELECT id, sys_name, short_code, series, name, subfolder_rule, acl_scope, active "
        "FROM tenant.dir_config WHERE tenant_id=:t AND sys_name=:n AND series=:s"),
        {"t": _TENANT, "n": sys_name, "s": series or ""}).first()
    if not row:
        return None
    return {"id": row[0], "sys_name": row[1], "short_code": row[2] or "", "series": row[3] or "",
            "name": row[4] or "", "subfolder_rule": row[5], "acl_scope": row[6], "active": row[7]}


def _load_storages(s, cfg_id):
    rows = s.execute(_t(
        "SELECT role, backend, root_path FROM tenant.dir_config_storage "
        "WHERE dir_config_id=:c AND active=true ORDER BY CASE role WHEN 'primary' THEN 0 WHEN 'mirror' THEN 1 ELSE 2 END, id"),
        {"c": cfg_id}).fetchall()
    return [{"role": r[0], "backend": r[1], "root_path": r[2]} for r in rows]


def _apply_rules(s, cfg_id, ctx):
    """Výjimky jako data (dir_config_rule). Vrací dict override_field→override_value."""
    out = {}
    try:
        rows = s.execute(_t(
            "SELECT condition_type, condition_value, override_field, override_value "
            "FROM tenant.dir_config_rule WHERE dir_config_id=:c AND active=true ORDER BY priority"),
            {"c": cfg_id}).fetchall()
    except Exception:
        return out
    for ctype, cval, ofield, oval in rows:
        cv = str((ctx or {}).get(ctype, ""))
        if ctype.startswith("date_"):
            # date_before / date_from porovnání 'YYYY-MM-DD'
            d = str((ctx or {}).get("date", ""))
            if ctype == "date_before" and d and d < cval:
                out[ofield] = oval
            elif ctype == "date_from" and d and d >= cval:
                out[ofield] = oval
        elif cv and cv == str(cval):
            out[ofield] = oval
    return out


def _build_sub(rule, short_code, entity_id):
    eid = str(entity_id or "").strip()
    if rule == "none":
        return ""
    if rule == "id":
        return (short_code or "") + eid
    # cislo_zakazky | cislo_org | poradove_cislo | user_id → hodnota přímo
    if rule == "poradove_cislo":
        return (short_code or "") + eid
    return eid


def resolve(s, sys_name, entity_id, series="", ctx=None):
    """→ dict {ok, error?, config, storages[], sub, paths[]}."""
    cfg = _load_config(s, sys_name, series)
    if not cfg:
        return {"ok": False, "error": "config_not_found", "sys_name": sys_name}
    if not cfg["active"]:
        return {"ok": False, "error": "config_inactive"}
    storages = _load_storages(s, cfg["id"])
    overrides = _apply_rules(s, cfg["id"], ctx)
    rule = overrides.get("subfolder_rule", cfg["subfolder_rule"])
    sub = _build_sub(rule, cfg["short_code"], entity_id)
    paths = []
    for st in storages:
        root = overrides.get("root_path", st["root_path"]) if st["role"] == "primary" else st["root_path"]
        back = overrides.get("backend", st["backend"]) if st["role"] == "primary" else st["backend"]
        full = root.rstrip("/\\")
        if sub:
            full = full + "/" + sub
        paths.append({"role": st["role"], "backend": back, "root": root, "path": full})
    return {"ok": True, "config": cfg, "storages": storages, "sub": sub, "paths": paths}


# ── Storage adapter (list/read/write) nad backendy ──────────────────────────
def _mcp():
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    return get_eurosoft_mcp_client()


def _eu_list(rel_subpath):
    mcp = _mcp()
    if mcp is None:
        return {"ok": False, "error": "mcp_offline"}
    raw = mcp.call_tool_sync("eurosoft_eurosoft_file_list",
                             {"user_namespace": "rw", "subpath": rel_subpath}, conversation_id=None)
    r = _json.loads(raw) if isinstance(raw, str) else raw
    return r if isinstance(r, dict) else {"ok": True, "items": r}


def _eu_write(rel_path, content_b64):
    mcp = _mcp()
    if mcp is None:
        return {"ok": False, "error": "mcp_offline"}
    raw = mcp.call_tool_sync("eurosoft_eurosoft_file_write",
                             {"user_namespace": "rw", "path": rel_path,
                              "content": content_b64, "encoding": "base64", "mode": "overwrite"},
                             conversation_id=None)
    return _json.loads(raw) if isinstance(raw, str) else raw


def _eu_read(rel_path):
    mcp = _mcp()
    if mcp is None:
        return {"ok": False, "error": "mcp_offline"}
    raw = mcp.call_tool_sync("eurosoft_eurosoft_file_read",
                             {"user_namespace": "rw", "path": rel_path}, conversation_id=None)
    return _json.loads(raw) if isinstance(raw, str) else raw


def _cloud_read_file(root, sub, filename):
    d = _cloud_dir(root, sub)
    p = os.path.join(d, filename)
    if not os.path.isfile(p):
        return {"ok": False, "error": "not_found"}
    with open(p, "rb") as f:
        return {"ok": True, "content": base64.b64encode(f.read()).decode("ascii"), "encoding": "base64"}


def _cloud_dir(root, sub):
    base = os.path.join(_CLOUD_ROOT, root.strip("/\\").replace("/", os.sep))
    if sub:
        base = os.path.join(base, sub.replace("/", os.sep))
    return base


def _cloud_list(root, sub):
    d = _cloud_dir(root, sub)
    if not os.path.isdir(d):
        return {"ok": True, "items": []}
    items = []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        items.append({"name": n, "is_dir": os.path.isdir(p),
                      "size": (os.path.getsize(p) if os.path.isfile(p) else None)})
    return {"ok": True, "items": items}


def _cloud_write(root, sub, filename, content_b64):
    d = _cloud_dir(root, sub)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, filename), "wb") as f:
        f.write(base64.b64decode(content_b64))
    return {"ok": True}


# ── Endpointy ───────────────────────────────────────────────────────────────
@dir_router.get("/app/dir/resolve")
async def app_dir_resolve(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    sys_name = (req.query_params.get("sys_name") or "").strip()
    entity_id = (req.query_params.get("id") or "").strip()
    series = (req.query_params.get("series") or "").strip()
    if not sys_name:
        return JSONResponse({"ok": False, "error": "sys_name_required"}, status_code=400)
    cm, s = _sess()
    try:
        r = resolve(s, sys_name, entity_id, series)
        if not r["ok"]:
            return JSONResponse(r)
        scope = r["config"]["acl_scope"]
        ok, reason = _acl_allow(s, uid, scope)
        if not ok:
            _audit(s, uid=uid, scope=scope, dir_config_id=r["config"]["id"],
                   entity_id=entity_id, path="", action="read", ok=False, err="acl:" + reason)
            return JSONResponse({"ok": False, "error": "acl_denied", "reason": reason}, status_code=403)
        return JSONResponse(r)
    finally:
        cm.__exit__(None, None, None)


@dir_router.get("/app/dir/list")
async def app_dir_list(req: Request) -> JSONResponse:
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    sys_name = (req.query_params.get("sys_name") or "").strip()
    entity_id = (req.query_params.get("id") or "").strip()
    series = (req.query_params.get("series") or "").strip()
    cm, s = _sess()
    try:
        r = resolve(s, sys_name, entity_id, series)
        if not r["ok"]:
            return JSONResponse(r)
        scope = r["config"]["acl_scope"]
        ok, reason = _acl_allow(s, uid, scope)
        if not ok:
            _audit(s, uid=uid, scope=scope, dir_config_id=r["config"]["id"],
                   entity_id=entity_id, path="", action="list", ok=False, err="acl:" + reason)
            return JSONResponse({"ok": False, "error": "acl_denied", "reason": reason}, status_code=403)
        prim = next((p for p in r["paths"] if p["role"] == "primary"), (r["paths"][0] if r["paths"] else None))
        if not prim:
            return JSONResponse({"ok": False, "error": "no_storage"})
        if prim["backend"] == "eurosoft_unc":
            sub = posixpath.join(prim["root"].strip("/\\"), r["sub"]) if r["sub"] else prim["root"].strip("/\\")
            res = _eu_list(sub)
        else:
            res = _cloud_list(prim["root"], r["sub"])
        _audit(s, uid=uid, scope=scope, dir_config_id=r["config"]["id"],
               entity_id=entity_id, path=prim["path"], action="list",
               ok=bool(res.get("ok", True)), err=str(res.get("error", "")))
        return JSONResponse({"ok": True, "path": prim["path"], "backend": prim["backend"],
                             "result": res})
    finally:
        cm.__exit__(None, None, None)


def _write_to(storage, sub, filename, content_b64):
    """Zapíše do jednoho úložiště. Vrací (ok, detail)."""
    if storage["backend"] == "eurosoft_unc":
        root = storage["root"].strip("/\\")
        rel = posixpath.join(root, sub, filename) if sub else posixpath.join(root, filename)
        res = _eu_write(rel, content_b64)
    else:
        res = _cloud_write(storage["root"], sub, filename, content_b64)
    ok = (res is True) or (isinstance(res, dict) and bool(res.get("ok", False)))
    detail = (res.get("error", "") if isinstance(res, dict) else "")
    return ok, str(detail or "")


def store_document(s, sys_name, entity_id, filename, content_b64, *, uid,
                   parent_override=False, series="", ctx=None):
    """Resolve → ACL(write) → primár (povinný) → mirror(y) best-effort + audit.
    Marti-AI Q3: primár transakce; mirror best-effort + povinný audit při selhání;
    jen-mirror (bez primáru) → selhání = chyba."""
    r = resolve(s, sys_name, entity_id, series, ctx)
    if not r["ok"]:
        return r
    scope = r["config"]["acl_scope"]
    cfgid = r["config"]["id"]
    ok, reason = _acl_allow(s, uid, scope, write=True, parent_override=parent_override)
    if not ok:
        _audit(s, uid=uid, scope=scope, dir_config_id=cfgid, entity_id=entity_id,
               path="", action="write", ok=False, err="acl:" + reason)
        return {"ok": False, "error": "acl_denied", "reason": reason}
    paths = r["paths"]
    if not paths:
        return {"ok": False, "error": "no_storage"}
    sub = r["sub"]
    has_primary = any(p["role"] == "primary" for p in paths)
    results = []
    final_path = None
    for p in paths:
        good, detail = _write_to(p, sub, filename, content_b64)
        full = p["path"] + "/" + filename
        required = (p["role"] == "primary") or (not has_primary and p is paths[0])
        if required:
            _audit(s, uid=uid, scope=scope, dir_config_id=cfgid, entity_id=entity_id,
                   path=full, action="write", ok=good, err=detail)
            if not good:
                return {"ok": False, "error": "write_failed", "detail": detail, "path": full}
            final_path = full
        else:
            _audit(s, uid=uid, scope=scope, dir_config_id=cfgid, entity_id=entity_id,
                   path=full, action=("write" if good else "write_mirror_failed"),
                   ok=good, err=detail)
        results.append({"role": p["role"], "backend": p["backend"], "ok": good})
    return {"ok": True, "path": final_path or (paths[0]["path"] + "/" + filename),
            "filename": filename, "results": results}


@dir_router.post("/app/dir/write")
async def app_dir_write(req: Request) -> JSONResponse:
    """Upload souboru do adresáře entity. Body: sys_name, id, filename, content_b64, series?."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    sys_name = str((b or {}).get("sys_name") or "").strip()
    entity_id = str((b or {}).get("id") or "").strip()
    series = str((b or {}).get("series") or "").strip()
    filename = str((b or {}).get("filename") or "").strip()
    content_b64 = str((b or {}).get("content_b64") or "")
    if not (sys_name and filename and content_b64):
        return JSONResponse({"ok": False, "error": "missing_params"}, status_code=400)
    # bezpečný název souboru
    import re as _re
    filename = _re.sub(r"[\\/]+", "_", filename).lstrip(".") or "soubor"
    cm, s = _sess()
    try:
        res = store_document(s, sys_name, entity_id, filename, content_b64, uid=uid)
        code = 200 if res.get("ok") else (403 if res.get("error") == "acl_denied" else 200)
        return JSONResponse(res, status_code=code)
    finally:
        cm.__exit__(None, None, None)


@dir_router.post("/app/dir/store-doc")
async def app_dir_store_doc(req: Request) -> JSONResponse:
    """Vyrenderuje šablonu (doc_template) a uloží PDF přes resolver do adresáře entity.
    Body: template_id, entity_id (ref pro provider), sys_name (cíl), series?, parent_override?."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        b = await req.json()
    except Exception:
        b = {}
    try:
        tid = int((b or {}).get("template_id") or 0)
    except Exception:
        tid = 0
    ref = str((b or {}).get("entity_id") or "").strip()
    sys_name = str((b or {}).get("sys_name") or "").strip()
    series = str((b or {}).get("series") or "").strip()
    parent_override = bool((b or {}).get("parent_override") or False)
    if not (tid and sys_name):
        return JSONResponse({"ok": False, "error": "missing_params"}, status_code=400)
    import base64 as _b64, datetime as _dtm, re as _re, unicodedata as _ud
    from modules.erp.api import doc_templates as _dt
    from modules.erp.api.router import _doc_can
    cm, s = _sess()
    try:
        if not _doc_can(s, uid):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        tr = s.execute(_t("SELECT entity_kind, body_html, css, code, nazev FROM tenant.doc_template "
                          "WHERE id=:i AND tenant_id=2 AND is_current=true"), {"i": tid}).first()
        if not tr:
            return JSONResponse({"ok": False, "error": "template_not_found"})
        t_nazev = tr[4] or tr[3] or "dokument"
        prov = _dt.get_provider(tr[0])
        context = prov.resolve(ref, uid, True) if (prov and ref) else {}
        html = _dt.render({"body_html": tr[1], "css": tr[2]}, context)
        try:
            pdf = _dt.render_pdf(html)
        except RuntimeError as e:
            return JSONResponse({"ok": False, "error": "pdf_engine", "note": str(e)}, status_code=503)
        if not pdf:
            return JSONResponse({"ok": False, "error": "render_failed"}, status_code=500)
        person = (context.get("jmeno") if isinstance(context, dict) else None) or ("ref" + ref)
        ascii_name = _ud.normalize("NFKD", (t_nazev + "_" + str(person))).encode("ascii", "ignore").decode("ascii")
        safe = _re.sub(r"[^A-Za-z0-9]+", "_", ascii_name).strip("_") or "dokument"
        fname = safe + "_" + _dtm.date.today().isoformat() + ".pdf"
        content_b64 = _b64.b64encode(pdf).decode("ascii")
        res = store_document(s, sys_name, ref, fname, content_b64, uid=uid, parent_override=parent_override)
        res["bytes"] = len(pdf)
        code = 200 if res.get("ok") else (403 if res.get("error") == "acl_denied" else 200)
        return JSONResponse(res, status_code=code)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)
    finally:
        cm.__exit__(None, None, None)


@dir_router.get("/app/dir/read")
async def app_dir_read(req: Request) -> JSONResponse:
    """Stažení souboru z adresáře entity. ?sys_name=&id=&name=&series=."""
    uid = _uid(req)
    if not uid:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    sys_name = (req.query_params.get("sys_name") or "").strip()
    entity_id = (req.query_params.get("id") or "").strip()
    series = (req.query_params.get("series") or "").strip()
    name = (req.query_params.get("name") or "").strip()
    import re as _re
    name = _re.sub(r"[\\/]+", "_", name).lstrip(".")
    if not (sys_name and name):
        return JSONResponse({"ok": False, "error": "missing_params"}, status_code=400)
    cm, s = _sess()
    try:
        r = resolve(s, sys_name, entity_id, series)
        if not r["ok"]:
            return JSONResponse(r)
        scope = r["config"]["acl_scope"]
        ok, reason = _acl_allow(s, uid, scope)
        if not ok:
            _audit(s, uid=uid, scope=scope, dir_config_id=r["config"]["id"],
                   entity_id=entity_id, path=name, action="read", ok=False, err="acl:" + reason)
            return JSONResponse({"ok": False, "error": "acl_denied", "reason": reason}, status_code=403)
        prim = next((p for p in r["paths"] if p["role"] == "primary"), (r["paths"][0] if r["paths"] else None))
        if not prim:
            return JSONResponse({"ok": False, "error": "no_storage"})
        if prim["backend"] == "eurosoft_unc":
            rel = posixpath.join(prim["root"].strip("/\\"), r["sub"], name) if r["sub"] else posixpath.join(prim["root"].strip("/\\"), name)
            res = _eu_read(rel)
        else:
            res = _cloud_read_file(prim["root"], r["sub"], name)
        good = isinstance(res, dict) and res.get("ok")
        _audit(s, uid=uid, scope=scope, dir_config_id=r["config"]["id"], entity_id=entity_id,
               path=prim["path"] + "/" + name, action="read", ok=bool(good),
               err=str(res.get("error", "") if isinstance(res, dict) else ""))
        if not good:
            return JSONResponse({"ok": False, "error": (res.get("error") if isinstance(res, dict) else "read_failed")})
        return JSONResponse({"ok": True, "name": name, "content_b64": res.get("content", ""),
                             "encoding": res.get("encoding", "base64")})
    finally:
        cm.__exit__(None, None, None)


@dir_router.get("/app/dir/configs")
async def app_dir_configs(req: Request) -> JSONResponse:
    """Admin: seznam konfigurací adresářů (jen rodič)."""
    uid = _uid(req)
    if not uid or not _is_parent(uid):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    cm, s = _sess()
    try:
        rows = s.execute(_t(
            "SELECT c.id, c.sys_name, c.short_code, c.series, c.name, c.subfolder_rule, c.acl_scope, c.active, "
            "(SELECT count(*) FROM tenant.dir_config_storage st WHERE st.dir_config_id=c.id) "
            "FROM tenant.dir_config c WHERE c.tenant_id=:t ORDER BY c.sys_name, c.series"),
            {"t": _TENANT}).fetchall()
        out = [{"id": r[0], "sys_name": r[1], "short_code": r[2], "series": r[3], "name": r[4],
                "subfolder_rule": r[5], "acl_scope": r[6], "active": r[7], "storages": r[8]} for r in rows]
        return JSONResponse({"ok": True, "configs": out})
    finally:
        cm.__exit__(None, None, None)
