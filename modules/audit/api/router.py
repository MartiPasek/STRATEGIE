"""
Audit log admin API.

Endpoint pro superadmina (Marti) -- co se v systemu dela. Obecny user
nevidi (security through obscurity + chrana soukromi ostatnich userů).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from core.database_core import get_core_session
from core.logging import get_logger
from modules.audit.application.service import list_recent_events
from modules.core.infrastructure.models_core import User

logger = get_logger("audit.api")

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def _require_superadmin(req: Request) -> int:
    """Vyzaduje prihlaseneho superadmina. Vraci user_id nebo 401/403."""
    uid_str = req.cookies.get("user_id")
    if not uid_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(uid_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    # Superadmin check pres modules/personas (centralni definice)
    from modules.personas.application.service import _is_superadmin
    if not _is_superadmin(user_id):
        raise HTTPException(status_code=403, detail="Audit log smi videt jen superadmin.")

    return user_id


@router.get("")
def list_audit(
    req: Request,
    limit: int = 100,
    action: str | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
    entity_type: str | None = None,
) -> dict:
    """
    Vraci posledni audit events. Defaultne 100, max 500.

    Query parametry pro filtrovani:
      action       -- presny match akce ('login_success', 'document_uploaded', ...)
      user_id      -- jen eventy daneho usera
      tenant_id    -- jen eventy v danem tenantu
      entity_type  -- 'auth' / 'rag' / 'invite' / 'analysis' / 'conversation' / 'action'
    """
    _require_superadmin(req)
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit musi byt 1..500")

    events = list_recent_events(
        limit=limit,
        action_filter=action,
        user_id_filter=user_id,
        tenant_id_filter=tenant_id,
        entity_type_filter=entity_type,
    )

    # Obohaceni o user info pro UI (jmeno + email pro zobrazeni)
    user_ids = {e["user_id"] for e in events if e["user_id"]}
    user_info: dict[int, dict] = {}
    if user_ids:
        cs = get_core_session()
        try:
            users = cs.query(User).filter(User.id.in_(user_ids)).all()
            for u in users:
                full = " ".join(filter(None, [u.first_name, u.last_name])).strip()
                user_info[u.id] = {
                    "name": full or u.short_name or f"#{u.id}",
                    "status": u.status,
                }
        finally:
            cs.close()

    for e in events:
        if e["user_id"] and e["user_id"] in user_info:
            e["user_name"] = user_info[e["user_id"]]["name"]
        else:
            e["user_name"] = None

    return {"events": events, "count": len(events)}
