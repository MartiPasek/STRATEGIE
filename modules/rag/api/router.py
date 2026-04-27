"""
RAG HTTP API.

Endpointy:
    POST  /api/v1/documents/upload         multipart form (file + optional project_id)
    GET   /api/v1/documents                list dokumentu current tenant+project
    DELETE /api/v1/documents/{id}          smazat (cascade chunky + vektory + FS)
    POST  /api/v1/documents/search         {query, k?, project_id?} -> chunky
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.rag.application import service as rag_service

logger = get_logger("rag.api")

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Max velikost uploadu (MB). FastAPI / starlette drzi v pameti, takze
# 50 MB je rozumne ceiling pro MVP (PDF 500 stran).
MAX_UPLOAD_MB = 50


def _get_user_context(req: Request) -> tuple[int, int]:
    """Vraci (user_id, tenant_id) pro current session. Raises 401 pri chybeni."""
    uid_str = req.cookies.get("user_id")
    if not uid_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(uid_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Účet není aktivní.")
        if not user.last_active_tenant_id:
            raise HTTPException(status_code=400, detail="Nemáš aktivní tenant.")
        return user_id, user.last_active_tenant_id
    finally:
        session.close()


# ── UPLOAD ────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_endpoint(
    req: Request,
    file: UploadFile = File(...),
    project_id: int | None = Form(default=None),
    display_name: str | None = Form(default=None),
    relative_path: str | None = Form(default=None),
) -> dict:
    """
    Upload souboru (multipart/form-data). Pripoji se do current tenantu,
    optional project_id pro project-scoped dokument. Processing je sync v MVP.

    REST-Bulk: relative_path -- pro bulk upload slozky se zachovanim
    podadresarove struktury (napr. "TISAX/audit_2026/cert.pdf"). Backend
    ho prepne do display_name (pokud display_name neni explicit dany).
    """
    user_id, tenant_id = _get_user_context(req)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Chybí filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Prázdný soubor.")
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Soubor je větší než {MAX_UPLOAD_MB} MB.",
        )

    # REST-Bulk: pokud klient poslal relative_path (z folder upload)
    # a nedal explicit display_name, pouzijeme path jako display_name
    # pro zachovani slozkove struktury v UI listu.
    if relative_path and not display_name:
        # Sanitize -- jen alphanum, slash, dot, dash, underscore, mezery
        import re
        safe = re.sub(r"[^\w\s./\-]", "_", relative_path.strip().lstrip("/"))
        if safe and len(safe) <= 500:
            display_name = safe

    from modules.audit.application.service import log_event
    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    try:
        document_id = rag_service.upload_document(
            file_bytes=content,
            filename=file.filename,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            display_name=display_name,
        )
    except RuntimeError as e:
        logger.error(f"RAG upload failed (config): {e}")
        log_event(action="document_uploaded", status="error",
                  user_id=user_id, tenant_id=tenant_id,
                  error=str(e)[:200], ip_address=ip, user_agent=ua,
                  extra_metadata={"filename": file.filename, "size": len(content)})
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"RAG upload failed: {e}")
        log_event(action="document_uploaded", status="error",
                  user_id=user_id, tenant_id=tenant_id,
                  error=str(e)[:200], ip_address=ip, user_agent=ua,
                  extra_metadata={"filename": file.filename, "size": len(content)})
        raise HTTPException(status_code=500, detail=f"Upload selhal: {e}")

    log_event(action="document_uploaded", status="success",
              user_id=user_id, tenant_id=tenant_id, entity_id=document_id,
              ip_address=ip, user_agent=ua,
              extra_metadata={
                  "filename": file.filename, "size": len(content),
                  "project_id": project_id,
              })

    return {"document_id": document_id, "status": "uploaded"}


# ── LIST ──────────────────────────────────────────────────────────────────

@router.get("")
def list_endpoint(req: Request, project_id: int | None = None) -> dict:
    """
    Vypis dokumentu v current tenant/project scope.
    Query param project_id=N -> vraci project docs + tenant-global.
    Bez project_id -> vraci jen tenant-global (project_id IS NULL).
    """
    user_id, tenant_id = _get_user_context(req)
    docs = rag_service.list_documents(tenant_id=tenant_id, project_id=project_id)
    return {"documents": docs, "count": len(docs)}


# ── INBOX COUNT (UI badge na 📁 ikone v chat input) ───────────────────────

@router.get("/inbox/count")
def inbox_count_endpoint(req: Request) -> dict:
    """
    Vraci pocet dokumentu v osobnim inboxu (per user + current tenant).
    Inbox = documents s project_id IS NULL pro current user (uploadnute,
    cekaji na zarazeni do projektu pres Marti-AI document kustod).

    UI ho vola pri loaded + 30s polling -> badge na 📁 ikone v chat input.
    """
    from modules.rag.application import triage_service
    user_id, tenant_id = _get_user_context(req)
    count = triage_service.count_inbox_documents(
        user_id=user_id, tenant_id=tenant_id,
    )
    return {"count": count}


# ── SELECTION (per-user multi-select pro batch akce s Marti-AI) ───────────

class _SelectionToggleBody(BaseModel):
    document_ids: list[int]


@router.get("/selection")
def selection_get_endpoint(req: Request) -> dict:
    """
    Vrati seznam dokumentu oznacenych aktualnim userem v aktualnim tenantu.
    UI to vola pri otevreni Files modalu pro restoring multi-select state.
    """
    from modules.rag.application import selection_service
    user_id, tenant_id = _get_user_context(req)
    items = selection_service.list_selection(user_id=user_id, tenant_id=tenant_id)
    return {"items": items, "count": len(items)}


@router.post("/selection/toggle")
def selection_toggle_endpoint(body: _SelectionToggleBody, req: Request) -> dict:
    """
    Toggle multi-select. Pro kazde document_id v body: pokud je v selection,
    odebere; pokud neni, prida (po overeni ze patri usera tenantu).

    Vraci sumar: {added, removed, rejected_tenant, rejected_missing,
                  total_selected_in_tenant} -- UI muze update progress.
    """
    from modules.rag.application import selection_service
    user_id, tenant_id = _get_user_context(req)
    if not body.document_ids:
        raise HTTPException(status_code=400, detail="Chybí document_ids.")
    if len(body.document_ids) > 200:
        raise HTTPException(status_code=413, detail="Max 200 IDs per request.")
    result = selection_service.toggle_documents(
        user_id=user_id, document_ids=body.document_ids, tenant_id=tenant_id,
    )
    result["total_selected_in_tenant"] = selection_service.count_selection(
        user_id=user_id, tenant_id=tenant_id,
    )
    return result


@router.delete("/selection")
def selection_clear_endpoint(req: Request) -> dict:
    """Clear all selection v aktualnim tenantu (UI 'Clear all' tlacitko)."""
    from modules.rag.application import selection_service
    user_id, tenant_id = _get_user_context(req)
    deleted = selection_service.clear_selection(user_id=user_id, tenant_id=tenant_id)
    return {"deleted": deleted}


# ── PREVIEW (inline content pro UI modal) ─────────────────────────────────

@router.get("/{document_id}/preview")
def preview_endpoint(document_id: int, req: Request):
    """
    Preview obsahu dokumentu pro UI modal. Podle file_type:
      - PDF/image/audio -> FileResponse inline (browser nativni preview)
      - plain text (txt/md/csv/log/json/xml/yaml/sql/ini/html/htm)
        -> FileResponse inline jako text/plain (browser zobrazi)
      - office (doc/docx/xls/xlsx/ppt/pptx/odt/...) -> JSON kind='text'
        s reconstrucked obsahem z document_chunks (markitdown extracted)
      - storage_only (zip/rar/exe/...) -> JSON kind='unsupported'
      - processing_error -> JSON kind='error'

    Read-only, tenant scope check. Klient (UI) podle 'kind' / Content-Type
    rozhodne jakou render strategy pouzit.
    """
    from fastapi.responses import FileResponse, JSONResponse
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import Document, DocumentChunk
    import os

    user_id, tenant_id = _get_user_context(req)

    # MIME mapping pro inline preview (browser-native render)
    INLINE_MIME = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif", "bmp": "image/bmp",
        "webp": "image/webp", "tiff": "image/tiff", "tif": "image/tiff",
        "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
        "ogg": "audio/ogg", "flac": "audio/flac", "aac": "audio/aac",
        "mp4": "video/mp4",
    }
    PLAIN_TEXT_EXTS = {
        "txt", "md", "csv", "log", "json", "xml", "yaml", "yml",
        "sql", "ini", "html", "htm", "rtf",
    }
    OFFICE_LIKE_EXTS = {
        "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "odt", "ods", "odp", "epub", "msg", "eml",
    }

    ds = get_data_session()
    try:
        doc = ds.query(Document).filter_by(id=document_id).first()
        if not doc or doc.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Dokument neexistuje.")
        if not doc.storage_path or not os.path.exists(doc.storage_path):
            raise HTTPException(status_code=410, detail="Soubor uz nemam na disku.")

        ext = (doc.file_type or "").lower().lstrip(".")
        is_storage_only = bool(doc.storage_only)

        # Storage_only (ZIP/RAR/EXE/...) -- preview neni dostupny
        if is_storage_only:
            return JSONResponse({
                "kind": "unsupported",
                "file_type": ext,
                "name": doc.name,
                "note": "Tento soubor je v úschově — obsah není indexovaný. "
                        "Pro prohlédnutí si ho stáhni přes 📥 ikonu.",
            })

        # 1) Inline preview (browser-native render): PDF, image, audio, video.
        # Tyhle formaty browser zobrazi sam ze storage_path -- processing_error
        # (failed embeddings) je orthogonalni k preview, soubor je validni binary.
        if ext in INLINE_MIME:
            return FileResponse(
                path=doc.storage_path,
                media_type=INLINE_MIME[ext],
                headers={"Content-Disposition": "inline"},
            )

        # 2) Plain text -- raw content jako text/plain (browser zobrazi). Stejne
        # jako PDF orthogonalni k processing_error.
        if ext in PLAIN_TEXT_EXTS:
            return FileResponse(
                path=doc.storage_path,
                media_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": "inline"},
            )

        # 3) Office formaty (DOC/DOCX/XLSX/PPTX/...) -- potrebujeme markitdown-
        # extracted text. Try chunks first (stary processed flow), fallback
        # on-the-fly extract (pokud processing kdysi selhalo na embeddings).
        if ext in OFFICE_LIKE_EXTS or doc.is_processed:
            chunks = (
                ds.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )
            if chunks:
                content = "\n\n".join(c.content for c in chunks if c.content)
                return JSONResponse({
                    "kind": "text",
                    "file_type": ext,
                    "name": doc.name,
                    "content": content,
                    "note": (
                        "Náhled je čistý text bez formátování (extrahovaný "
                        "markitdownem při uploadu). Pro plný formát si stáhni soubor."
                    ),
                })
            # Chunks chybi -- typicky pokud processing selhalo (napr. Voyage
            # embedding failed). Zkusime on-the-fly extract pres markitdown,
            # at user vidi obsah i tak.
            try:
                from modules.rag.application.extraction import extract_text
                content = extract_text(doc.storage_path)
                if content and content.strip():
                    return JSONResponse({
                        "kind": "text",
                        "file_type": ext,
                        "name": doc.name,
                        "content": content,
                        "note": (
                            "Náhled extrahován on-the-fly (původní zpracování "
                            "selhalo na embeddings). Search nad tímto souborem "
                            "zatím nepojede, ale obsah vidíš."
                        ),
                    })
            except Exception as e:
                logger.warning(
                    f"RAG | preview on-the-fly extract failed | doc={document_id}: {e}"
                )
            # Ani fallback nepomohl -- vratime error
            return JSONResponse({
                "kind": "error",
                "file_type": ext,
                "name": doc.name,
                "error": (doc.processing_error or "Žádný obsah nebyl extrahován.")[:500],
            })

        # 4) Fallback -- neznamy format, neni storage_only ani office
        return JSONResponse({
            "kind": "unsupported",
            "file_type": ext,
            "name": doc.name,
            "note": "Pro tento formát zatím nemáme náhled.",
        })
    finally:
        ds.close()


# ── DOWNLOAD RAW FILE ─────────────────────────────────────────────────────

@router.get("/{document_id}/raw")
def download_raw_endpoint(document_id: int, req: Request):
    """
    Vrati raw obsah souboru ke stazeni. Read-only (zadny mutation).
    Tenant scope check -- user smi stahnout jen dokumenty z aktualniho tenantu.

    UI: project files modal -> 📥 download ikona per row.
    """
    from fastapi.responses import FileResponse
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import Document
    import os

    user_id, tenant_id = _get_user_context(req)

    ds = get_data_session()
    try:
        doc = ds.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Dokument neexistuje.")
        if doc.tenant_id != tenant_id:
            # Cross-tenant access -- maskujeme jako 404 aby neukazoval existence.
            raise HTTPException(status_code=404, detail="Dokument neexistuje.")
        if not doc.storage_path or not os.path.exists(doc.storage_path):
            raise HTTPException(status_code=410, detail="Soubor uz nemam na disku.")

        # Display name pro Content-Disposition. Pokud original_filename ma
        # slozkovou strukturu (bulk upload napr. "01 1.10.2025/cert.pdf"),
        # vezmem jen koncovou cast (bez slozky) pro browser download.
        download_name = doc.original_filename or doc.name or f"doc_{document_id}"
        if "/" in download_name:
            download_name = download_name.rsplit("/", 1)[-1]

        return FileResponse(
            path=doc.storage_path,
            filename=download_name,
            media_type="application/octet-stream",
        )
    finally:
        ds.close()


# ── DELETE ────────────────────────────────────────────────────────────────

@router.delete("/{document_id}")
def delete_endpoint(document_id: int, req: Request) -> dict:
    """Smaze dokument (+ fyzicky soubor). Tenant check uvnitr service."""
    from modules.audit.application.service import log_event
    user_id, tenant_id = _get_user_context(req)
    ok = rag_service.delete_document(document_id=document_id, tenant_id=tenant_id)
    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    if not ok:
        log_event(action="document_deleted", status="error",
                  user_id=user_id, tenant_id=tenant_id, entity_id=document_id,
                  error="not_found_or_wrong_tenant",
                  ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=404, detail="Dokument neexistuje nebo patří jinému tenantu.")
    log_event(action="document_deleted", status="success",
              user_id=user_id, tenant_id=tenant_id, entity_id=document_id,
              ip_address=ip, user_agent=ua)
    return {"status": "deleted", "document_id": document_id}


# ── SEARCH ────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    project_id: int | None = None


@router.post("/search")
def search_endpoint(body: SearchRequest, req: Request) -> dict:
    """
    Semanticke hledani. Hodne typicky volane z frontendu pro UI, ale
    AI si drzi paralelni cestu pres search_documents tool (tools.py).
    """
    user_id, tenant_id = _get_user_context(req)
    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query nesmí být prázdný.")
    if body.k < 1 or body.k > 20:
        raise HTTPException(status_code=400, detail="k musí být 1..20.")

    results = rag_service.search_documents(
        query=body.query,
        tenant_id=tenant_id,
        project_id=body.project_id,
        k=body.k,
    )
    return {"results": results, "count": len(results)}
