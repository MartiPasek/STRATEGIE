"""
RAG service -- high-level orkestrator.

Flow:
    upload_document(bytes, filename, tenant_id, project_id, user_id) -> Document row
        -> save to disk, insert Document with is_processed=False
        -> sync call process_document (MVP)

    process_document(document_id) -> None
        -> extract text, chunk, embed batches, insert DocumentChunk + DocumentVector
        -> set is_processed=True nebo processing_error

    search_documents(query, tenant_id, project_id=None, k=5) -> list[dict]
        -> embed query, pgvector cosine distance, scope WHERE, return chunks

    list_documents(tenant_id, project_id=None) -> list[dict]
    delete_document(document_id, user_id) -> bool
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text as sql_text

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Document, DocumentChunk, DocumentVector,
)
from modules.rag.application.chunking import chunk_text
from modules.rag.application.embeddings import (
    embed_documents, embed_query, VOYAGE_MODEL,
)
from modules.rag.application.extraction import extract_text, detect_file_type
from modules.rag.application.storage import save_upload, delete_document_file

logger = get_logger("rag.service")


# ── UPLOAD + PROCESSING ───────────────────────────────────────────────────

def upload_document(
    *,
    file_bytes: bytes,
    filename: str,
    tenant_id: int,
    user_id: int,
    project_id: int | None = None,
    display_name: str | None = None,
) -> int:
    """
    Ulozi dokument + zaradi do zpracovani (sync v MVP). Vrati document_id.
    Raises jen pri totalnich chybach (DB down, disk full). Processing chyby
    se ulozi do documents.processing_error a dokument zustane nezpracovany.
    """
    ext = detect_file_type(filename)
    name = (display_name or filename or "Bez názvu").strip()

    session = get_data_session()
    try:
        doc = Document(
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            name=name,
            original_filename=filename,
            file_type=ext,
            file_size_bytes=len(file_bytes),
            is_processed=False,
            created_at=datetime.now(timezone.utc),
        )
        session.add(doc)
        session.flush()     # potrebujeme id pred ulozenim souboru
        document_id = doc.id

        # Ulozit na disk (jmeno souboru je document_id.ext)
        storage_path = save_upload(tenant_id, document_id, ext, file_bytes)
        doc.storage_path = storage_path
        session.commit()
        logger.info(
            f"RAG | document uploaded | id={document_id} | tenant={tenant_id} | "
            f"filename={filename} | size={len(file_bytes)}"
        )
    finally:
        session.close()

    # Sync processing (MVP). V budoucnu muzeme hodit do background task / queue.
    try:
        process_document(document_id)
    except Exception as e:
        logger.exception(f"RAG | processing failed | document_id={document_id}: {e}")
        # Mark error a pokracuj -- dokument je ve stavu is_processed=False s errorem.
        _mark_processing_error(document_id, str(e))

    return document_id


def process_document(document_id: int) -> None:
    """
    Extrakce -> chunking -> embeddings -> DB.
    Vola se inline z upload_document (MVP sync), v budoucnu z background tasku.
    """
    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} neexistuje")
        if not doc.storage_path:
            raise ValueError(f"Document {document_id} nema storage_path")
        storage_path = doc.storage_path
    finally:
        session.close()

    # 1) Extract text -- nejdele trvajici krok pro velke PDF (vteriny az desitky)
    logger.info(f"RAG | extracting text | document_id={document_id} | path={storage_path}")
    try:
        text_content = extract_text(storage_path)
    except Exception as e:
        raise RuntimeError(f"Extrakce textu selhala: {e}")

    if not text_content or not text_content.strip():
        raise RuntimeError("Z dokumentu nebyl extrahovan zadny text (prazdny nebo nekompatibilni format)")

    # 2) Chunking
    chunks = chunk_text(text_content)
    if not chunks:
        raise RuntimeError("Chunking vratil 0 chunku (text moc kratky?)")
    logger.info(f"RAG | chunking done | document_id={document_id} | chunks={len(chunks)}")

    # 3) Embeddings (batch na Voyage)
    texts = [c["content"] for c in chunks]
    embeddings = embed_documents(texts)
    if len(embeddings) != len(chunks):
        raise RuntimeError(
            f"Voyage vratil {len(embeddings)} embeddings pro {len(chunks)} chunku -- mismatch"
        )

    # 4) Insert vsechno atomicky
    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} mezitim smazan")
        doc.extracted_text_length = len(text_content)

        for chunk, embedding in zip(chunks, embeddings):
            dc = DocumentChunk(
                document_id=document_id,
                content=chunk["content"],
                chunk_index=chunk["index"],
                token_count=chunk["approx_tokens"],
                char_start=chunk["char_start"],
                char_end=chunk["char_end"],
            )
            session.add(dc)
            session.flush()     # potrebujeme chunk_id pro vector FK
            dv = DocumentVector(
                chunk_id=dc.id,
                embedding=embedding,
                model=VOYAGE_MODEL,
            )
            session.add(dv)

        doc.is_processed = True
        doc.processing_error = None
        session.commit()
        logger.info(
            f"RAG | processing done | document_id={document_id} | "
            f"chunks={len(chunks)} | text_len={len(text_content)}"
        )
    finally:
        session.close()


def _mark_processing_error(document_id: int, error_message: str) -> None:
    """Zaznamena error na dokumentu, aby UI videlo co se pokazilo."""
    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if doc:
            doc.processing_error = error_message[:500]
            doc.is_processed = False
            session.commit()
    finally:
        session.close()


# ── SEARCH (retrieval pro AI tool) ────────────────────────────────────────

def search_documents(
    *,
    query: str,
    tenant_id: int,
    project_id: int | None = None,
    k: int = 5,
    include_tenant_global: bool = True,
) -> list[dict]:
    """
    Semanticke vyhledavani. Vraci top-k chunku serazenych cosine similarity.

    Scope:
      tenant_id povinny (nikdy nedostupne cross-tenant).
      project_id volitelny:
        - None + include_tenant_global=True  -> obecne tenant docs (project_id IS NULL)
                                              + zadne project-specificke
        - int + include_tenant_global=True  -> chunky z daneho projektu
                                              + tenant-globalni (project_id IS NULL)
        - int + include_tenant_global=False -> jen chunky z daneho projektu
    """
    # 1) Embed query (1024-dim)
    qvec = embed_query(query)

    # 2) SQL s pgvector cosine distance operator <=>.
    #    Lower distance = higher similarity. ORDER BY asc.
    #    Filter: dokument musi byt processed + spravny tenant scope.
    scope_clause = "d.project_id IS NULL"
    params: dict = {"tenant_id": tenant_id, "k": k, "query_vec": qvec}
    if project_id is not None:
        if include_tenant_global:
            scope_clause = "(d.project_id = :project_id OR d.project_id IS NULL)"
            params["project_id"] = project_id
        else:
            scope_clause = "d.project_id = :project_id"
            params["project_id"] = project_id

    sql = f"""
        SELECT
            c.id               AS chunk_id,
            c.content          AS content,
            c.chunk_index      AS chunk_index,
            d.id               AS document_id,
            d.name             AS document_name,
            d.original_filename AS original_filename,
            d.file_type        AS file_type,
            (v.embedding <=> (:query_vec)::vector) AS distance
        FROM document_vectors v
        JOIN document_chunks c ON c.id = v.chunk_id
        JOIN documents d       ON d.id = c.document_id
        WHERE d.tenant_id = :tenant_id
          AND d.is_processed = TRUE
          AND {scope_clause}
        ORDER BY v.embedding <=> (:query_vec)::vector ASC
        LIMIT :k
    """

    session = get_data_session()
    try:
        rows = session.execute(sql_text(sql), params).mappings().all()
        results = [
            {
                "chunk_id": r["chunk_id"],
                "content": r["content"],
                "chunk_index": r["chunk_index"],
                "document_id": r["document_id"],
                "document_name": r["document_name"],
                "original_filename": r["original_filename"],
                "file_type": r["file_type"],
                # Similarity score pro UI (1.0 = perfektní match, 0.0 = ortogonálni).
                # Cosine distance je 0..2, takze 1 - dist/2 = similarity v 0..1.
                "similarity": max(0.0, 1.0 - float(r["distance"]) / 2.0),
            }
            for r in rows
        ]
        logger.info(
            f"RAG | search | tenant={tenant_id} | project={project_id} | "
            f"query_len={len(query)} | results={len(results)}"
        )
        return results
    finally:
        session.close()


# ── LIST + DELETE ─────────────────────────────────────────────────────────

def list_documents(
    *,
    tenant_id: int,
    project_id: int | None = None,
    include_tenant_global: bool = True,
) -> list[dict]:
    """Vypis dokumentu ve scope. Pro UI seznam + delete."""
    session = get_data_session()
    try:
        query = session.query(Document).filter_by(tenant_id=tenant_id)
        if project_id is not None:
            if include_tenant_global:
                query = query.filter(
                    (Document.project_id == project_id) | (Document.project_id.is_(None))
                )
            else:
                query = query.filter(Document.project_id == project_id)
        else:
            query = query.filter(Document.project_id.is_(None))

        docs = query.order_by(Document.created_at.desc()).all()
        return [_serialize_document(d) for d in docs]
    finally:
        session.close()


def delete_document(*, document_id: int, tenant_id: int) -> bool:
    """Smaze dokument (DB rows cascade + fyzicky soubor).
    Tenant check: nelze mazat dokument z ciziho tenantu."""
    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id, tenant_id=tenant_id).first()
        if not doc:
            return False
        storage_path = doc.storage_path
        session.delete(doc)       # CASCADE smaze chunky + vektory
        session.commit()
    finally:
        session.close()

    delete_document_file(storage_path)
    logger.info(f"RAG | document deleted | id={document_id} | tenant={tenant_id}")
    return True


def _serialize_document(d: Document) -> dict:
    status = (
        "ready" if d.is_processed
        else ("error" if d.processing_error else "processing")
    )
    return {
        "id": d.id,
        "name": d.name,
        "original_filename": d.original_filename,
        "file_type": d.file_type,
        "file_size_bytes": d.file_size_bytes,
        "tenant_id": d.tenant_id,
        "project_id": d.project_id,
        "user_id": d.user_id,
        "is_processed": d.is_processed,
        "processing_error": d.processing_error,
        "status": status,
        "extracted_text_length": d.extracted_text_length,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
