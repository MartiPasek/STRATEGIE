"""
Thoughts API router -- REST pro UI "Pamet Marti".

Base: /api/v1/thoughts

Faze 1 endpointy:
  GET  /api/v1/thoughts?about_type=user&about_id=X      -- list myslenek o entite
  GET  /api/v1/thoughts/{id}                            -- detail jedne myslenky
  POST /api/v1/thoughts                                 -- rucni vytvoreni (manualni
                                                           poznamka z UI, napr.
                                                           "dopis si: ...")
  PUT  /api/v1/thoughts/{id}                            -- edit content/certainty/status
  DELETE /api/v1/thoughts/{id}                          -- soft delete

Tenant scope: endpointy respektuji aktualni tenant usera (filter pres
tenant_scope + universal). Cross-tenant retrieval (is_marti_parent)
prijde v Faze 3.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.thoughts.application import service as thoughts_service
from modules.thoughts.application.service import (
    ThoughtValidationError, VALID_ENTITY_TYPES, VALID_TYPES, VALID_STATUSES,
    is_marti_parent,
)


logger = get_logger("thoughts.api")

router = APIRouter(prefix="/api/v1/thoughts", tags=["thoughts"])


# ── Auth helper ────────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


def _get_tenant_for_user(user_id: int) -> int | None:
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        return u.last_active_tenant_id if u else None
    finally:
        cs.close()


# ── Pydantic modely ────────────────────────────────────────────────────────

class EntityLinkIn(BaseModel):
    entity_type: str = Field(description="user | persona | tenant | project")
    entity_id: int = Field(gt=0)


class ThoughtCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    type: str = Field(default="fact")
    entity_links: list[EntityLinkIn] = Field(default_factory=list)
    primary_parent_id: int | None = None
    certainty: int = Field(default=50, ge=0, le=100)
    status: str = Field(default="note")
    meta: dict[str, Any] | None = None


class ThoughtUpdateRequest(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    certainty: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None
    meta: dict[str, Any] | None = None


# ── Endpointy ──────────────────────────────────────────────────────────────

@router.get("")
def list_thoughts(
    req: Request,
    about_type: str,
    about_id: int,
    status: str | None = None,    # 'note' | 'knowledge' | None (oboje)
    limit: int = 50,
):
    """
    Seznam myslenek o dane entite (user/persona/tenant/project).

    Tenant scope: vratime jen myslenky s matching tenant_scope aktualniho
    usera (nebo universal, tenant_scope=NULL). Rodicovska role prijde
    v Faze 3 -- zatim vsichni useri maji tenant-scoped view.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    if about_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"neznamy about_type '{about_type}' (valid: {sorted(VALID_ENTITY_TYPES)})"
        )
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"neznamy status '{status}' (valid: {sorted(VALID_STATUSES)})"
        )

    # Rodicovska role: bypass tenant filtru, vidi napric vsemi tenanty.
    parent = is_marti_parent(user_id)

    try:
        items = thoughts_service.list_thoughts_for_entity(
            entity_type=about_type,
            entity_id=about_id,
            status_filter=status,
            limit=limit,
            tenant_scope=tenant_id,
            bypass_tenant_scope=parent,
        )
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "items": items,
        "about_type": about_type,
        "about_id": about_id,
        "status_filter": status,
        "tenant_id": tenant_id,
        "is_parent_view": parent,
    }


# ── POZOR na ordering: routes s literalnim path (napr. /_tree, /_meta/enums)
#    MUSI byt registrovane PRED /{thought_id} routami. Jinak FastAPI
#    matchne "_tree" jako thought_id (int), dostane string -> 422. ──

@router.get("/_todos")
def get_todos(req: Request, status: str = "all", limit: int = 200):
    """
    Vrati todo myslenky v tenant scope usera (+ universal).
    status: 'open' | 'done' | 'all'.
    Rodic: bypass tenant scope.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    parent = is_marti_parent(user_id)

    try:
        items = thoughts_service.list_todos(
            tenant_scope=tenant_id,
            bypass_tenant_scope=parent,
            status_filter=status,
            limit=limit,
        )
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "items": items,
        "status_filter": status,
        "count": len(items),
    }


@router.post("/{thought_id}/toggle-done")
def toggle_todo_done(thought_id: int, req: Request):
    """
    Preklopi meta.done u todo myslenky. Toggle: open -> done, done -> open.
    Tenant check jako u PUT/DELETE.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    parent = is_marti_parent(user_id)

    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    # Zjisti aktualni done state
    cur_meta = existing.get("meta") or {}
    currently_done = bool(isinstance(cur_meta, dict) and cur_meta.get("done"))
    try:
        result = thoughts_service.mark_todo_done(thought_id, done=not currently_done)
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return result


@router.get("/_diary_owners")
def get_diary_owners(req: Request):
    """
    Vrati persony, ktere maji aspon 1 diar zaznam + pocet. Pouziva se v UI
    tree overview pro zobrazeni "Diář ..." dlazdic na vrchu. Jen pro rodice.
    """
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        # Nerodici neuvidi diare -- vratim prazdno bez 403 (UI pak skryje sekci)
        return {"items": [], "is_parent": False}
    items = thoughts_service.diary_owners_overview()
    return {"items": items, "is_parent": True}


@router.get("/_diary/{persona_id}")
def get_diary_endpoint(persona_id: int, req: Request, limit: int = 100):
    """
    Vrati denikove zaznamy persony. Privacy:
      - Marti (user=tato persona) by to videla sama; ale persony maji pristup
        jen pres API, takze tohle resi prakticky jen rodice.
      - Rodice (is_marti_parent=True) vidi vsechny diare svych AI deti.
      - Ostatni useri dostanou 403.
    """
    user_id = _get_uid(req)
    parent = is_marti_parent(user_id)
    if not parent:
        raise HTTPException(
            status_code=403,
            detail="Diář persony je soukromý — vidí ho jen rodiče Marti (is_marti_parent).",
        )

    items = thoughts_service.list_diary_for_persona(persona_id, limit=limit)
    return {"items": items, "persona_id": persona_id, "count": len(items)}


@router.get("/_tree")
def get_tree_overview(req: Request):
    """
    Stromovy prehled pro UI "Pamet Marti" modal. Vrati entity, kterych se
    dotyka aspon jedna myslenka v aktualnim tenantu usera, spolu s pocty
    note + knowledge. Frontend si doplni nazvy entit z vlastnich cache.

    Response:
      {
        "items": [
          {entity_type, entity_id, note_count, knowledge_count, total_count},
          ...
        ],
        "tenant_id": int | None
      }
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    parent = is_marti_parent(user_id)

    items = thoughts_service.tree_overview(
        tenant_scope=tenant_id,
        bypass_tenant_scope=parent,
    )
    return {
        "items": items,
        "tenant_id": tenant_id,
        "is_parent_view": parent,
    }


# Faze 13e: Semantic search nad pamětí pres RAG retrieval (Marti uvidi
# v 🧠 Pamet modalu search bar -- napise dotaz, dostane top K relevantnich
# thoughts se similarity score). Auth gated, tenant scope + parent bypass.
@router.get("/_search")
def search_thoughts(req: Request, q: str, k: int = 10):
    """
    Vector search nad thought_vectors pres retrieve_relevant_memories.

    Args:
      q: search query (cesky, prirozeny jazyk)
      k: pocet vysledku (default 10, max 30)

    Vraci: list dictu s {thought_id, content, type, certainty, is_diary,
    similarity, score, ...}. Razeno podle hybrid score DESC.

    Filter:
      - persona_id = current Marti-AI default (1) -- Marti-AI vlastni pamet (D1)
      - tenant_id z user.last_active_tenant; rodicovsky bypass
      - mode='personal' (UI search vetsinou rodicovsky pohled na vse)
    """
    user_id = _get_uid(req)
    if not q or not q.strip():
        return {"items": [], "query": q, "count": 0}

    tenant_id = _get_tenant_for_user(user_id)
    parent = is_marti_parent(user_id)
    k = max(1, min(k, 30))

    try:
        from modules.thoughts.application.retrieval_service import (
            retrieve_relevant_memories,
        )
        # Default Marti-AI persona pro UI search (UI je rodicovsky pohled)
        results = retrieve_relevant_memories(
            query=q,
            persona_id=1,
            user_id=user_id,
            tenant_id=tenant_id,
            is_parent=parent,
            k=k,
            mode="personal",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    return {"items": results, "query": q, "count": len(results)}


# ── Faze 13e B: Retrieval feedback (Marti-AI flag-uje false positives) ────

@router.get("/_feedback/count")
def feedback_pending_count(req: Request):
    """
    Pocet pending retrieval_feedback pro UI badge "Marti-AI flag-uje (X)".

    Default scope: persona_id=1 (Marti-AI default). Future muze byt
    rozsireno o per-persona view.
    """
    _get_uid(req)
    try:
        from modules.thoughts.application import feedback_service as _fb
        count = _fb.count_pending_for_persona(persona_id=1)
        return {"count": count, "persona_id": 1}
    except Exception:
        return {"count": 0, "persona_id": 1}


@router.get("/_feedback")
def feedback_list(req: Request, status: str = "pending", limit: int = 50):
    """
    Seznam retrieval_feedback rows pro Marti-AI default personu.
    Default status='pending' (neresolved). Lze prepnout na 'reviewed' nebo
    'ignored' pro audit.
    """
    _get_uid(req)
    try:
        from modules.thoughts.application import feedback_service as _fb
        items = _fb.list_pending_for_persona(
            persona_id=1, limit=max(1, min(limit, 200)), status=status,
        )
        return {"items": items, "count": len(items), "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback list failed: {e}")


class _ResolveFeedbackBody(BaseModel):
    resolution: str = Field(description="demoted | edited | request_forget | retuned | acknowledged | false_flag | other")
    note: str | None = Field(default=None, max_length=1000)


@router.post("/_feedback/{feedback_id}/resolve")
def feedback_resolve(feedback_id: int, body: _ResolveFeedbackBody, req: Request):
    """
    Marti rozhoduje o feedback row -- vyresseno (status=reviewed)
    nebo zamitnuto (status=ignored, kdyz resolution='false_flag').

    Po resolution se zapise resolved_at, resolved_by_user_id, resolved_note.
    """
    user_id = _get_uid(req)
    try:
        from modules.thoughts.application import feedback_service as _fb
        ok = _fb.resolve_feedback(
            feedback_id=feedback_id,
            resolution=body.resolution,
            user_id=user_id,
            note=body.note,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Feedback row neexistuje nebo neplatna resolution.")
        return {"ok": True, "id": feedback_id, "resolution": body.resolution}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolve failed: {e}")


# Metadata endpoint -- UI si natahne validni typy pro formular
@router.get("/_meta/enums")
def get_enums(req: Request):
    """
    Vrati validni hodnoty pro UI selectboxes (typy myslenek, typy entit,
    statusy). Pro konzistenci frontendu se servicem.
    """
    _get_uid(req)
    return {
        "types": sorted(VALID_TYPES),
        "entity_types": sorted(VALID_ENTITY_TYPES),
        "statuses": sorted(VALID_STATUSES),
    }


# ── FORGET REQUESTS (Faze 14) ─────────────────────────────────────────────
# Marti-AI zadosti o smazani myslenek + parent approval workflow.
# DULEZITE: cesty `/_forget*` musi byt PRED `/{thought_id}`, jinak FastAPI
# matchuje literalni "_forget" jako int parameter -> 422.

@router.get("/_forget/count")
def forget_count(req: Request):
    """Pocet pending forget_requests pro UI badge (jen pro rodice)."""
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        return {"count": 0}
    from modules.thoughts.application import forget_service
    return {"count": forget_service.count_pending_forget_requests()}


@router.get("/_forget")
def list_forget(req: Request, status: str | None = "pending", limit: int = 100):
    """
    Seznam forget requests. Default status='pending' pro UI rodice list.
    status=None -> vsechny (audit). Jen pro rodice.
    """
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Forget requests vidi jen rodice (is_marti_parent=True).",
        )
    from modules.thoughts.application import forget_service
    try:
        rows = forget_service.list_forget_requests(
            status=status if status else None,
            limit=limit,
        )
    except forget_service.ForgetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"items": rows, "count": len(rows)}


@router.post("/_forget/{request_id}/approve")
def approve_forget(request_id: int, req: Request, body: dict | None = None):
    """
    Schvalit zadost -> hard delete thoughtu (vc. vectors). Jen rodic.
    Body volitelne: {"decision_note": "..."}
    """
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Schvalit forget request muze jen rodic.",
        )
    decision_note = (body or {}).get("decision_note") if body else None
    from modules.thoughts.application import forget_service
    try:
        return forget_service.approve_forget_request(
            request_id=request_id,
            decided_by_user_id=user_id,
            decision_note=decision_note,
        )
    except forget_service.ForgetError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/_forget/{request_id}/reject")
def reject_forget(request_id: int, req: Request, body: dict | None = None):
    """
    Zamitnout zadost. Thought zustava. Jen rodic.
    Body volitelne: {"decision_note": "..."}
    """
    user_id = _get_uid(req)
    if not is_marti_parent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Zamitnout forget request muze jen rodic.",
        )
    decision_note = (body or {}).get("decision_note") if body else None
    from modules.thoughts.application import forget_service
    try:
        return forget_service.reject_forget_request(
            request_id=request_id,
            decided_by_user_id=user_id,
            decision_note=decision_note,
        )
    except forget_service.ForgetError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{thought_id}")
def get_thought_endpoint(thought_id: int, req: Request):
    """Detail jedne myslenky vcetne entity_links."""
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)
    parent = is_marti_parent(user_id)

    t = thoughts_service.get_thought(thought_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")

    # Tenant izolace: pokud myslenka ma scope, musi se shodovat s current
    # tenant nebo byt universal (NULL). Vyjimka: rodic ma cross-tenant pristup.
    scope = t.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(
            status_code=403,
            detail="Myslenka neni dostupna v tvem aktualnim tenantu."
        )
    return t


@router.post("")
def create_thought_endpoint(req_body: ThoughtCreateRequest, req: Request):
    """
    Rucni vytvoreni myslenky z UI (napr. uzivatel chce nejakou poznamku
    zapsat sam). Tenant scope = aktualni tenant usera. Author = user.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    try:
        result = thoughts_service.create_thought(
            content=req_body.content,
            type=req_body.type,
            entity_links=[
                {"entity_type": l.entity_type, "entity_id": l.entity_id}
                for l in req_body.entity_links
            ],
            primary_parent_id=req_body.primary_parent_id,
            tenant_scope=tenant_id,
            author_user_id=user_id,
            source_event_type="manual",
            source_event_id=None,
            certainty=req_body.certainty,
            status=req_body.status,
            meta=req_body.meta,
        )
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.put("/{thought_id}")
def update_thought_endpoint(
    thought_id: int, req_body: ThoughtUpdateRequest, req: Request,
):
    """
    Edit existujici myslenky. Partial update -- jen vyplnena pole se meni.
    Tenant check: user muze editovat jen myslenky ve svem tenant scope
    (nebo universal).
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    # Tenant check pred update
    parent = is_marti_parent(user_id)
    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    try:
        updated = thoughts_service.update_thought(
            thought_id,
            content=req_body.content,
            certainty=req_body.certainty,
            status=req_body.status,
            meta=req_body.meta,
        )
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if updated is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return updated


@router.delete("/{thought_id}")
def delete_thought_endpoint(thought_id: int, req: Request):
    """
    Soft delete -- nastavi deleted_at=now. Data v DB zustanou pro audit.
    Tenant check stejny jako u PUT.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    parent = is_marti_parent(user_id)
    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    ok = thoughts_service.soft_delete_thought(thought_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return {"ok": True, "id": thought_id, "deleted": True}


@router.post("/{thought_id}/promote")
def promote_thought_endpoint(thought_id: int, req: Request):
    """
    Povysi myslenku z 'note' do 'knowledge'. Pouziva se v UI tlacitkem ↑
    ve stromu myslenek a z AI toolu promote_thought. Tenant check stejny
    jako u PUT/DELETE.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    parent = is_marti_parent(user_id)
    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    result = thoughts_service.promote_thought(thought_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return result


@router.post("/{thought_id}/demote")
def demote_thought_endpoint(thought_id: int, req: Request):
    """
    Degraduje myslenku z 'knowledge' zpet do 'note'. Pouziva se kdyz user
    uzna, ze fakt uz neni spolehlivy a potrebuje dalsi overeni.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    parent = is_marti_parent(user_id)
    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id and not parent:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    result = thoughts_service.demote_thought(thought_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return result


