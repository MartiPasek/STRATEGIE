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
