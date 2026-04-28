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


# ── EXTRACTION WHITELIST (v3.5) ───────────────────────────────────────────
# Formaty, ze kterych umime vytahnout text -- markitdown podporuje nase
# manualni bypass v extraction.py (txt/md/csv/log primym readem).
#
# Vsechno OSTATNI -> storage_only=True pri uploadu. Pipeline preskoci
# extract_text() a misto toho vyrobi 1 'filename chunk' (nazev + slozka +
# projekt + typ) pro semantic search dohledani podle jmena.
EXTRACTABLE_EXTENSIONS: frozenset[str] = frozenset({
    # plain text family
    "txt", "md", "csv", "log", "json", "xml", "yaml", "yml", "sql", "ini",
    # rich text
    "rtf", "html", "htm",
    # office (Microsoft + LibreOffice)
    "pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt",
    "odt", "ods", "odp",
    # ebook
    "epub",
    # email (markitdown msg/eml support)
    "msg", "eml",
    # images (OCR)
    "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp",
    # audio (whisper transcription)
    "mp3", "wav", "m4a", "wma", "ogg", "flac", "aac", "mp4",
    # poznamka mp4 -- markitdown vytahne audio track + transcribe;
    # video bez audio vrati prazdny string -> processing_error a fallback
    # rucne nebo pres backfill na storage_only=True.
})


def is_extractable(extension: str) -> bool:
    """True pokud markitdown / nas extraction.py umi extrahovat text z formatu."""
    return (extension or "").lower().lstrip(".") in EXTRACTABLE_EXTENSIONS


# ── UPLOAD + PROCESSING ───────────────────────────────────────────────────

def upload_document(
    *,
    file_bytes: bytes,
    filename: str,
    tenant_id: int,
    user_id: int | None,
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

    # v3.5: detekuj jestli je format extrahovatelny (markitdown-supported).
    # Pokud ne -> storage_only=True, pipeline pak preskoci extract_text() a
    # misto toho vytvori filename chunk pro searchability podle jmena.
    storage_only_flag = not is_extractable(ext)

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
            storage_only=storage_only_flag,
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

    # Phase 16-A: activity_log hook -- upload je událost pro Marti-AI's
    # 'recall_today'. Skip pokud system import (user_id=None, např. email
    # attachment auto-import -- attach helper zaznamenává sám zvlášť).
    if user_id is not None:
        try:
            from modules.activity.application import activity_service as _act_doc
            _user_label = "user"
            try:
                from core.database_core import get_core_session as _gcs_act
                from modules.core.infrastructure.models_core import User as _U_act
                _cs_act = _gcs_act()
                try:
                    _u_act = _cs_act.query(_U_act).filter_by(id=user_id).first()
                    if _u_act:
                        _user_label = (
                            f"{_u_act.first_name or ''} {_u_act.last_name or ''}"
                        ).strip() or _u_act.username or "user"
                finally:
                    _cs_act.close()
            except Exception:
                pass
            _proj_label = ""
            if project_id:
                try:
                    from core.database_core import get_core_session as _gcs_pn
                    from modules.core.infrastructure.models_core import Project as _Proj
                    _cs_pn = _gcs_pn()
                    try:
                        _p = _cs_pn.query(_Proj).filter_by(id=project_id).first()
                        if _p:
                            _proj_label = f" do projektu {_p.name}"
                    finally:
                        _cs_pn.close()
                except Exception:
                    pass
            _name = name or filename or f"doc#{document_id}"
            _act_doc.record(
                category="doc_upload",
                summary=f"{_user_label} uploadoval/a {_name}{_proj_label}",
                importance=3,
                persona_id=None,
                user_id=user_id,
                tenant_id=tenant_id,
                actor="user",
                ref_type="document",
                ref_id=document_id,
            )
        except Exception as _act_e:
            logger.warning(f"RAG | activity hook failed | doc={document_id}: {_act_e}")

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
        # v3.5-c: pro storage_only nacti i metadata pro filename chunk
        is_storage_only = bool(doc.storage_only)
        doc_name = doc.name or doc.original_filename or f"doc#{document_id}"
        doc_ext = doc.file_type or ""
        doc_project_id = doc.project_id
    finally:
        session.close()

    # v3.5-c: storage_only -> preskoc extract_text/chunk, vyrob 1 filename chunk
    # pro searchability podle nazvu/slozky/projektu/typu (nepodporovane formaty:
    # ZIP, RAR, MP4 bez audio, EXE, ...).
    if is_storage_only:
        _process_storage_only(document_id, doc_name, doc_ext, doc_project_id)
        return

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


def _process_storage_only(
    document_id: int,
    doc_name: str,
    doc_ext: str,
    doc_project_id: int | None,
) -> None:
    """
    v3.5-c: Pipeline pro ne-extrahovatelne formaty (storage_only=True).

    Misto extract_text + chunking vytvori 1 'filename chunk' s popisem
    souboru -- nazev, slozka, typ, projekt -- a embedduje ho. Document
    pak je dohledatelny pres semantic search podle jmena (napr. uzivatel
    napise 'kde mam ten zip s fotkami z Vanoc' a najde se podle nazvu).

    Nedotyka se file_bytes na disku -- ZIP/MP4/EXE zustavaji v uschove.
    """
    logger.info(
        f"RAG | storage_only -> filename chunk | document_id={document_id}"
        f" | name={doc_name!r}"
    )

    # Sestav filename chunk: oddel slozku/jmeno (display_name muze obsahovat
    # 'slozka/soubor.ext' z bulk uploadu).
    slash_idx = doc_name.rfind("/")
    if slash_idx > 0:
        folder_part = doc_name[:slash_idx]
        base_part = doc_name[slash_idx + 1:]
    else:
        folder_part = ""
        base_part = doc_name

    project_part = ""
    if doc_project_id:
        try:
            from core.database_core import get_core_session
            from modules.core.infrastructure.models_core import Project
            cs = get_core_session()
            try:
                p = cs.query(Project).filter_by(id=doc_project_id).first()
                if p:
                    project_part = p.name
            finally:
                cs.close()
        except Exception as e:
            logger.warning(f"RAG | nelze nacist projekt #{doc_project_id}: {e}")

    fn_chunk_text = (
        f"Soubor: {base_part}\n"
        f"Slozka: {folder_part or '(bez slozky)'}\n"
        f"Typ: {doc_ext or '?'}\n"
        f"Projekt: {project_part or '(neprirazeno)'}\n"
        f"Poznamka: Tento soubor je v uschove, jeho obsah neni indexovan"
        f" (nepodporovany format pro extrakci textu). Searchable je podle"
        f" nazvu, slozky a projektu."
    )

    # Embed (Voyage). Pokud spadne -> RuntimeError -> caller (upload_document)
    # to chyti pres _mark_processing_error.
    try:
        embedding = embed_documents([fn_chunk_text])[0]
    except Exception as e:
        raise RuntimeError(f"Embedding filename chunk selhal: {e}")

    session = get_data_session()
    try:
        doc = session.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} mezitim smazan")
        doc.extracted_text_length = len(fn_chunk_text)

        dc = DocumentChunk(
            document_id=document_id,
            content=fn_chunk_text,
            chunk_index=0,
            token_count=max(1, len(fn_chunk_text) // 4),
            char_start=0,
            char_end=len(fn_chunk_text),
        )
        session.add(dc)
        session.flush()
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
            f"RAG | storage_only processing done | document_id={document_id}"
            f" | filename chunk len={len(fn_chunk_text)}"
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
