"""
Auto-send consent router -- REST API pro sprave trvalych souhlasu
s odesilanim emailu/SMS bez potvrzeni (Phase 7).

Governance:
  - GET /api/v1/auto-send-consents  -- read-only, dostupne vsem uzivatelum
    (transparency: kazdy vidi, komu Marti muze posilat bez ptani).
  - POST, DELETE -- pouze rodice (is_marti_parent=True).
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.logging import get_logger
from modules.notifications.application import consent_service
from modules.thoughts.application.service import is_marti_parent

logger = get_logger("consent.api")

router = APIRouter(prefix="/api/v1/auto-send-consents", tags=["auto-send-consents"])


def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


class GrantRequest(BaseModel):
    channel: str                                  # email | sms
    target_user_id: int | None = None
    target_contact: str | None = None
    note: str | None = None


# ── GET: list aktivnich consentu (read-only pro vsechny) ───────────────────

@router.get("")
def list_consents(req: Request, include_revoked: bool = False, limit: int = 200):
    _get_uid(req)   # require login, ale nerequire parent
    try:
        if include_revoked:
            items = consent_service.list_all_consents(include_revoked=True, limit=limit)
        else:
            items = consent_service.list_active_consents()
        return {"items": items, "count": len(items)}
    except Exception as e:
        logger.exception(f"LIST CONSENTS | failed | {e}")
        raise HTTPException(status_code=500, detail=f"Chyba: {e}")


# ── POST: grant (jen rodice) ───────────────────────────────────────────────

@router.post("")
def grant(req: Request, body: GrantRequest):
    uid = _get_uid(req)
    if not is_marti_parent(uid):
        raise HTTPException(
            status_code=403,
            detail="Souhlas muze udelit jen rodic (is_marti_parent=True).",
        )
    try:
        result = consent_service.grant_consent(
            granted_by_user_id=uid,
            channel=body.channel,
            target_user_id=body.target_user_id,
            target_contact=body.target_contact,
            note=body.note,
        )
        return result
    except consent_service.ConsentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"GRANT | failed | {e}")
        raise HTTPException(status_code=500, detail=f"Chyba: {e}")


# ── DELETE: revoke (jen rodice) ────────────────────────────────────────────

@router.delete("/{consent_id}")
def revoke(req: Request, consent_id: int):
    uid = _get_uid(req)
    if not is_marti_parent(uid):
        raise HTTPException(
            status_code=403,
            detail="Odvolani souhlasu muze provest jen rodic.",
        )
    try:
        # channel nepotrebujeme, consent_id staci
        result = consent_service.revoke_consent(
            revoked_by_user_id=uid,
            channel="email",   # default, nebude pouzit protoze consent_id je zadany
            consent_id=consent_id,
        )
        if result.get("status") == "no_active_consent":
            raise HTTPException(status_code=404, detail="Consent nenalezen nebo jiz odvolan.")
        return result
    except consent_service.ConsentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"REVOKE | failed | {e}")
        raise HTTPException(status_code=500, detail=f"Chyba: {e}")
