"""
Thought retrieval service (Faze 13b Marti Memory v2 RAG).

Vector search nad thought_vectors s hybrid scoring + scope filter + mode-aware
boosting/skipping (per design v docs/memory_rag.md).

Klicova funkce:
  retrieve_relevant_memories(
      query, persona_id, user_id, tenant_id, is_parent,
      k=8, mode='personal',
  ) -> list[dict]

Output:
  [
    {
      "thought_id": 65,
      "content": "...",
      "type": "fact",
      "status": "knowledge",
      "certainty": 90,
      "is_diary": False,
      "created_at": "2026-04-25T10:40:14Z",
      "entity_links": [{"entity_type": "user", "entity_id": 1}, ...],
      "similarity": 0.87,           # 0..1
      "score": 0.78,                # final hybrid score po vsech bonusech
      "score_breakdown": {           # pro debug / Dev View
          "similarity": 0.87,
          "priority": 1.0,
          "recency": 1.0,
          "certainty_factor": 0.9,
          "entity_boost": 0.15,
          "diary_boost": 0.0,
      },
    },
    ...
  ]

Hybrid score formula:
  base   = similarity × priority × recency × (certainty / 100)
  boosts = entity_boost + diary_boost + ... (mode-dependent)
  score  = base + boosts

Filter logika:
  - D1: author_persona_id = :persona_id (kazda persona ma vlastni namespace)
  - C1: tenant_scope = :tenant_id OR tenant_scope IS NULL  (rodicovsky bypass)
  - Mode-aware:
      * personal: include diaries (boost +0.10), all types
      * project:  include diaries, exclude entity_link.persona thoughts
                  (zatim nuance, future), prioritize project entity link
      * work:     EXCLUDE diaries (is_diary=True), prioritize tenant link
      * system:   include all, no special boost

Read-only (zatim) -- caller fetchne result, dela co chce. Composer integration
je samostatna Faze 13c (Phase D z memory_rag.md migration path).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text as sql_text

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import (
    ThoughtEntityLink,
)

logger = get_logger("thoughts.retrieval")


# ── Konfigurace skoringu (default; future presunout do core/config.py) ──────

# Priority per source layer (zatim jen thoughts; A3 architecture pro future
# rozsireni o communication_vectors a document_vectors).
LAYER_PRIORITY = {
    "thought": 1.0,
    "communication": 0.6,
    "document": 0.4,
}

# Recency decay -- thought aging:
# diary nebo knowledge (potvrzena pravda) = vzdy 1.0 (forever)
# notes (low certainty) starnou
RECENCY_BUCKETS = [
    (7,    1.00),    # <7 dni: full
    (30,   0.85),
    (90,   0.70),
    (365,  0.50),
    # jinde: 0.30
]
RECENCY_FALLBACK = 0.30

# Boost hodnoty -- jemne signaly, nedominantni pres similarity
# (pri puvodnich 0.15/0.10 entity boost dominoval -- skoro vsechny thoughts maji
# entity_user_ids=[Marti], takze +0.15 byl konstantni "all-rounder bias".)
ENTITY_USER_BOOST = 0.05
ENTITY_TENANT_BOOST = 0.03
ENTITY_PROJECT_BOOST = 0.05
DIARY_PERSONAL_BOOST = 0.08        # personal mode boost is_diary=True (vyssi -- diar je hlavni signal modu)
FRESHNESS_BONUS_24H = 0.03          # very recent (<24h) -- jemny tlak na novy


# ── Helpers ─────────────────────────────────────────────────────────────────

def _calc_recency(thought_created_at: datetime, is_diary: bool, status: str) -> float:
    """
    Recency decay per design:
    - is_diary nebo status='knowledge' -> vzdy 1.0 (osobni zazitky / potvrzena pravda nestarne)
    - jinak: bucketed decay podle stari
    """
    if is_diary or status == "knowledge":
        return 1.0
    now = datetime.now(timezone.utc)
    if thought_created_at.tzinfo is None:
        # SQLAlchemy nekdy vrati naive datetime z PG -- assume UTC
        thought_created_at = thought_created_at.replace(tzinfo=timezone.utc)
    age_days = (now - thought_created_at).days
    for max_days, weight in RECENCY_BUCKETS:
        if age_days < max_days:
            return weight
    return RECENCY_FALLBACK


def _calc_freshness_bonus(thought_created_at: datetime) -> float:
    """Bonus pro velmi cerstve thoughts (<24h)."""
    now = datetime.now(timezone.utc)
    if thought_created_at.tzinfo is None:
        thought_created_at = thought_created_at.replace(tzinfo=timezone.utc)
    age_hours = (now - thought_created_at).total_seconds() / 3600
    return FRESHNESS_BONUS_24H if age_hours < 24 else 0.0


def _calc_entity_boost(
    *,
    entity_user_ids: list[int],
    entity_tenant_ids: list[int],
    entity_project_ids: list[int],
    current_user_id: int | None,
    current_tenant_id: int | None,
    current_project_id: int | None = None,
) -> float:
    """
    Entity boost: pokud thought ma entity link na current user / tenant / project,
    boost similarity score. Vyssi pri user-level match (specificky), nizsi pri
    tenant/project (obecny kontext).
    """
    boost = 0.0
    if current_user_id is not None and current_user_id in (entity_user_ids or []):
        boost += ENTITY_USER_BOOST
    if current_tenant_id is not None and current_tenant_id in (entity_tenant_ids or []):
        boost += ENTITY_TENANT_BOOST
    if current_project_id is not None and current_project_id in (entity_project_ids or []):
        boost += ENTITY_PROJECT_BOOST
    return boost


def _calc_mode_modifier(is_diary: bool, mode: str) -> tuple[bool, float]:
    """
    Mode-aware filter + boost.
    Vraci (skip: bool, mode_boost: float)

    - personal: nikdy neskip; diary boost +0.10
    - project:  nikdy neskip; bez extra
    - work:     SKIP diaries; bez extra
    - system:   nikdy neskip; bez extra
    """
    if mode == "work":
        if is_diary:
            return True, 0.0
        return False, 0.0
    if mode == "personal":
        return False, DIARY_PERSONAL_BOOST if is_diary else 0.0
    # project / system / unknown
    return False, 0.0


# ── Public API ──────────────────────────────────────────────────────────────

def retrieve_relevant_memories(
    *,
    query: str,
    persona_id: int | None,
    user_id: int | None,
    tenant_id: int | None,
    is_parent: bool = False,
    k: int = 8,
    mode: str = "personal",
    project_id: int | None = None,
    coarse_k: int = 30,
) -> list[dict[str, Any]]:
    """
    Vyhleda top-K relevantnich thoughts pro query, podle hybrid score.

    Two-stage:
      Stage 1 (coarse): pgvector HNSW top `coarse_k` (default 30)
      Stage 2 (fine):   hybrid score rerank, vraci top `k` (default 8)

    Filter:
      - D1: author_persona_id = persona_id (NULL = universal, viditelne vsude)
      - C1: tenant_scope = tenant_id OR NULL OR is_parent (rodicovsky bypass)
      - Mode-aware: 'work' SKIP diaries; ostatni include
      - Soft delete: deleted_at IS NULL (filtrovano implicit pres ON DELETE CASCADE
                     vs explicit -- thought_vectors zustanou pri soft delete dokud
                     se nezavola embedding_service.delete_vector. Filtrujeme join.)

    Pri prazdnem query / chybi VOYAGE_API_KEY -> vraci [] (best effort).
    """
    if not query or not query.strip():
        logger.warning("RETRIEVAL | empty query, returning []")
        return []

    # 1) Embed query
    try:
        from modules.rag.application.embeddings import embed_query
        qvec = embed_query(query)
    except Exception as e:
        logger.warning(f"RETRIEVAL | embed_query failed: {e}")
        return []

    # 2) Build SQL filter
    filters: list[str] = []
    params: dict = {"query_vec": qvec, "coarse_k": max(coarse_k, k)}

    # D1 persona ownership
    if persona_id is not None:
        filters.append("(tv.author_persona_id = :persona_id OR tv.author_persona_id IS NULL)")
        params["persona_id"] = persona_id

    # C1 tenant scope (rodicovsky bypass)
    if not is_parent:
        if tenant_id is not None:
            filters.append("(tv.tenant_scope = :tenant_id OR tv.tenant_scope IS NULL)")
            params["tenant_id"] = tenant_id
        else:
            # No tenant context -> jen universal
            filters.append("tv.tenant_scope IS NULL")

    # Soft delete check (join na thoughts.deleted_at)
    filters.append("t.deleted_at IS NULL")

    # Work mode: skip diaries v SQL stage 1 (zbyte not se filtruje v Pythonu)
    if mode == "work":
        filters.append("tv.is_diary = FALSE")

    where_clause = " AND ".join(filters) if filters else "TRUE"

    # 3) SQL: pgvector cosine distance operator <=>
    #    Pripojime thoughts pro full content + entity_links pro post-processing
    sql = f"""
        SELECT
            tv.thought_id     AS thought_id,
            tv.thought_type   AS thought_type,
            tv.is_diary       AS is_diary,
            tv.author_persona_id AS author_persona_id,
            tv.tenant_scope   AS tenant_scope,
            tv.status         AS status,
            tv.entity_user_ids AS entity_user_ids,
            tv.entity_tenant_ids AS entity_tenant_ids,
            tv.entity_project_ids AS entity_project_ids,
            tv.entity_persona_ids AS entity_persona_ids,
            t.content         AS content,
            t.certainty       AS certainty,
            t.created_at      AS created_at,
            (tv.embedding <=> (:query_vec)::vector) AS distance
        FROM thought_vectors tv
        JOIN thoughts t ON t.id = tv.thought_id
        WHERE {where_clause}
        ORDER BY tv.embedding <=> (:query_vec)::vector ASC
        LIMIT :coarse_k
    """

    session = get_data_session()
    try:
        rows = session.execute(sql_text(sql), params).mappings().all()
    except Exception as e:
        logger.exception(f"RETRIEVAL | SQL failed: {e}")
        session.close()
        return []

    # 4) Hybrid scoring v Pythonu (clearer + flexible)
    candidates: list[dict] = []
    for r in rows:
        # Cosine distance je 0..2, similarity = 1 - dist/2 (range 0..1)
        similarity = max(0.0, 1.0 - float(r["distance"]) / 2.0)

        is_diary = bool(r["is_diary"])
        status = r["status"]
        created_at = r["created_at"]
        certainty = int(r["certainty"] or 50)

        # Mode filter (work skip diary uz je v SQL; tady mozna jeste nuance)
        skip, mode_boost = _calc_mode_modifier(is_diary, mode)
        if skip:
            continue

        recency = _calc_recency(created_at, is_diary, status)
        certainty_factor = max(0.1, certainty / 100.0)  # min 0.1, ne 0
        priority = LAYER_PRIORITY["thought"]
        entity_boost = _calc_entity_boost(
            entity_user_ids=list(r["entity_user_ids"] or []),
            entity_tenant_ids=list(r["entity_tenant_ids"] or []),
            entity_project_ids=list(r["entity_project_ids"] or []),
            current_user_id=user_id,
            current_tenant_id=tenant_id,
            current_project_id=project_id,
        )
        freshness = _calc_freshness_bonus(created_at)
        diary_boost = mode_boost  # personal mode + is_diary

        base = similarity * priority * recency * certainty_factor
        score = base + entity_boost + freshness + diary_boost

        candidates.append({
            "thought_id": r["thought_id"],
            "content": r["content"],
            "type": r["thought_type"],
            "status": status,
            "certainty": certainty,
            "is_diary": is_diary,
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
            "author_persona_id": r["author_persona_id"],
            "entity_user_ids": list(r["entity_user_ids"] or []),
            "entity_tenant_ids": list(r["entity_tenant_ids"] or []),
            "similarity": round(similarity, 4),
            "score": round(score, 4),
            "score_breakdown": {
                "similarity": round(similarity, 4),
                "priority": priority,
                "recency": recency,
                "certainty_factor": round(certainty_factor, 4),
                "entity_boost": entity_boost,
                "freshness_bonus": freshness,
                "diary_boost": diary_boost,
            },
        })

    session.close()

    # 5) Sort by hybrid score (desc), top K
    candidates.sort(key=lambda c: c["score"], reverse=True)
    top_k = candidates[:k]

    logger.info(
        f"RETRIEVAL | mode={mode} | persona={persona_id} | tenant={tenant_id} | "
        f"is_parent={is_parent} | coarse={len(rows)} | returned={len(top_k)} | "
        f"top_score={top_k[0]['score'] if top_k else 0:.3f}"
    )

    return top_k


__all__ = [
    "retrieve_relevant_memories",
    "LAYER_PRIORITY",
]
