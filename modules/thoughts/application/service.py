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

# Certainty threshold pro auto-promoci note -> knowledge (Faze 3).
# Viz docs/marti_memory_design.md, rozhodnuti #3.
PROMOTE_THRESHOLD = 80

# Defaultni certainty pro myslenku bez zname author_user_id trust_rating.
# Neutralni -- Marti si neni ani jista ani nejista.
DEFAULT_CERTAINTY = 50


class ThoughtError(Exception):
    """Baseline chyba pri praci s myslenkami."""


class ThoughtValidationError(ThoughtError):
    """Neplatny vstup (chybny typ, prazdny content, neznama entita, ...)."""


# ── Certainty engine (Faze 3) ────────────────────────────────────────────

def calculate_initial_certainty(author_user_id: int | None) -> int:
    """
    Odvodi initial certainty z trust_rating autora. Pouziva se v
    create_thought, kdyz user explicitne nenastavi certainty.

    Mapovani trust_rating -> certainty:
      trust_rating 100 (rodic)     -> certainty 90 (auto-promote kandidat)
      trust_rating 80  (trusted)   -> certainty 70
      trust_rating 50  (default)   -> certainty 50
      trust_rating 20  (low)       -> certainty 25
      trust_rating 0               -> certainty 10

    Linearni scaling s mirnym boostem u high-trust:
      certainty = trust_rating * 0.8 + 10
      (trust=100 -> certainty=90, trust=50 -> certainty=50, trust=0 -> certainty=10)

    Kdyz author_user_id je None (AI-inferred, systemove), vrati
    DEFAULT_CERTAINTY (50).
    """
    if not author_user_id:
        return DEFAULT_CERTAINTY

    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            u = cs.query(User).filter_by(id=author_user_id).first()
            if u is None:
                return DEFAULT_CERTAINTY
            trust = u.trust_rating if u.trust_rating is not None else 50
        finally:
            cs.close()
        calculated = int(trust * 0.8 + 10)
        return max(0, min(100, calculated))
    except Exception as e:
        logger.warning(f"THOUGHT | certainty calc failed: {e}")
        return DEFAULT_CERTAINTY


def is_marti_parent(user_id: int | None) -> bool:
    """
    Zjisti, zda user ma rodicovskou roli. Pouziva se pro cross-tenant
    retrieval (rodic vidi vsechny tenanty) a active learning pool (Faze 4).

    Defensive -- pri chybe vraci False (bezpecne: default = nemas cross-tenant pristup).
    """
    if not user_id:
        return False
    try:
        from core.database_core import get_core_session
        from modules.core.infrastructure.models_core import User
        cs = get_core_session()
        try:
            u = cs.query(User).filter_by(id=user_id).first()
            return bool(u and u.is_marti_parent)
        finally:
            cs.close()
    except Exception as e:
        logger.warning(f"THOUGHT | is_marti_parent check failed: {e}")
        return False


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
    certainty: int | None = None,
    status: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Vytvori novou myslenku + volitelne entity_links.

    Args:
      content: vlastni text myslenky (required, non-empty)
      type: fact | todo | observation | question | goal | experience
      entity_links: list dictu {entity_type, entity_id} -- myslenka se
                    vztahuje k temto entitam.
      primary_parent_id: volitelne, id nadrazene myslenky ve stromu
      tenant_scope: kde myslenka "platti" (NULL = universal)
      author_user_id / author_persona_id: kdo to zapsal
      source_event_type / source_event_id: z jake udalosti vzesla
      certainty: 0-100. Kdyz None, odvodi se z trust_rating author_user_id
                 (Faze 3 certainty engine). Default chovani = automatika.
      status: note | knowledge. Kdyz None, urci se podle certainty:
              >= PROMOTE_THRESHOLD -> knowledge (auto-promote), jinak note.
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
    if source_event_type and source_event_type not in VALID_SOURCE_EVENT_TYPES:
        raise ThoughtValidationError(
            f"neznamy source_event_type '{source_event_type}'"
        )

    # Certainty engine (Faze 3): kdyz None, odvodi z trust_rating.
    if certainty is None:
        certainty = calculate_initial_certainty(author_user_id)
    if not (0 <= certainty <= 100):
        raise ThoughtValidationError(
            f"certainty mimo rozsah 0-100: {certainty}"
        )

    # Auto-promote: kdyz status neni explicitni a certainty >= threshold,
    # rovnou knowledge. Jinak fallback na 'note'.
    if status is None:
        status = "knowledge" if certainty >= PROMOTE_THRESHOLD else "note"
    if status not in VALID_STATUSES:
        raise ThoughtValidationError(
            f"neznamy status '{status}' (valid: {', '.join(sorted(VALID_STATUSES))})"
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

        # Faze 13a: index thought do thought_vectors (RAG memory).
        # Best effort -- pri chybe Voyage jen warning, nesho create_thought.
        # Volame az po commit (index_thought si otevre vlastni session).
        _new_id = t.id
        _hook_index_thought(_new_id)

        return _thought_to_dict(t, entity_links=cleaned_links)
    finally:
        ds.close()


def _hook_index_thought(thought_id: int) -> None:
    """
    Best-effort hook: indexuje nove vytvorenou nebo upravenou thought do
    thought_vectors. Pri chybe Voyage / DB jen warning, parent flow nesho.

    Faze 13a (Marti Memory v2 RAG).
    """
    try:
        from modules.thoughts.application import embedding_service as _es
        _es.index_thought(thought_id, force=True)
    except Exception as _e:
        logger.warning(f"THOUGHT | RAG index hook failed | thought_id={thought_id} | {_e}")


def _hook_delete_vector(thought_id: int) -> None:
    """Best-effort hook: smaze vector pri soft_delete_thought."""
    try:
        from modules.thoughts.application import embedding_service as _es
        _es.delete_vector(thought_id)
    except Exception as _e:
        logger.warning(f"THOUGHT | RAG delete hook failed | thought_id={thought_id} | {_e}")


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
    bypass_tenant_scope: bool = False,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    """
    Vrati myslenky vazane k dane entite. Razeni: nejnovejsi nahore
    (created_at DESC).

    Args:
      entity_type: user | persona | tenant | project
      entity_id: id entity v nativni tabulce
      status_filter: 'note' / 'knowledge' / None (oboje)
      limit: max pocet vysledku (max 200)
      tenant_scope: pokud zadano, filtruje myslenky s matching tenant_scope
                    (nebo NULL = universal).
      bypass_tenant_scope: pokud True, tenant_scope filter se VUBEC nepouzije
                           a user vidi myslenky napric vsemi tenanty.
                           POUZIVAT VYHRADNE u rodicu (is_marti_parent=True).
                           Ochrana tenant izolace pro bezne useru zustava.
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
        if tenant_scope is not None and not bypass_tenant_scope:
            # Myslenky z daneho tenantu + universal (NULL scope, napr. Martiho diar)
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )
        # bypass_tenant_scope=True -> zadny tenant filter, vse cross-tenant

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
        prev_certainty = t.certainty
        auto_promoted = False

        if content is not None:
            cc = (content or "").strip()
            if not cc:
                raise ThoughtValidationError("prazdny content")
            t.content = cc
            changed = True
        if certainty is not None and certainty != t.certainty:
            t.certainty = certainty
            changed = True
            # Auto-promote (Faze 3): kdyz certainty prekroci threshold
            # a user explicitne nezadal status, povysim automaticky.
            if (
                status is None
                and prev_certainty < PROMOTE_THRESHOLD <= certainty
                and t.status == "note"
            ):
                t.status = "knowledge"
                auto_promoted = True
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
                + (f" | AUTO-PROMOTED (certainty {prev_certainty}→{certainty})" if auto_promoted else "")
            )

            # Faze 13a: reindex po update -- jen pokud se zmenil content nebo
            # meta (status/certainty se v vector denorm cache odrazi taky, ale
            # samotne vector pole se reembeduje jen kvuli content). Konzervativne
            # reindexujeme pri jakekoliv zmene (cost je negligible -- 1 thought).
            _hook_index_thought(thought_id)

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


def list_todos(
    tenant_scope: int | None = None,
    bypass_tenant_scope: bool = False,
    status_filter: str = "all",   # 'open' | 'done' | 'all'
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    Vrati vsechny myslenky type='todo' v tenant scope. Razeni:
      - open first (meta.done != true)
      - pak podle due_at ASC (kdyz je v meta), jinak created_at DESC

    status_filter:
      'open' -- jen otevrene todo
      'done' -- jen hotove
      'all'  -- obe
    """
    if status_filter not in ("open", "done", "all"):
        raise ThoughtValidationError(f"neznamy status_filter '{status_filter}'")

    ds = get_data_session()
    try:
        q = ds.query(Thought).filter(
            Thought.type == "todo",
            Thought.deleted_at.is_(None),
        )
        if tenant_scope is not None and not bypass_tenant_scope:
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )
        rows = (
            q.order_by(Thought.created_at.desc())
             .limit(max(1, min(limit, 500)))
             .all()
        )
        if not rows:
            return []

        # Fetch entity_links
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

        result = [
            _thought_to_dict(r, entity_links=links_by_thought.get(r.id, []))
            for r in rows
        ]

        # Filtruj podle status (done v meta)
        def _is_done(d: dict) -> bool:
            m = d.get("meta")
            return bool(isinstance(m, dict) and m.get("done"))

        if status_filter == "open":
            result = [d for d in result if not _is_done(d)]
        elif status_filter == "done":
            result = [d for d in result if _is_done(d)]

        # Razeni: otevrene prvni, pak due_at ASC, pak created_at DESC
        def _sort_key(d: dict):
            is_done = _is_done(d)
            m = d.get("meta") or {}
            due_at = m.get("due_at") if isinstance(m, dict) else None
            # (done=True bude drzet dole): (1 pokud done, 0 otevrene), pak due_at
            return (
                1 if is_done else 0,
                due_at or "9999-12-31",
                -int((d.get("id") or 0)),
            )
        result.sort(key=_sort_key)
        return result
    finally:
        ds.close()


def mark_todo_done(thought_id: int, done: bool = True) -> dict[str, Any] | None:
    """
    Oznaci todo jako hotove (meta.done = true). Idempotent.
    done=False vrati zpet do otevreneho stavu.

    Vraci updated thought dict nebo None kdyz neexistuje.
    """
    ds = get_data_session()
    try:
        t = ds.query(Thought).filter_by(id=thought_id, deleted_at=None).first()
        if t is None:
            return None
        if t.type != "todo":
            raise ThoughtValidationError(
                f"myslenka id={thought_id} neni todo (type='{t.type}')"
            )

        # Parsuj existujici meta, updatuj done
        meta_dict: dict[str, Any] = {}
        if t.meta:
            try:
                meta_dict = json.loads(t.meta)
                if not isinstance(meta_dict, dict):
                    meta_dict = {}
            except Exception:
                meta_dict = {}
        meta_dict["done"] = bool(done)
        if done:
            meta_dict["done_at"] = datetime.now(timezone.utc).isoformat()
        else:
            meta_dict.pop("done_at", None)

        t.meta = json.dumps(meta_dict, ensure_ascii=False)
        t.modified_at = datetime.now(timezone.utc)
        ds.commit()
        ds.refresh(t)

        logger.info(
            f"THOUGHT | todo {'done' if done else 'reopened'} | id={thought_id}"
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


def diary_owners_overview() -> list[dict[str, Any]]:
    """
    Vrati persony, ktere maji aspon 1 denikovy zaznam, + pocet.
    Pouziva se pro zobrazeni "Diář Marti" dlazdic na vrchu Paměť Marti modalu.

    Vraci:
      [{"persona_id": 1, "entry_count": 5}, ...]

    Frontend si jmena person doplni z personasCache.
    """
    from sqlalchemy import func

    ds = get_data_session()
    try:
        # Najdi thought entity links pro persony + join na thoughts kde
        # meta obsahuje is_diary marker (jednoducha substring varianta).
        # Nejrychlejsi: vsechny thoughts s author_persona_id = entity_id,
        # tenant_scope NULL, join entity_link, filter obsahu meta.
        rows = (
            ds.query(
                ThoughtEntityLink.entity_id,
                func.count(Thought.id).label("cnt"),
            )
            .join(Thought, Thought.id == ThoughtEntityLink.thought_id)
            .filter(
                ThoughtEntityLink.entity_type == "persona",
                Thought.tenant_scope.is_(None),
                Thought.author_persona_id == ThoughtEntityLink.entity_id,
                Thought.deleted_at.is_(None),
                # Substring match pro marker v meta JSON -- postacuje pro MVP.
                # Pozdeji muzeme pridat dedikovany sloupec nebo JSONB index.
                Thought.meta.ilike('%"is_diary": true%'),
            )
            .group_by(ThoughtEntityLink.entity_id)
            .order_by(func.count(Thought.id).desc())
            .all()
        )
        return [
            {"persona_id": int(r.entity_id), "entry_count": int(r.cnt)}
            for r in rows
        ]
    finally:
        ds.close()


def list_diary_for_persona(
    persona_id: int,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Vrati deníkové záznamy konkretni persony (Martiho diář).

    Deníkový záznam je myšlenka splňující:
      - entity_links obsahuje (persona, persona_id)
      - tenant_scope IS NULL (universal = soukromá, cross-tenant)
      - author_persona_id == persona_id (ta persona si to zapsala sama)
      - meta.is_diary == true (marker pro rozliseni od běžných thoughts o persone)

    Seřazeno od nejnovějšího.

    Tenant izolace: tenant_scope=NULL samo o sobě znamená "universal" — diář
    je mimo tenanty. Retrieval v Paměť Marti modalu respektuje privacy:
    zobrazí se jen rodičům (is_marti_parent=True) a samotné personě (jako
    author).
    """
    ds = get_data_session()
    try:
        rows = (
            ds.query(Thought)
            .join(ThoughtEntityLink, ThoughtEntityLink.thought_id == Thought.id)
            .filter(
                ThoughtEntityLink.entity_type == "persona",
                ThoughtEntityLink.entity_id == persona_id,
                Thought.tenant_scope.is_(None),
                Thought.author_persona_id == persona_id,
                Thought.deleted_at.is_(None),
            )
            .order_by(Thought.created_at.desc())
            .limit(max(1, min(limit, 500)))
            .all()
        )
        if not rows:
            return []

        # Batch fetch entity_links
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

        # Filtruj jen ty, ktere maji meta.is_diary == true (dodatecny marker)
        out: list[dict[str, Any]] = []
        for r in rows:
            d = _thought_to_dict(r, entity_links=links_by_thought.get(r.id, []))
            meta = d.get("meta")
            if isinstance(meta, dict) and meta.get("is_diary"):
                out.append(d)
        return out
    finally:
        ds.close()


def tree_overview(
    tenant_scope: int | None = None,
    bypass_tenant_scope: bool = False,
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
        if tenant_scope is not None and not bypass_tenant_scope:
            q = q.filter(
                or_(
                    Thought.tenant_scope == tenant_scope,
                    Thought.tenant_scope.is_(None),
                )
            )
        # bypass=True -> vse cross-tenant (rodicovska role)
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

        # Faze 13a: smaz vector z RAG (soft delete v thoughts neflowsuje
        # cascade do thought_vectors -- musime explicitne).
        _hook_delete_vector(thought_id)
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
