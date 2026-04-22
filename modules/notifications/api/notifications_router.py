"""
Notifications unified router -- agregovana data napric notification typy
(email, SMS, do budoucna pripadne missed calls, DM mentions, ...).

Base: /api/v1/notifications

Pouziva se pro UI badge v hlavicce, ktere zobrazuje jeden globalni counter
pro vsechny nedoreseny provoz (emaily + SMS). Kdyby UI potreboval rozdeleny
counter, muze volat jednotlive /api/v1/sms/ui/unread-counts nebo vlastni
email endpoint.
"""
from fastapi import APIRouter, HTTPException, Request

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.notifications.application import email_inbox_service
from modules.notifications.application import sms_service


logger = get_logger("notifications.api")

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


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


@router.get("/unread-counts")
def get_unread_counts(req: Request):
    """
    Vraci agregovany pocet neprectenych/nezpracovanych notifikaci pro header
    badge:

      {
        "unread_email": 3,
        "unread_sms":   7,
        "total":        10,
        "tenant_id":    42
      }

    Pocty jsou scoped na aktualne aktivni tenant usera. Pri tenant switch
    se cisla automaticky prepocitaji.

    Volano UI pri polling (napr. kazdych 30s). Endpoint je lightweight --
    dve agregovane COUNT(*) dotazy.
    """
    user_id = _get_uid(req)
    tenant_id = _get_tenant_for_user(user_id)

    if tenant_id is None:
        return {
            "unread_email": 0,
            "unread_sms": 0,
            "total": 0,
            "tenant_id": None,
        }

    # Email: suma pres persony, ktere user vidi (global + current tenant).
    unread_email = email_inbox_service.count_unread_for_user(user_id)

    # SMS: per-persona counts v tenantu -> sum. Reuse existujici funkce
    # misto zavedeni nove "total" varianty (konzistence, jedna ruka na DB).
    sms_counts = sms_service.get_unread_counts_per_persona(tenant_id)
    unread_sms = sum(sms_counts.values())

    total = unread_email + unread_sms

    return {
        "unread_email": unread_email,
        "unread_sms": unread_sms,
        "total": total,
        "tenant_id": tenant_id,
    }
