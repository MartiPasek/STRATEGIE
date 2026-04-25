"""
Thought embedding service (Faze 13a Marti Memory v2 RAG).

Indexovani thoughts do thought_vectors tabulky pres Voyage voyage-3.

Klicove funkce:
  - build_embedding_text(thought, entity_summary)
      Sestavi entity-aware text pro embedding. Format:
      "[<type> | o <entity summary>] <content>"
      Embedding pak nese entity kontext (Honza/EUROSOFT/projekt) a similarity
      match pracuje i na entity-level dotazy.
  - index_thought(thought_id, force=False)
      Indexuje single thought. INSERT do thought_vectors. Pokud uz existuje
      vector pro tento thought_id (UNIQUE constraint), tise skipne (idempotent).
      force=True donuti reindex (UPDATE existujiciho).
  - reindex_thought(thought_id)
      Alias pro index_thought(force=True). Volat po update_thought() kdyz se
      zmenil content nebo entity_links.
  - delete_vector(thought_id)
      Fyzicky smaze vector row (volat po soft_delete_thought).
      FK CASCADE chrani jen pred DELETE thoughts row, soft delete neflowsuje.
  - index_thoughts_batch(thought_ids)
      Bulk indexing pro backfill. Pro 58 existujicich thoughts == 1 Voyage
      batch request (cost ~$0.0004).

Defensive design:
  - Pri jakekoli Voyage chybe (API key chybi, network, timeout) jen WARNING log,
    funkce vrati False/None, ale neshodi parent code (record_thought, batch).
  - Tj. RAG indexing je 'best effort' -- pokud Voyage padne, thought se ulozi do
    thoughts tabulky normalne, jen nebude v RAG dokud se to neopravi.
  - Cron / repair skript muze pak doindexovat chybejici (where v thought_vectors
    chybi).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from core.database_data import get_data_session
from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    Thought, ThoughtEntityLink, ThoughtVector,
)

logger = get_logger("thoughts.embedding")

VOYAGE_MODEL = "voyage-3"


# ── Entity summary helpers ──────────────────────────────────────────────────

def _resolve_entity_names(entity_links: list[dict]) -> dict[tuple[str, int], str]:
    """
    Pro list entity links {entity_type, entity_id} resolveuj jmena entit.
    Vrati slovnik {(type, id): nazev}.

    Cross-DB lookup:
      - user / persona: css_db (User, Persona)
      - tenant: css_db (Tenant)
      - project: data_db nebo css_db (zatim assume css_db, fallback ok)
    """
    if not entity_links:
        return {}

    out: dict[tuple[str, int], str] = {}

    # Group by type pro batch lookup
    by_type: dict[str, list[int]] = {}
    for link in entity_links:
        t = link.get("entity_type")
        i = link.get("entity_id")
        if t and i is not None:
            by_type.setdefault(t, []).append(i)

    cs = get_core_session()
    try:
        # Users
        if "user" in by_type:
            try:
                from modules.core.infrastructure.models_core import User
                rows = cs.query(User).filter(User.id.in_(by_type["user"])).all()
                for u in rows:
                    name = (
                        u.first_name or u.short_name or u.email or f"user#{u.id}"
                    ) if hasattr(u, "first_name") else f"user#{u.id}"
                    out[("user", u.id)] = name
            except Exception as e:
                logger.warning(f"EMBED | resolve users failed: {e}")

        # Personas
        if "persona" in by_type:
            try:
                from modules.core.infrastructure.models_core import Persona
                rows = cs.query(Persona).filter(Persona.id.in_(by_type["persona"])).all()
                for p in rows:
                    out[("persona", p.id)] = p.name or f"persona#{p.id}"
            except Exception as e:
                logger.warning(f"EMBED | resolve personas failed: {e}")

        # Tenants
        if "tenant" in by_type:
            try:
                from modules.core.infrastructure.models_core import Tenant
                rows = cs.query(Tenant).filter(Tenant.id.in_(by_type["tenant"])).all()
                for t in rows:
                    # Tenant ma 'code' jako stable identifier; 'name' nemusi byt vyplneny
                    label = (
                        getattr(t, "code", None)
                        or getattr(t, "name", None)
                        or f"tenant#{t.id}"
                    )
                    out[("tenant", t.id)] = label
            except Exception as e:
                logger.warning(f"EMBED | resolve tenants failed: {e}")
    finally:
        cs.close()

    # Projects (zatim minimal -- jen fallback)
    if "project" in by_type:
        for pid in by_type["project"]:
            out[("project", pid)] = f"projekt#{pid}"
        # TODO: nacist skutecny project name z dat (Project model location?)

    return out


def _format_entity_summary(entity_links: list[dict]) -> str:
    """
    Z entity_links sestavi human-readable summary pro embedding text.
    Priklady:
      - "o Honzovi (user), v EUROSOFT (tenant)"
      - "o Marti-AI (persona)"
      - prazdny string pokud zadne entity
    """
    if not entity_links:
        return ""
    names = _resolve_entity_names(entity_links)
    parts: list[str] = []
    seen_types: set[str] = set()
    for link in entity_links:
        t = link.get("entity_type")
        i = link.get("entity_id")
        if not t or i is None:
            continue
        name = names.get((t, i), f"{t}#{i}")
        if t == "user":
            parts.append(f"o {name}")
        elif t == "persona":
            parts.append(f"o {name} (persona)")
        elif t == "tenant":
            parts.append(f"v {name}")
        elif t == "project":
            parts.append(f"projekt {name}")
        seen_types.add(t)
    return ", ".join(parts)


def build_embedding_text(thought_content: str, thought_type: str, entity_links: list[dict]) -> str:
    """
    Sestavi entity-aware text pro embedding (Q1 z memory_rag.md).

    Format:  "[<type> | o <entity summary>] <content>"

    Priklady:
      build_embedding_text(
          "dnes pomohl s rozdelením úkolů",
          "observation",
          [{"entity_type": "user", "entity_id": 42}, {"entity_type": "tenant", "entity_id": 2}]
      )
      ->  "[observation | o Honza, v EUROSOFT] dnes pomohl s rozdelením úkolů"

      build_embedding_text("Marti se ozve zítra", "todo", [])
      ->  "[todo] Marti se ozve zítra"
    """
    content = (thought_content or "").strip()
    if not content:
        # Vector je smysluplny jen pokud ma obsah; pri prazdnem content
        # vratime aspon type marker
        return f"[{thought_type}]"

    summary = _format_entity_summary(entity_links)
    if summary:
        return f"[{thought_type} | {summary}] {content}"
    return f"[{thought_type}] {content}"


# ── Voyage helper (lazy import + fallback) ──────────────────────────────────

def _voyage_embed(text: str) -> list[float] | None:
    """
    Embed single text pres Voyage. Vrati list[float] nebo None pri chybe.
    Pri chybe jen WARNING log, ne raise -- caller nesmi shodit parent flow.
    """
    try:
        from modules.rag.application.embeddings import embed_documents
        embeddings = embed_documents([text])
        if not embeddings:
            return None
        return embeddings[0]
    except Exception as e:
        logger.warning(f"EMBED | voyage embed failed: {e}")
        return None


def _voyage_embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed batch textu. Pri chybe vrati prazdny list (caller dela skip).
    """
    if not texts:
        return []
    try:
        from modules.rag.application.embeddings import embed_documents
        return embed_documents(texts)
    except Exception as e:
        logger.warning(f"EMBED | voyage embed batch failed: {e}")
        return []


# ── Build vector row from thought ───────────────────────────────────────────

def _load_thought_with_links(session, thought_id: int) -> tuple[Thought, list[dict]] | None:
    """Nacte thought + jeho entity_links jako list dictu."""
    t = session.query(Thought).filter_by(id=thought_id).first()
    if t is None:
        return None
    links = session.query(ThoughtEntityLink).filter_by(thought_id=thought_id).all()
    link_dicts = [
        {"entity_type": l.entity_type, "entity_id": l.entity_id}
        for l in links
    ]
    return t, link_dicts


def _vector_payload_from_thought(t: Thought, entity_links: list[dict]) -> dict:
    """
    Sestavi dict polí pro ThoughtVector row z Thought ORM + entity_links.
    Embedding je separe (vola se Voyage). Tady jen ostatni denormalizovana pole.
    """
    # Denormalize entity arrays per type
    by_type: dict[str, list[int]] = {
        "user": [], "tenant": [], "project": [], "persona": [],
    }
    for link in entity_links:
        t_type = link.get("entity_type")
        t_id = link.get("entity_id")
        if t_type in by_type and t_id is not None:
            by_type[t_type].append(t_id)

    # is_diary z meta JSON
    is_diary = False
    meta = t.meta or {}
    if isinstance(meta, dict) and meta.get("is_diary") is True:
        is_diary = True

    return {
        "thought_id": t.id,
        "model": VOYAGE_MODEL,
        "author_persona_id": t.author_persona_id,
        "tenant_scope": t.tenant_scope,
        "status": t.status,
        "entity_user_ids": by_type["user"],
        "entity_tenant_ids": by_type["tenant"],
        "entity_project_ids": by_type["project"],
        "entity_persona_ids": by_type["persona"],
        "is_diary": is_diary,
        "thought_type": t.type,
    }


# ── Public API: index / reindex / delete ────────────────────────────────────

def index_thought(thought_id: int, force: bool = False) -> bool:
    """
    Indexuje thought do thought_vectors. Idempotent.

    force=False (default): pokud uz existuje vector, skipne (no-op).
    force=True: reindex -- UPDATE embedding + denorm fields.

    Vraci True pri uspechu, False pri preskoceni/chybe.
    Best effort -- pri chybe jen log, nesho deni parent flow.
    """
    session = get_data_session()
    try:
        loaded = _load_thought_with_links(session, thought_id)
        if loaded is None:
            logger.warning(f"EMBED | thought {thought_id} neexistuje, skip index")
            return False
        thought, entity_links = loaded

        # Soft-deleted thought neindexovat
        if thought.deleted_at is not None:
            logger.info(f"EMBED | thought {thought_id} je soft-deleted, skip index")
            return False

        # Existuje vector?
        existing = session.query(ThoughtVector).filter_by(thought_id=thought_id).first()
        if existing is not None and not force:
            logger.debug(f"EMBED | thought {thought_id} uz indexovan, skip (force=False)")
            return False

        # Build embedding text + voyage call
        text = build_embedding_text(thought.content, thought.type, entity_links)
        vector = _voyage_embed(text)
        if vector is None:
            return False  # Voyage failed, log uz byl

        payload = _vector_payload_from_thought(thought, entity_links)
        payload["embedding"] = vector

        if existing is None:
            row = ThoughtVector(**payload)
            session.add(row)
        else:
            for k, v in payload.items():
                setattr(existing, k, v)

        session.commit()
        logger.info(
            f"EMBED | indexed thought={thought_id} | type={thought.type} | "
            f"persona={thought.author_persona_id} | force={force}"
        )
        return True
    except Exception as e:
        logger.exception(f"EMBED | index_thought({thought_id}) failed: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return False
    finally:
        session.close()


def reindex_thought(thought_id: int) -> bool:
    """Alias pro index_thought(thought_id, force=True). Volat po update_thought()."""
    return index_thought(thought_id, force=True)


def delete_vector(thought_id: int) -> bool:
    """
    Fyzicky smaze ThoughtVector row pro dany thought_id.
    Volat po soft_delete_thought() -- soft delete v thoughts neflowsuje
    cascade do thought_vectors (FK CASCADE chrani jen pred DROP).
    """
    session = get_data_session()
    try:
        deleted = (
            session.query(ThoughtVector)
            .filter_by(thought_id=thought_id)
            .delete(synchronize_session=False)
        )
        session.commit()
        if deleted:
            logger.info(f"EMBED | deleted vector for thought={thought_id}")
        return bool(deleted)
    except Exception as e:
        logger.warning(f"EMBED | delete_vector({thought_id}) failed: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return False
    finally:
        session.close()


# ── Batch: pro backfill skript ──────────────────────────────────────────────

def index_thoughts_batch(thought_ids: list[int], force: bool = False) -> dict:
    """
    Bulk indexing pro backfill. Vola Voyage v jednom batchi (max 128 textu/req).

    Vraci dict: {indexed: int, skipped: int, failed: int}.
    Idempotent: pokud uz vector existuje a force=False, skipne.
    """
    if not thought_ids:
        return {"indexed": 0, "skipped": 0, "failed": 0}

    session = get_data_session()
    try:
        # Existing vectory
        existing_ids = set()
        if not force:
            rows = (
                session.query(ThoughtVector.thought_id)
                .filter(ThoughtVector.thought_id.in_(thought_ids))
                .all()
            )
            existing_ids = {r[0] for r in rows}

        # Nacti thoughts
        thoughts = (
            session.query(Thought)
            .filter(Thought.id.in_(thought_ids))
            .filter(Thought.deleted_at.is_(None))
            .all()
        )
        thought_map = {t.id: t for t in thoughts}

        # Nacti entity_links bulk
        all_links = (
            session.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id.in_(thought_ids))
            .all()
        )
        links_by_thought: dict[int, list[dict]] = {}
        for l in all_links:
            links_by_thought.setdefault(l.thought_id, []).append({
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
            })

        # Sestav texty + ID mapping (jen pro non-skipped)
        to_embed: list[tuple[int, str]] = []
        skipped = 0
        for tid in thought_ids:
            if tid in existing_ids and not force:
                skipped += 1
                continue
            t = thought_map.get(tid)
            if t is None:
                skipped += 1
                continue
            text = build_embedding_text(
                t.content, t.type, links_by_thought.get(tid, [])
            )
            to_embed.append((tid, text))

        if not to_embed:
            return {"indexed": 0, "skipped": skipped, "failed": 0}

        # Voyage batch
        texts = [t for _, t in to_embed]
        embeddings = _voyage_embed_batch(texts)
        if not embeddings or len(embeddings) != len(to_embed):
            logger.warning(
                f"EMBED | batch | voyage returned {len(embeddings)} != {len(to_embed)}"
            )
            return {"indexed": 0, "skipped": skipped, "failed": len(to_embed)}

        # Upsert do thought_vectors
        indexed = 0
        failed = 0
        for (tid, _), embedding in zip(to_embed, embeddings):
            try:
                t = thought_map[tid]
                links = links_by_thought.get(tid, [])
                payload = _vector_payload_from_thought(t, links)
                payload["embedding"] = embedding

                existing = (
                    session.query(ThoughtVector)
                    .filter_by(thought_id=tid)
                    .first()
                )
                if existing is None:
                    session.add(ThoughtVector(**payload))
                else:
                    for k, v in payload.items():
                        setattr(existing, k, v)
                indexed += 1
            except Exception as e:
                logger.warning(f"EMBED | upsert thought={tid} failed: {e}")
                failed += 1

        session.commit()
        logger.info(
            f"EMBED | batch done | indexed={indexed} | skipped={skipped} | failed={failed}"
        )
        return {"indexed": indexed, "skipped": skipped, "failed": failed}

    except Exception as e:
        logger.exception(f"EMBED | index_thoughts_batch failed: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return {"indexed": 0, "skipped": 0, "failed": len(thought_ids)}
    finally:
        session.close()


__all__ = [
    "build_embedding_text",
    "index_thought",
    "reindex_thought",
    "delete_vector",
    "index_thoughts_batch",
    "VOYAGE_MODEL",
]
