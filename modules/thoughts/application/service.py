"""
Marti Memory -- thoughts service (Faze 1).

Zakladni CRUD nad Thought + ThoughtEntityLink tabulkami. Bez promoce,
bez certainty logiky, bez rodicovske role, bez active learning --
tohle je pouze datova vrstva, ktera Fazi 1 umozni:

  - Marti v chatu zavola AI tool `record_thought` -> create_thought()
  - User v UI otevre "Pamet o mne" -> list_thoughts_for_entity()

Pozdejsi faze pridaji:
  Faze 2: promoce note -> knowledge, strom s rozbalovanim, bulk akce
  Faze 3: certainty weighting, auto-promoce >=80, trust rating
  Faze 4: active learning (otazky od Marti), rodicovska role
  Faze 5: Martiho diar, cross-tenant pravidla

Design rozhodnuti -- viz docs/marti_memory_design.md.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from core.database_data import get_data_session
from core.logging import get_logger
from modules.core.infrastructure.models_data import Thought, ThoughtEntityLink

logger = get_logger("thoughts.service")


# ── Konstanty ─────────────────────────────────────────────────────────────

VALID_TYPES = {"fact", "todo", "observation", "question", "goal", "experience"}
VALID_ENTITY_TYPES = {"user", "persona", "tenant", "project"}
VALID_STATUSES = {"note", "knowledge"}
VALID_SOURCE_EVENT_TYPES = {
    "conversation", "email", "sms", "manual", "ai_inferred",
}


class ThoughtError(Exception):
    """Baseline chyba pri praci s myslenkami."""


class ThoughtValidationError(ThoughtError):
    """Neplatny vstup (chybny typ, prazdny content, neznama entita, ...)."""


# ── Create ─────────────────────────────────────────────────────────────────

def create_thought(
    *,
    content: str,
    type: str = "fact",
    entity_links: list[dict[str, Any]] | None = None,
    primary_parent_id: int | None = None,
    tenant_scope: int | None = None,
    author_user_id: int | None = None,
    author_persona_id: int | None = None,
    source_event_type: str | None = None,
    source_event_id: int | None = None,
    certainty: int = 50,
    status: str = "note",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Vytvori novou myslenku + volitelne entity_links.

    Args:
      content: vlastni text myslenky (required, non-empty)
      type: fact | todo | observation | question | goal | experience
      entity_links: list dictu {entity_type, entity_id} -- myslenka se
                    vztahuje k temto entitam. Napr. pro myslenku o Petrovi
                    a projektu STRATEGIE:
                    [{"entity_type": "user", "entity_id": petr_id},
                     {"entity_type": "project", "entity_id": strategie_id}]
      primary_parent_id: volitelne, id nadrazene myslenky ve stromu
      tenant_scope: kde myslenka "platti" (NULL = universal)
      author_user_id / author_persona_id: kdo to zapsal
      source_event_type / source_event_id: z jake udalosti vzesla
                    (napr. source_event_type='conversation', source_event_id=42)
      certainty: 0-100 (default 50 -- mid-range, ceka na overeni)
      status: note (default) | knowledge
      meta: type-specific fields jako dict, ulozi se jako JSON

    Returns:
      dict s nove vytvorenou myslenkou (vcetne id + entity_links).

    Raises: ThoughtValidationError pri neplatnem vstupu.
    """
    content_clean = (content or "").strip()
    if not content_clean:
        raise ThoughtValidationError("prazdny content")
    if type not in VALID_TYPES:
        raise ThoughtValidationError(
            f"neznamy type '{type}' (valid: {', '.join(sorted(VALID_TYPES))})"
        )
    if status not in VALID_STATUSES:
        raise ThoughtValidationError(
            f"neznamy status '{status}' (valid: {', '.join(sorted(VALID_STATUSES))})"
        )
    if source_event_type and source_event_type not in VALID_SOURCE_EVENT_TYPES:
        raise ThoughtValidationError(
            f"neznamy source_event_type '{source_event_type}'"
        )
    if not (0 <= certainty <= 100):
        raise ThoughtValidationError(
            f"certainty mimo rozsah 0-100: {certainty}"
        )

    # Validuj entity_links pred zapisem, aby pri chybe nevznikl "polosirotek"
    # (thought bez linku).
    cleaned_links: list[dict[str, Any]] = []
    for link in (entity_links or []):
        et = link.get("entity_type")
        eid = link.get("entity_id")
        if et not in VALID_ENTITY_TYPES:
            raise ThoughtValidationError(
                f"neznamy entity_type '{et}' v entity_links "
                f"(valid: {', '.join(sorted(VALID_ENTITY_TYPES))})"
            )
        if not isinstance(eid, int) or eid <= 0:
            raise ThoughtValidationError(
                f"neplatne entity_id '{eid}' pro {et}"
            )
        cleaned_links.append({"entity_type": et, "entity_id": eid})

    meta_json = json.dumps(meta, ensure_ascii=False) if meta else None

    ds = get_data_session()
    try:
        t = Thought(
            content=content_clean,
            type=type,
            status=status,
            certainty=certainty,
            primary_parent_id=primary_parent_id,
            tenant_scope=tenant_scope,
            author_user_id=author_user_id,
            author_persona_id=author_persona_id,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            meta=meta_json,
        )
        ds.add(t)
        ds.flush()   # potrebuju id pro entity_links

        for link in cleaned_links:
            ds.add(ThoughtEntityLink(
                thought_id=t.id,
                entity_type=link["entity_type"],
                entity_id=link["entity_id"],
            ))

        ds.commit()
        ds.refresh(t)

        logger.info(
            f"THOUGHT | created | id={t.id} | type={type} | status={status} | "
            f"certainty={certainty} | author_user={author_user_id} | "
            f"author_persona={author_persona_id} | tenant={tenant_scope} | "
            f"links={len(cleaned_links)}"
        )
        return _thought_to_dict(t, entity_links=cleaned_links)
    finally:
        ds.close()


# ── Read ───────────────────────────────────────────────────────────────────

def get_thought(thought_id: int, include_deleted: bool = False) -> dict[str, Any] | None:
    """Nacte jednu myslenku vcetne entity_links. None kdyz neexistuje nebo smazana."""
    ds = get_data_session()
    try:
        q = ds.query(Thought).filter(Thought.id == thought_id)
        if not include_deleted:
            q = q.filter(Thought.deleted_at.is_(None))
        t = q.first()
        if t is None:
            return None

        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id == t.id)
            .all()
        )
        return _thought_to_dict(t, entity_links=[
            {"entity_type": l.entity_type, "entity_id": l.entity_id}
            for l in links
        ])
    finally:
        ds.close()


def list_thoughts_for_entity(
    *,
    entity_type: str,
    entity_id: int,
    status_filter: str | None = None,   # 'note' | 'knowledge' | None (oboje)
    limit: int = 50,
    tenant_scope: int | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    """
    Vrati myslenky vazane k dane entite. Razeni: nejnovejsi nahore
    (created_at DESC).

    Args:
      entity_type: user | persona | tenant | project
      entity_id: id entity v nativni tabulce (css_db users / personas /
                 tenants / projects)
      status_filter: 'note' (jen poznamky), 'knowledge' (jen znalosti),
                     None = oboje
      limit: max pocet vysledku (max 200)
      tenant_scope: pokud zadano, filtruje myslenky s matching tenant_scope
                    (nebo NULL = universal). Pouziva se pro tenant izolaci.
      include_deleted: pokud True, vrati i soft-deleted (default False)

    Returns:
      List dictu, kazdy dict reprezentuje jednu myslenku.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ThoughtValidationError(
            f"neznamy entity_type '{entity_type}'"
        )
    if status_filter is not None and status_filter not in VALID_STATUSES:
        raise ThoughtValidationError(
            f"neznamy status_filter '{status_filter}'"
        )

    ds = get_data_session()
    try:
        # Join pres entity_links -> thoughts
        q = (
            ds.query(Thought)
            .join(
                ThoughtEntityLink,
                ThoughtEntityLink.thought_id == Thought.id,
            )
            .filter(
                ThoughtEntityLink.entity_type == entity_type,
                ThoughtEntityLink.entity_id == entity_id,
            )
        )
        if not include_deleted:
            q = q.filter(Thought.deleted_at.is_(None))
        if status_filter:
            q = q.filter(Thought.status == status_filter)
        if tenant_scope is not None:
            # Myslenky z daneho tenantu + universal (NULL scope, napr. Martiho diar)
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )

        rows = (
            q.order_by(Thought.created_at.desc())
             .limit(max(1, min(limit, 200)))
             .all()
        )

        # Batch fetch entity_links pro vsechny vracene myslenky (vyhneme N+1)
        if rows:
            ids = [r.id for r in rows]
            links = (
                ds.query(ThoughtEntityLink)
                .filter(ThoughtEntityLink.thought_id.in_(ids))
                .all()
            )
            links_by_thought: dict[int, list[dict[str, Any]]] = {}
            for l in links:
                links_by_thought.setdefault(l.thought_id, []).append({
                    "entity_type": l.entity_type,
                    "entity_id": l.entity_id,
                })
        else:
            links_by_thought = {}

        return [
            _thought_to_dict(r, entity_links=links_by_thought.get(r.id, []))
            for r in rows
        ]
    finally:
        ds.close()


# ── Update ─────────────────────────────────────────────────────────────────

def update_thought(
    thought_id: int,
    *,
    content: str | None = None,
    certainty: int | None = None,
    status: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Updatne vybrana pole myslenky. Jen specifikovana pole se zmeni (partial update).
    Zaroven nastavi modified_at = now.

    Vraci updated dict, nebo None kdyz myslenka neexistuje / je smazana.
    """
    if certainty is not None and not (0 <= certainty <= 100):
        raise ThoughtValidationError(f"certainty mimo rozsah 0-100: {certainty}")
    if status is not None and status not in VALID_STATUSES:
        raise ThoughtValidationError(f"neznamy status '{status}'")

    ds = get_data_session()
    try:
        t = (
            ds.query(Thought)
            .filter(Thought.id == thought_id, Thought.deleted_at.is_(None))
            .first()
        )
        if t is None:
            return None

        changed = False
        if content is not None:
            cc = (content or "").strip()
            if not cc:
                raise ThoughtValidationError("prazdny content")
            t.content = cc
            changed = True
        if certainty is not None and certainty != t.certainty:
            t.certainty = certainty
            changed = True
        if status is not None and status != t.status:
            t.status = status
            changed = True
        if meta is not None:
            t.meta = json.dumps(meta, ensure_ascii=False)
            changed = True

        if changed:
            t.modified_at = datetime.now(timezone.utc)
            ds.commit()
            ds.refresh(t)
            logger.info(
                f"THOUGHT | updated | id={thought_id} | fields="
                + ",".join(filter(None, [
                    "content" if content is not None else None,
                    "certainty" if certainty is not None else None,
                    "status" if status is not None else None,
                    "meta" if meta is not None else None,
                ]))
            )

        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id == t.id)
            .all()
        )
        return _thought_to_dict(t, entity_links=[
            {"entity_type": l.entity_type, "entity_id": l.entity_id}
            for l in links
        ])
    finally:
        ds.close()


def promote_thought(thought_id: int) -> dict[str, Any] | None:
    """
    Povysi myslenku ze stavu 'note' do 'knowledge'. Idempotentni -- kdyz
    uz je knowledge, vrati aktualni data bez zmeny.

    Returns: updated thought dict (stejny format jako update_thought),
             None pokud myslenka neexistuje / je smazana.
    """
    ds = get_data_session()
    try:
        t = (
            ds.query(Thought)
            .filter(Thought.id == thought_id, Thought.deleted_at.is_(None))
            .first()
        )
        if t is None:
            return None
        if t.status == "knowledge":
            logger.info(f"THOUGHT | promote | id={thought_id} | uz bylo knowledge")
        else:
            t.status = "knowledge"
            t.modified_at = datetime.now(timezone.utc)
            ds.commit()
            ds.refresh(t)
            logger.info(f"THOUGHT | promoted | id={thought_id} | note -> knowledge")

        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id == t.id)
            .all()
        )
        return _thought_to_dict(t, entity_links=[
            {"entity_type": l.entity_type, "entity_id": l.entity_id}
            for l in links
        ])
    finally:
        ds.close()


def demote_thought(thought_id: int) -> dict[str, Any] | None:
    """
    Degraduje myslenku z 'knowledge' zpet do 'note'. Pouzije se napr. kdyz
    se ukaze, ze fakt byl mylny nebo uz neplatí a chceme ho ponechat jako
    poznamku k dalsimu overeni. Idempotentni.

    Returns: updated thought dict, None pokud neexistuje / smazana.
    """
    ds = get_data_session()
    try:
        t = (
            ds.query(Thought)
            .filter(Thought.id == thought_id, Thought.deleted_at.is_(None))
            .first()
        )
        if t is None:
            return None
        if t.status == "note":
            logger.info(f"THOUGHT | demote | id={thought_id} | uz bylo note")
        else:
            t.status = "note"
            t.modified_at = datetime.now(timezone.utc)
            ds.commit()
            ds.refresh(t)
            logger.info(f"THOUGHT | demoted | id={thought_id} | knowledge -> note")

        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id == t.id)
            .all()
        )
        return _thought_to_dict(t, entity_links=[
            {"entity_type": l.entity_type, "entity_id": l.entity_id}
            for l in links
        ])
    finally:
        ds.close()


def find_thought_by_text(
    query: str,
    *,
    tenant_scope: int | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fulltext-podobne hledani myslenek podle substring matche v content.
    Pouziva se AI toolem `promote_thought(query=...)` kdyz AI nezna id,
    ale ma popis myslenky.

    Case-insensitive substring match. Jednoduche -- bez relevance scoringu.
    V Fazi 3+ muzeme nahradit embedding search.

    tenant_scope pro tenant izolaci (zahrnuje i universal/NULL scope).
    Filtruje deleted_at IS NULL.
    """
    query_clean = (query or "").strip()
    if not query_clean:
        return []

    ds = get_data_session()
    try:
        q = ds.query(Thought).filter(
            Thought.deleted_at.is_(None),
            Thought.content.ilike(f"%{query_clean}%"),
        )
        if tenant_scope is not None:
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )
        rows = (
            q.order_by(Thought.modified_at.desc().nulls_last(), Thought.created_at.desc())
             .limit(max(1, min(limit, 20)))
             .all()
        )
        if not rows:
            return []

        ids = [r.id for r in rows]
        links = (
            ds.query(ThoughtEntityLink)
            .filter(ThoughtEntityLink.thought_id.in_(ids))
            .all()
        )
        links_by_thought: dict[int, list[dict[str, Any]]] = {}
        for l in links:
            links_by_thought.setdefault(l.thought_id, []).append({
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
            })

        return [
            _thought_to_dict(r, entity_links=links_by_thought.get(r.id, []))
            for r in rows
        ]
    finally:
        ds.close()


def tree_overview(
    tenant_scope: int | None = None,
    include_empty_entities: bool = False,
) -> list[dict[str, Any]]:
    """
    Vrati strukturu pro UI strom v "Pamet Marti" modalu:
      [
        {
          "entity_type": "user",
          "entity_id": 1,
          "note_count": 3,
          "knowledge_count": 1,
          "total_count": 4,
        },
        ...
      ]

    Razeno podle entity_type a total_count DESC (nejaktivnejsi entity prvni).
    Filtr: jen entity, kterich se dotyka aspon jedna myslenka v aktualnim
    tenant scope (nebo universal).

    Pozn.: metoda vraci hrube ID; frontend si doplni jmeno entity z
    existujicich caches (currentUser, personasCache, projectsCache, ...).
    """
    from sqlalchemy import case, func

    ds = get_data_session()
    try:
        q = (
            ds.query(
                ThoughtEntityLink.entity_type,
                ThoughtEntityLink.entity_id,
                func.sum(case((Thought.status == "note", 1), else_=0)).label("note_count"),
                func.sum(case((Thought.status == "knowledge", 1), else_=0)).label("knowledge_count"),
                func.count(Thought.id).label("total_count"),
            )
            .join(Thought, Thought.id == ThoughtEntityLink.thought_id)
            .filter(Thought.deleted_at.is_(None))
        )
        if tenant_scope is not None:
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )
        rows = (
            q.group_by(ThoughtEntityLink.entity_type, ThoughtEntityLink.entity_id)
             .order_by(
                 ThoughtEntityLink.entity_type.asc(),
                 func.count(Thought.id).desc(),
             )
             .all()
        )
        return [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "note_count": int(r.note_count or 0),
                "knowledge_count": int(r.knowledge_count or 0),
                "total_count": int(r.total_count or 0),
            }
            for r in rows
        ]
    finally:
        ds.close()


def soft_delete_thought(thought_id: int) -> bool:
    """
    Oznaci myslenku jako smazanou (deleted_at = now). Entity links nemazeme
    (pro audit). Vraci True pri uspechu, False kdyz myslenka neexistuje
    nebo uz byla smazana.
    """
    ds = get_data_session()
    try:
        t = (
            ds.query(Thought)
            .filter(Thought.id == thought_id, Thought.deleted_at.is_(None))
            .first()
        )
        if t is None:
            return False
        t.deleted_at = datetime.now(timezone.utc)
        ds.commit()
        logger.info(f"THOUGHT | soft deleted | id={thought_id}")
        return True
    finally:
        ds.close()


# ── Helpers ────────────────────────────────────────────────────────────────

def add_entity_link(
    thought_id: int,
    entity_type: str,
    entity_id: int,
) -> bool:
    """
    Pridani dodatecneho entity linku k existujici myslence. Idempotent --
    pokud link uz existuje (unique constraint), tise projdeme.

    Vraci True kdyz link vznikl nove, False kdyz uz existoval.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ThoughtValidationError(f"neznamy entity_type '{entity_type}'")

    ds = get_data_session()
    try:
        try:
            ds.add(ThoughtEntityLink(
                thought_id=thought_id,
                entity_type=entity_type,
                entity_id=entity_id,
            ))
            ds.commit()
            return True
        except IntegrityError:
            ds.rollback()
            return False
    finally:
        ds.close()


def _thought_to_dict(t: Thought, entity_links: list[dict[str, Any]]) -> dict[str, Any]:
    """Zobrazitelna podoba myslenky pro API / UI / AI tool."""
    meta_parsed: Any = None
    if t.meta:
        try:
            meta_parsed = json.loads(t.meta)
        except Exception:
            # Defensive -- v DB jsou divna data? Vratime raw string.
            meta_parsed = t.meta
    return {
        "id": t.id,
        "content": t.content,
        "type": t.type,
        "status": t.status,
        "certainty": t.certainty,
        "primary_parent_id": t.primary_parent_id,
        "tenant_scope": t.tenant_scope,
        "author_user_id": t.author_user_id,
        "author_persona_id": t.author_persona_id,
        "source_event_type": t.source_event_type,
        "source_event_id": t.source_event_id,
        "meta": meta_parsed,
        "entity_links": entity_links,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "modified_at": t.modified_at.isoformat() if t.modified_at else None,
        "deleted_at": t.deleted_at.isoformat() if t.deleted_at else None,
    }
