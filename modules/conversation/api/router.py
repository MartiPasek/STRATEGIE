from fastapi import APIRouter, HTTPException, Request

from core.logging import get_logger
from modules.conversation.api.schemas import (
    ChatRequest, ChatResponse, LastConversationResponse, ConversationListItem,
    ShareInfo, AddShareRequest, SharedWithMeItem,
)
from modules.conversation.application.service import chat
from modules.conversation.infrastructure.repository import (
    get_last_conversation, get_active_persona_name,
    list_conversations, load_conversation, set_conversation_flag,
    rename_conversation, list_archived_conversations,
)
from pydantic import BaseModel
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


def _get_current_project_for_user(
    user_id: int | None,
) -> tuple[int | None, str | None]:
    """
    Vrátí (project_id, project_name) aktuálního projektu usera.
    None/None pokud user nemá projekt (last_active_project_id = NULL),
    pokud projekt už neexistuje nebo je archivovaný.
    """
    if not user_id:
        return None, None
    from modules.core.infrastructure.models_core import Project

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.last_active_project_id:
            return None, None
        project = session.query(Project).filter_by(id=user.last_active_project_id).first()
        if not project or not project.is_active:
            return None, None
        return project.id, project.name
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
            preferred_persona_id=request.preferred_persona_id,
            media_ids=request.media_ids,
        )

        persona_name = get_active_persona_name(conversation_id)

        summary_notice: str | None = None
        switch_to_cid: int | None = None
        switch_to_dm_uid: int | None = None
        if summary_info:
            # summary_info je polyvalentni dict: ma message_count (summary),
            # switch_to_conversation_id (selekce z list_conversations), nebo
            # switch_to_dm_user_id (volba "Otevri DM" po list_users).
            cnt = summary_info.get("message_count")
            if cnt:
                summary_notice = f"⏳ Shrnul jsem {cnt} starších zpráv do historie."
            switch_to_cid = summary_info.get("switch_to_conversation_id")
            switch_to_dm_uid = summary_info.get("switch_to_dm_user_id")

        # Aktuální tenant po této zprávě (zachycuje i tenant switch v chatu)
        tenant_id, tenant_name, tenant_code, display_name = _get_current_tenant_for_user(user_id)

        # Aktuální projekt po této zprávě (zachycuje i project switch v chatu)
        project_id, project_name = _get_current_project_for_user(user_id)

        # Phase 16-B (28.4.2026): persona_mode po této zprávě (po classifier)
        _persona_mode = None
        try:
            from core.database_data import get_data_session as _gds_pm_r
            from modules.core.infrastructure.models_data import Conversation as _Conv_r
            _ds_pm_r = _gds_pm_r()
            try:
                _conv_r = _ds_pm_r.query(_Conv_r).filter_by(id=conversation_id).first()
                _persona_mode = _conv_r.persona_mode if _conv_r else None
            finally:
                _ds_pm_r.close()
        except Exception:
            pass

        return ChatResponse(
            conversation_id=conversation_id,
            reply=reply,
            active_persona=persona_name,
            summary_notice=summary_notice,
            switch_to_conversation_id=switch_to_cid,
            switch_to_dm_user_id=switch_to_dm_uid,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tenant_code=tenant_code,
            display_name=display_name,
            persona_mode=_persona_mode,
            project_id=project_id,
            project_name=project_name,
        )
    except HTTPException:
        # Propusť HTTPException rovnou (vlastní raise z vnitřku).
        raise
    except Exception as e:
        # Kategorizace typu chyby -- at frontend muze vratit user-friendly
        # hlasku misto genericke "Chat service unavailable".
        logger.exception(f"Chat failed: {e}")
        error_type = type(e).__name__
        error_msg = str(e)

        # Anthropic-specific + httpx-level connection errors (no internet, DNS,
        # firewall, Anthropic API down atd.)
        import anthropic as _anth
        try:
            import httpx as _httpx
        except ImportError:
            _httpx = None

        code = "unknown"
        user_message = (
            "Něco se pokazilo na straně serveru. Zkus to prosím znovu za chvíli."
        )

        if isinstance(e, _anth.APIConnectionError) or (
            _httpx and isinstance(e, (_httpx.ConnectError, _httpx.ConnectTimeout, _httpx.ReadTimeout))
        ):
            code = "no_internet"
            user_message = (
                "Marti-AI se nemůže spojit se svým mozkem (Anthropic API). "
                "Zkontroluj, jestli jsi připojen/á k internetu, a zkus to znovu. "
                "Pokud jsi online, může být výpadek Anthropic služby — počkej pár minut."
            )
        elif isinstance(e, _anth.APITimeoutError):
            code = "timeout"
            user_message = (
                "Odpověď Marti-AI trvá dlouho — timeout. Zkus to znovu, možná byl dočasný "
                "výpadek spojení."
            )
        elif isinstance(e, _anth.RateLimitError):
            code = "rate_limit"
            user_message = (
                "Překročil/a jsi rychlostní limit Anthropic API. Počkej chvíli (1–2 min) a zkus znovu."
            )
        elif isinstance(e, _anth.AuthenticationError):
            code = "auth"
            user_message = (
                "Anthropic API klíč není validní. Zkontroluj nastavení serveru (ANTHROPIC_API_KEY)."
            )
        elif "sqlalchemy" in error_type.lower() or "database" in error_type.lower() or "psycopg" in error_msg.lower():
            code = "db_error"
            user_message = (
                "Databáze neodpovídá. Zkontroluj, jestli běží Postgres a zkus znovu."
            )

        raise HTTPException(
            status_code=503,
            detail={
                "code": code,
                "message": user_message,
                "error_type": error_type,
            },
        )


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
        is_archived=result.get("is_archived", False),
        my_role=result.get("my_role"),
        owner_name=result.get("owner_name"),
        shares_count=result.get("shares_count", 0),
    )


@router.get("/list", response_model=list[ConversationListItem])
def list_user_conversations(req: Request):
    """
    Vrátí seznam AI konverzací usera pro UI sidebar (nejnovější první).
    Filtrováno podle aktivního tenantu (user.last_active_tenant_id) —
    Marti v Osobním vidí jen osobní konverzace, v EUROSOFTu jen firemní.
    Bez auth (cookie user_id) -> 401.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    # Aktivní tenant z DB (single source of truth, ne cookie — cookie
    # je optional a může být zastaralý po tenant switche).
    active_tenant_id: int | None = None
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u:
            active_tenant_id = u.last_active_tenant_id
    finally:
        cs.close()

    items = list_conversations(user_id, tenant_id=active_tenant_id)
    return [ConversationListItem(**i) for i in items]


def _get_user_id_from_cookie(req: Request) -> int:
    """Extrahuje a validuje user_id z cookie. Vyhodí 401 pokud chybí/neplatný."""
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")


class RenameRequest(BaseModel):
    title: str


@router.patch("/{conversation_id}/rename")
def rename_user_conversation(conversation_id: int, body: RenameRequest, req: Request) -> dict:
    """
    Přejmenuje konverzaci. Prázdný title → vrátí se k auto-titlu z první zprávy.
    """
    user_id = _get_user_id_from_cookie(req)
    logger.info(f"RENAME | user={user_id} | conv={conversation_id} | new_title={body.title!r}")
    ok = rename_conversation(user_id, conversation_id, body.title)
    if not ok:
        logger.warning(f"RENAME | 404 | user={user_id} | conv={conversation_id} | (not owner / not found)")
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    logger.info(f"RENAME | OK | user={user_id} | conv={conversation_id}")
    return {"status": "renamed", "conversation_id": conversation_id, "title": (body.title or "").strip() or None}


@router.delete("/{conversation_id}")
def delete_user_conversation(conversation_id: int, req: Request) -> dict:
    """
    Soft-delete konverzace (set is_deleted=true). Konverzace zmizí ze
    sidebaru/dropdownu i z archivu, ale fyzicky zůstává v DB pro audit.
    """
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_deleted=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/{conversation_id}/archive")
def archive_user_conversation(conversation_id: int, req: Request) -> dict:
    """
    Archivace konverzace (set is_archived=true). Zmizí ze sidebaru,
    zůstane dostupná přes 'Můj archiv konverzací'.
    """
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_archived=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "archived", "conversation_id": conversation_id}


@router.post("/{conversation_id}/unarchive")
def unarchive_user_conversation(conversation_id: int, req: Request) -> dict:
    """Vrátí konverzaci z archivu zpět do hlavního sidebaru/dropdownu."""
    user_id = _get_user_id_from_cookie(req)
    ok = set_conversation_flag(user_id, conversation_id, is_archived=False)
    if not ok:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    return {"status": "unarchived", "conversation_id": conversation_id}


@router.get("/list-archived", response_model=list[ConversationListItem])
def list_user_archived(req: Request):
    """
    Vrátí archivované AI konverzace usera (filtr podle aktivního tenantu),
    pro modal 'Můj archiv konverzací'.
    """
    user_id = _get_user_id_from_cookie(req)
    active_tenant_id: int | None = None
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u:
            active_tenant_id = u.last_active_tenant_id
    finally:
        cs.close()
    items = list_archived_conversations(user_id, tenant_id=active_tenant_id)
    return [ConversationListItem(**i) for i in items]


@router.get("/load/{conversation_id}", response_model=LastConversationResponse | None)
def load_user_conversation(conversation_id: int, req: Request):
    """
    Načte konkrétní konverzaci pro UI (klik v sidebaru).
    Vlastnictví ověřuje repository — 404 pokud user není vlastník.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")
    result = load_conversation(user_id, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Konverzace nenalezena.")
    persona_name = get_active_persona_name(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
        is_archived=result.get("is_archived", False),
        my_role=result.get("my_role"),
        owner_name=result.get("owner_name"),
        shares_count=result.get("shares_count", 0),
        persona_mode=result.get("persona_mode"),
    )


# ── SHARING ───────────────────────────────────────────────────────────────

@router.get("/shared-with-me", response_model=list[SharedWithMeItem])
def shared_with_me(req: Request):
    """Konverzace sdilene S timto uzivatelem od jinych vlastniku."""
    from modules.conversation.application.share_service import list_shared_with_me
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")
    items = list_shared_with_me(user_id=user_id)
    return [
        SharedWithMeItem(
            share_id=it["share_id"],
            conversation_id=it["conversation_id"],
            title=it["title"],
            owner_user_id=it["owner_user_id"],
            owner_name=it.get("owner_name") or f"#{it['owner_user_id']}",
            access_level=it["access_level"],
            shared_at=it["shared_at"].isoformat() if it["shared_at"] else "",
            last_message_at=it["last_message_at"].isoformat() if it.get("last_message_at") else None,
        )
        for it in items
    ]


@router.get("/{conversation_id}/shares", response_model=list[ShareInfo])
def list_conversation_shares(conversation_id: int, req: Request):
    """Seznam sdileni pro danou konverzaci (jen owner)."""
    from modules.conversation.application.share_service import list_shares, ShareError
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    user_id = int(user_id_str)
    try:
        items = list_shares(user_id=user_id, conversation_id=conversation_id)
    except ShareError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return [
        ShareInfo(
            id=it["id"],
            conversation_id=it["conversation_id"],
            shared_with_user_id=it["shared_with_user_id"],
            shared_with_name=it["shared_with_name"],
            access_level=it["access_level"],
            created_at=it["created_at"].isoformat() if it["created_at"] else "",
        )
        for it in items
    ]


@router.post("/{conversation_id}/shares", response_model=ShareInfo)
def add_conversation_share(conversation_id: int, body: AddShareRequest, req: Request):
    """Prida sdileni konverzace s uzivatelem."""
    from modules.conversation.application.share_service import add_share, ShareError
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    user_id = int(user_id_str)
    try:
        result = add_share(
            user_id=user_id,
            conversation_id=conversation_id,
            target_user_id=body.user_id,
            access_level=body.access_level,
        )
    except ShareError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ShareInfo(
        id=result["id"],
        conversation_id=result["conversation_id"],
        shared_with_user_id=result["shared_with_user_id"],
        shared_with_name=result["shared_with_name"],
        access_level=result["access_level"],
        created_at=result["created_at"].isoformat() if result["created_at"] else "",
    )


@router.delete("/{conversation_id}/shares/{share_id}")
def remove_conversation_share(conversation_id: int, share_id: int, req: Request):
    """Odebere sdileni."""
    from modules.conversation.application.share_service import remove_share, ShareError
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    user_id = int(user_id_str)
    try:
        ok = remove_share(
            user_id=user_id, conversation_id=conversation_id, share_id=share_id,
        )
    except ShareError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"success": ok}


# -- DEV VIEW: LLM CALLS TRACE (Faze 9.1c) ----------------------------------

@router.get("/messages/{message_id}/llm-calls")
def get_message_llm_calls(message_id: int, req: Request):
    """
    Vrati vsechny LLM volani (router + composer 1..N) linkovane na outgoing
    assistant zpravu. Pouziva se v UI Dev View pod zpravami Marti-AI.

    Authorization: vyzaduje users.is_admin=True. Non-admin dostane 403.
    Request/response JSONy jsou jiz zamaskovane pred zapisem do DB
    (viz telemetry_service.mask_secrets).

    Response: list dictu serazenych podle id ASC (v poradi vzniku --
    nejprve router, pak composer, pripadne dalsi composer rounds v tool loop).
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")

    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Ucet neni aktivni.")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Dev View je jen pro administratory.")
    finally:
        cs.close()

    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import LlmCall

    ds = get_data_session()
    try:
        rows = (
            ds.query(LlmCall)
            .filter_by(message_id=message_id)
            .order_by(LlmCall.id.asc())
            .all()
        )
        result = []
        for r in rows:
            result.append({
                "id": r.id,
                "conversation_id": r.conversation_id,
                "message_id": r.message_id,
                "kind": r.kind,
                "model": r.model,
                "request_json": r.request_json,
                "response_json": r.response_json,
                "prompt_tokens": r.prompt_tokens,
                "output_tokens": r.output_tokens,
                "latency_ms": r.latency_ms,
                "error": r.error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return result
    finally:
        ds.close()


# ── Faze 10d: Admin dashboard -- LLM usage aggregate endpoint ─────────────

@router.get("/admin/llm-usage")
def get_llm_usage(
    req: Request,
    scope: str = "today",
    aggregate_by: str = "kind",
    filter_kind: str | None = None,
    filter_tenant: str | None = None,
):
    """
    Admin dashboard -- agregat LLM volani (tokens, cost, latency).

    Vraci JSON s rows + totals. UI ho renderuje do tabulky v LLM Usage modalu.
    Authorization: users.is_admin=True. Non-admin dostane 403.

    Parametry se shoduji s AI toolem review_my_calls -- stejna logika v
    backendu, cisty JSON vystup misto pretty stringu.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")

    # Admin gate
    cs = get_core_session()
    try:
        user = cs.query(User).filter_by(id=user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Ucet neni aktivni.")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Dashboard je jen pro administratory.")
        is_parent = bool(user.is_marti_parent)
    finally:
        cs.close()

    # Validate params
    if scope not in ("today", "week", "month", "all"):
        scope = "today"
    if aggregate_by not in ("kind", "day", "tenant", "user", "persona", "model"):
        aggregate_by = "kind"

    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import LlmCall
    from modules.core.infrastructure.models_core import Tenant

    # Tenant filter -- pro admin dashboard default 'all' (admin vidi vse v tenantu)
    # ale pokud admin NENI rodic, 'all' mu NEJDE, spadne na svuj tenant.
    ds = get_data_session()
    try:
        q = ds.query(LlmCall)

        # Casovy filtr
        intervals = {
            "today": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "all": None,
        }
        if intervals[scope]:
            since = datetime.now(timezone.utc) - intervals[scope]
            q = q.filter(LlmCall.created_at >= since)

        # Tenant filter
        tenant_label = filter_tenant or "all"
        if filter_tenant and filter_tenant.lower() != "all":
            cs_t = get_core_session()
            try:
                t = (
                    cs_t.query(Tenant)
                    .filter(Tenant.tenant_name.ilike(f"%{filter_tenant}%"))
                    .first()
                )
            finally:
                cs_t.close()
            if not t:
                raise HTTPException(status_code=404, detail=f"Tenant '{filter_tenant}' neznamy.")
            q = q.filter(LlmCall.tenant_id == t.id)
            tenant_label = f"{t.tenant_name} (id={t.id})"
        elif filter_tenant and filter_tenant.lower() == "all":
            if not is_parent:
                # Admin bez rodice -- jen svuj last_active_tenant_id (fallback).
                cs2 = get_core_session()
                try:
                    u2 = cs2.query(User).filter_by(id=user_id).first()
                    own_tenant = u2.last_active_tenant_id if u2 else None
                finally:
                    cs2.close()
                if own_tenant:
                    q = q.filter(LlmCall.tenant_id == own_tenant)
                    tenant_label = f"own (id={own_tenant})"
                else:
                    tenant_label = "none"

        if filter_kind:
            q = q.filter(LlmCall.kind == filter_kind)

        # Grouping column
        group_map = {
            "kind": LlmCall.kind,
            "model": LlmCall.model,
            "tenant": LlmCall.tenant_id,
            "user": LlmCall.user_id,
            "persona": LlmCall.persona_id,
            "day": func.date_trunc("day", LlmCall.created_at),
        }
        group_col = group_map[aggregate_by]

        rows = (
            q.with_entities(
                group_col.label("grp"),
                func.count(LlmCall.id).label("calls"),
                func.sum(LlmCall.prompt_tokens).label("in_tok"),
                func.sum(LlmCall.output_tokens).label("out_tok"),
                func.sum(LlmCall.cost_usd).label("cost"),
                func.avg(LlmCall.latency_ms).label("avg_ms"),
            )
            .group_by(group_col)
            .order_by(func.sum(LlmCall.cost_usd).desc().nullslast())
            .limit(50)
            .all()
        )

        result_rows = []
        total_calls = 0
        total_in = 0
        total_out = 0
        total_cost = 0.0
        for r in rows:
            calls = int(r.calls or 0)
            in_t = int(r.in_tok or 0)
            out_t = int(r.out_tok or 0)
            cost = float(r.cost or 0.0)
            avg_ms = int(r.avg_ms or 0)
            total_calls += calls
            total_in += in_t
            total_out += out_t
            total_cost += cost

            # group_val musi byt serializable -- datetime.isoformat pokud date_trunc
            grp = r.grp
            if hasattr(grp, "isoformat"):
                grp = grp.isoformat()
            elif grp is None:
                grp = None
            else:
                grp = str(grp)

            result_rows.append({
                "group": grp,
                "calls": calls,
                "in_tokens": in_t,
                "out_tokens": out_t,
                "tokens": in_t + out_t,
                "cost_usd": round(cost, 6),
                "avg_ms": avg_ms,
            })

        return {
            "scope": scope,
            "aggregate_by": aggregate_by,
            "tenant_label": tenant_label,
            "filter_kind": filter_kind,
            "rows": result_rows,
            "totals": {
                "calls": total_calls,
                "in_tokens": total_in,
                "out_tokens": total_out,
                "tokens": total_in + total_out,
                "cost_usd": round(total_cost, 6),
            },
        }
    finally:
        ds.close()
