from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.conversation.api.schemas import ChatRequest, ChatResponse, LastConversationResponse
from modules.conversation.application.service import chat
from modules.conversation.infrastructure.repository import get_last_conversation, get_active_persona_name
from core.database_core import get_core_session
from modules.core.infrastructure.models_core import User, Tenant

logger = get_logger("conversation.api")

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


def _get_current_tenant_for_user(
    user_id: int | None,
) -> tuple[int | None, str | None, str | None, str | None]:
    """
    Vrátí (tenant_id, tenant_name, tenant_code, display_name) aktuálního
    tenantu usera. Display_name je z user_tenant_profiles pro daný tenant.
    """
    if not user_id:
        return None, None, None, None
    from modules.core.infrastructure.models_core import UserTenant, UserTenantProfile

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.last_active_tenant_id:
            return None, None, None, None
        tenant = session.query(Tenant).filter_by(id=user.last_active_tenant_id).first()
        if not tenant:
            return None, None, None, None
        # Display name z user_tenant_profiles
        display_name = None
        ut = (
            session.query(UserTenant)
            .filter_by(user_id=user_id, tenant_id=tenant.id)
            .first()
        )
        if ut:
            profile = (
                session.query(UserTenantProfile)
                .filter_by(user_tenant_id=ut.id)
                .first()
            )
            if profile:
                display_name = profile.display_name
        if not display_name:
            display_name = user.first_name or user.short_name
        return tenant.id, tenant.tenant_name, tenant.tenant_code, display_name
    finally:
        session.close()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    try:
        user_id_str = req.cookies.get("user_id")
        user_id = int(user_id_str) if user_id_str else None

        conversation_id, reply, summary_info = chat(
            conversation_id=request.conversation_id,
            user_message=request.text,
            user_id=user_id,
        )

        persona_name = get_active_persona_name(conversation_id)

        summary_notice: str | None = None
        if summary_info:
            cnt = summary_info.get("message_count", 0)
            summary_notice = f"⏳ Shrnul jsem {cnt} starších zpráv do historie."

        # Aktuální tenant po této zprávě (zachycuje i tenant switch v chatu)
        tenant_id, tenant_name, tenant_code, display_name = _get_current_tenant_for_user(user_id)

        return ChatResponse(
            conversation_id=conversation_id,
            reply=reply,
            active_persona=persona_name,
            summary_notice=summary_notice,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tenant_code=tenant_code,
            display_name=display_name,
        )
    except Exception as e:
        logger.exception(f"Chat failed: {e}")
        raise HTTPException(status_code=503, detail="Chat service unavailable.")


@router.get("/last", response_model=LastConversationResponse | None)
def get_last(req: Request):
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        return None
    user_id = int(user_id_str)
    result = get_last_conversation(user_id)
    if not result:
        return None

    persona_name = get_active_persona_name(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
    )
