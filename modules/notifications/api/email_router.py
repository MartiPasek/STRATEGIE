"""
Email router -- PR2 scope: manualni Fetch-now trigger z UI tlacitka.

Base: /api/v1/email

PR3 pridame dalsi endpointy (inbox list, mark-processed, suggest-reply,
reply) v samostatnem email_ui_routeru -- stejne jako mame sms_gateway_router
+ sms_ui_router. Tenhle router je prozatim mini (fetch on-demand).
"""
from fastapi import APIRouter, HTTPException, Request

from core.database_core import get_core_session
from core.logging import get_logger
from modules.core.infrastructure.models_core import User
from modules.notifications.application import ews_fetcher


logger = get_logger("email.api")

router = APIRouter(prefix="/api/v1/email", tags=["email"])


# ── Auth helper ────────────────────────────────────────────────────────────

def _get_uid(req: Request) -> int:
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")


# ── Fetch triggers ─────────────────────────────────────────────────────────

@router.post("/fetch/{persona_id}")
def fetch_one_persona(persona_id: int, req: Request):
    """
    Manualni trigger fetchu INBOXu pro konkretni personu. Pouziva se v UI
    (napr. tlacitko "Fetch now" v per-persona pohledu, pripadne ajax reload
    kdyz user vidi ze ma neco pricist).

    Pozn.: neni potreba cekat na polling worker (60s interval) -- tenhle
    endpoint blokuje, dokud se fetch nedokonci. Mal pripad = par vterin.
    """
    _get_uid(req)   # auth guard
    logger.info(f"EMAIL | fetch trigger | persona_id={persona_id}")
    result = ews_fetcher.fetch_unread_for_persona(persona_id)
    return result


@router.post("/fetch-all")
def fetch_all(req: Request):
    """
    Fetchne unread pro vsechny aktivni email kanaly. Pouziva se globalnim
    tlacitkem "Fetch now" v hlavicce -- user vidi v badge kolik toho ma
    a chce to obnovit hned, bez cekani na polling interval.

    Pozor: tenhle endpoint muze trvat dele pokud ma systems hodne person
    a kazda EWS connect/fetch trva par sekund. Pro dev/mvp je to OK,
    v produkci muzeme pridat async queue.
    """
    user_id = _get_uid(req)
    logger.info(f"EMAIL | fetch-all trigger | user_id={user_id}")
    # Phase 29-D (4.5.2026): clean cut na mailbox-based variant.
    result = ews_fetcher.fetch_all_active_mailboxes()
    return result
