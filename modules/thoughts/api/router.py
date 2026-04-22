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

    try:
        items = thoughts_service.list_thoughts_for_entity(
            entity_type=about_type,
            entity_id=about_id,
            status_filter=status,
            limit=limit,
            tenant_scope=tenant_id,
        )
    except ThoughtValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "items": items,
        "about_type": about_type,
        "about_id": about_id,
        "status_filter": status,
        "tenant_id": tenant_id,
    }


# ── POZOR na ordering: routes s literalnim path (napr. /_tree, /_meta/enums)
#    MUSI byt registrovane PRED /{thought_id} routami. Jinak FastAPI
#    matchne "_tree" jako thought_id (int), dostane string -> 422. ──

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

    items = thoughts_service.tree_overview(tenant_scope=tenant_id)
    return {"items": items, "tenant_id": tenant_id}


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


@router.get("/{thought_id}")
def get_thought_endpoint(thought_id: int, req: Request):
    """Detail jedne myslenky vcetne entity_links."""
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    t = thoughts_service.get_thought(thought_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")

    # Tenant izolace: pokud myslenka ma scope, musi se shodovat s current tenant
    # nebo byt universal (NULL). Cross-tenant role (rodic) prijde v Faze 3.
    scope = t.get("tenant_scope")
    if scope is not None and scope != tenant_id:
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
    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id:
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

    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id:
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

    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id:
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

    existing = thoughts_service.get_thought(thought_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    scope = existing.get("tenant_scope")
    if scope is not None and scope != tenant_id:
        raise HTTPException(status_code=403, detail="Myslenka neni v tvem tenantu.")

    result = thoughts_service.demote_thought(thought_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Myslenka id={thought_id} neexistuje")
    return result


