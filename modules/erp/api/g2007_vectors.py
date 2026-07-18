# -*- coding: utf-8 -*-
"""G2007 vektorizace — sémantické hledání nad g2007.znalost.

Vlastní vektorová vrstva (g2007.znalost_chunk + g2007.znalost_vector) oddělená od
obecného RAGu — G2007 = čistá nosná znalostní báze bez balastu. Reuse existující
Voyage pipeline (modules.rag.application.chunking + embeddings, voyage-3 / 1024-dim).

Endpointy (parent/cockpit):
  POST /api/v1/erp/app/g2007/index   {id?}                 — přeindexuj vše (nebo jednu)
  POST /api/v1/erp/app/g2007/search  {dotaz, oblast?, k?}  — sémantické hledání
Volá se i z upsertu (re-index po zápisu znalosti). Claude 17.7.2026.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

g2007_vec_router = APIRouter(prefix="/api/v1/erp", tags=["g2007-vectors"])

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def _guard(req):
    from modules.erp.api.router import _uid_from_token_or_cookie, _is_parent, _is_cockpit
    from core.database_data import get_data_session
    uid = _uid_from_token_or_cookie(req)
    s = get_data_session()
    try:
        ok = bool(uid and (_is_parent(s, uid) or _is_cockpit(s, uid)))
    finally:
        s.close()
    return uid, ok


def _ensure_schema(sg):
    """Best-effort. App role (strategie) nemá CREATE na g2007 — tabulky zakládá
    Marti-AI přes bridge, tady se jen ověří/no-op (permission error se spolkne)."""
    from sqlalchemy import text as T
    ddl = [
        ("CREATE TABLE IF NOT EXISTS g2007.znalost_chunk ("
         " id bigserial PRIMARY KEY,"
         " znalost_id bigint NOT NULL REFERENCES g2007.znalost(id) ON DELETE CASCADE,"
         " poradi int NOT NULL,"
         " text text NOT NULL,"
         " created_at timestamptz DEFAULT now())"),
        ("CREATE TABLE IF NOT EXISTS g2007.znalost_vector ("
         " chunk_id bigint PRIMARY KEY REFERENCES g2007.znalost_chunk(id) ON DELETE CASCADE,"
         " embedding vector(1024) NOT NULL,"
         " model varchar(50) DEFAULT 'voyage-3',"
         " created_at timestamptz DEFAULT now())"),
        "CREATE INDEX IF NOT EXISTS ix_g2007_chunk_znalost ON g2007.znalost_chunk(znalost_id)",
    ]
    for stmt in ddl:
        try:
            sg.execute(T(stmt))
            sg.commit()
        except Exception:
            sg.rollback()  # nemá práva / už existuje — pokračuj


def _vec_literal(v):
    return "[" + ",".join(repr(float(x)) for x in v) + "]"


def index_znalost(sg, znalost_id, obsah):
    """Přeindexuje jednu znalost: smaž staré chunky → chunkuj → embedni → ulož. Vrací # chunků."""
    from sqlalchemy import text as T
    from modules.rag.application.chunking import chunk_text
    from modules.rag.application.embeddings import embed_documents
    sg.execute(T("DELETE FROM g2007.znalost_chunk WHERE znalost_id=:z"), {"z": znalost_id})
    chunks = chunk_text(obsah or "", chunk_size_chars=CHUNK_SIZE, overlap_chars=CHUNK_OVERLAP)
    texts = [c["content"] for c in chunks]
    if not texts:
        sg.commit()
        return 0
    vecs = embed_documents(texts)
    for i, (c, v) in enumerate(zip(chunks, vecs)):
        cid = sg.execute(T("INSERT INTO g2007.znalost_chunk (znalost_id, poradi, text) "
                           "VALUES (:z,:p,:t) RETURNING id"),
                         {"z": znalost_id, "p": i, "t": c["content"]}).scalar()
        sg.execute(T("INSERT INTO g2007.znalost_vector (chunk_id, embedding, model) "
                     "VALUES (:c, CAST(:e AS vector), 'voyage-3')"),
                   {"c": cid, "e": _vec_literal(v)})
    sg.commit()
    return len(texts)


def reindex_by_kod(kod):
    """Pomůcka pro upsert endpoint — přeindexuje znalost podle kódu (best-effort)."""
    from sqlalchemy import text as T
    from core.database import get_session
    sg = get_session()
    try:
        _ensure_schema(sg)
        row = sg.execute(T("SELECT id, obsah FROM g2007.znalost WHERE kod=:k"), {"k": kod}).fetchone()
        if not row:
            return 0
        return index_znalost(sg, row[0], row[1])
    finally:
        sg.close()


def _index_work(only_id):
    from sqlalchemy import text as T
    from core.database import get_session
    sg = get_session()
    try:
        _ensure_schema(sg)
        if only_id:
            rows = sg.execute(T("SELECT id, obsah FROM g2007.znalost WHERE id=:i"),
                              {"i": only_id}).fetchall()
        else:
            rows = sg.execute(T("SELECT id, obsah FROM g2007.znalost WHERE stav='aktivni' "
                                "ORDER BY id")).fetchall()
        total, n = 0, 0
        for zid, obsah in rows:
            total += index_znalost(sg, zid, obsah)
            n += 1
        return {"ok": True, "znalosti": n, "chunku": total}
    except Exception as e:
        try:
            sg.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400])}
    finally:
        sg.close()


def _search_work(query, oblast, k):
    from sqlalchemy import text as T
    from core.database import get_session
    from modules.rag.application.embeddings import embed_query
    try:
        qlit = _vec_literal(embed_query(query))
    except Exception as e:
        return {"ok": False, "error": "embed_query %s: %s" % (type(e).__name__, str(e)[:300])}
    sg = get_session()
    try:
        # DISTINCT ON (z.id) → nejlepší chunk každé znalosti; vnější dotaz pak
        # seřadí tyto reprezentanty podle podobnosti a vezme top-k. Bez toho by
        # top-k vracelo více chunků jedné znalosti (balast).
        sql = ("SELECT kod, nadpis, oblast, "
               "ROUND((1 - dist)::numeric, 3) AS shoda, ukazka "
               "FROM ("
               "  SELECT DISTINCT ON (z.id) z.id AS zid, z.kod, z.nadpis, o.kod AS oblast, "
               "    (v.embedding <=> CAST(:qv AS vector)) AS dist, "
               "    LEFT(ch.text, 240) AS ukazka "
               "  FROM g2007.znalost_vector v "
               "  JOIN g2007.znalost_chunk ch ON ch.id=v.chunk_id "
               "  JOIN g2007.znalost z ON z.id=ch.znalost_id "
               "  JOIN g2007.znalost_oblast o ON o.id=z.oblast_id "
               "  WHERE z.stav='aktivni' " + ("AND o.kod=:ob " if oblast else "") +
               "  ORDER BY z.id, dist"
               ") sub "
               "ORDER BY dist LIMIT :k")
        params = {"qv": qlit, "k": int(k)}
        if oblast:
            params["ob"] = oblast
        rows = sg.execute(T(sql), params).fetchall()
        return {"ok": True, "dotaz": query, "oblast": oblast,
                "vysledky": [{"kod": r[0], "nadpis": r[1], "oblast": r[2],
                              "shoda": float(r[3]), "ukazka": r[4]} for r in rows]}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400])}
    finally:
        sg.close()


@g2007_vec_router.post("/app/g2007/index")
async def g2007_index(req: Request):
    """Přeindexuj g2007.znalost do vektorů. Body: {id?} — bez id = všechny aktivní."""
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        b = await req.json()
    except Exception:
        b = {}
    only_id = (b or {}).get("id")
    only_id = int(only_id) if only_id else None
    out = await run_in_threadpool(_index_work, only_id)
    return JSONResponse(out, status_code=200)


@g2007_vec_router.get("/app/ops/worktree-status")
async def ops_worktree_status(req: Request):
    """Drift detekce: `git status --porcelain` na běžící produkci (app repo).
    Ukáže lokální necommitnuté / untracked soubory = KÓD MIMO GIT. Parent/cockpit only.
    Claude C23, 18.7.2026 — nástroj proti 'produkce běží kód mimo git' (doc-go-120/121)."""
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        from modules.conversation.application.deployment_service import (
            _git_working_tree_clean as _wtc,
        )
        clean, detail = await run_in_threadpool(_wtc)
        return JSONResponse({"ok": True, "clean": bool(clean), "detail": detail or ""})
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])},
            status_code=200)


@g2007_vec_router.post("/app/g2007/search")
async def g2007_search(req: Request):
    """Sémantické hledání nad G2007. Body: {dotaz, oblast?, k?}."""
    uid, ok = _guard(req)
    if not ok:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        b = await req.json()
    except Exception:
        b = {}
    query = str((b or {}).get("dotaz") or (b or {}).get("q") or "").strip()
    oblast = str((b or {}).get("oblast") or "").strip().lower() or None
    try:
        k = max(1, min(20, int((b or {}).get("k") or 6)))
    except Exception:
        k = 6
    if not query:
        return JSONResponse({"ok": False, "error": "chybí dotaz"}, status_code=200)
    out = await run_in_threadpool(_search_work, query, oblast, k)
    return JSONResponse(out, status_code=200)
