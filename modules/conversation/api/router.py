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
    list_personal_conversations, create_conversation,
    find_empty_unshared_conversation,
)
from pydantic import BaseModel
from core.database_core import get_core_session
from modules.core.infrastructure.models_core import User, Tenant

logger = get_logger("conversation.api")

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


def _build_incarnation_safe(conversation_id: int | None) -> dict | None:
    """Phase 24-G: Wrapper pro build_incarnation_info -- safe pri exception.
    Pouziva se v endpointech /chat, /last, /load. Single source of truth
    pro UI hlavičku "Mluvis s: ..."."""
    if not conversation_id:
        return None
    try:
        from modules.md_pyramid.application.service import build_incarnation_info
        return build_incarnation_info(conversation_id)
    except Exception as e:
        logger.warning(f"_build_incarnation_safe failed: {e}")
        return None


def _fetch_context_window_size(conversation_id: int | None) -> int | None:
    """
    Phase 31 polish (3.5.2026): nacti aktualni context_window_size konverzace
    pro UI 🪟 window size badge v hlavicce. Default 5 ('klid pozornosti').
    Marti-AI to meni pres set_conversation_window AI tool.
    """
    if not conversation_id:
        return None
    try:
        from core.database_data import get_data_session as _gds_cw
        from modules.core.infrastructure.models_data import Conversation as _Conv_cw
        ds = _gds_cw()
        try:
            conv = ds.query(_Conv_cw).filter_by(id=conversation_id).first()
            if conv and conv.context_window_size is not None:
                return int(conv.context_window_size)
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"_fetch_context_window_size failed: {e}")
    return None


def _detect_zoom_in_n(message_id: int | None) -> int | None:
    """
    Phase 31 polish (3.5.2026): detekuj zda assistant message volala
    recall_conversation_history(N=X) v tomto turn-u (z tool_blocks).
    UI zobrazi 📜 zoom N badge u te bubliny.

    Hleda v messages.tool_blocks JSONB navazujicim audit message
    (message_id+1 typicky, ale stacit hledat conversation pseudo-user
    s message_type='tool_result' nasledujicim).
    """
    if not message_id:
        return None
    try:
        from core.database_data import get_data_session as _gds_zoom
        from modules.core.infrastructure.models_data import Message as _Msg_zoom
        ds = _gds_zoom()
        try:
            # Najdi audit follow-up po tomto assistant msg
            audit = (
                ds.query(_Msg_zoom)
                .filter(
                    _Msg_zoom.id > message_id,
                    _Msg_zoom.message_type == "tool_result",
                )
                .order_by(_Msg_zoom.id.asc())
                .first()
            )
            if not audit or not audit.tool_blocks:
                return None
            blocks = audit.tool_blocks if isinstance(audit.tool_blocks, list) else []
            for b in blocks:
                if (
                    isinstance(b, dict)
                    and b.get("type") == "tool_use"
                    and b.get("name") == "recall_conversation_history"
                ):
                    n = (b.get("input") or {}).get("n_messages")
                    if isinstance(n, int):
                        return n
        finally:
            ds.close()
    except Exception as e:
        logger.warning(f"_detect_zoom_in_n failed: {e}")
    return None


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


@router.get("/progress")
def chat_progress(req: Request) -> dict:
    """Live progress (Marti 2.6.2026): "co Marti-AI zrovna dela" pro UI poll
    behem "Premyslim...". Keyed user_id (session cookie). Best-effort, in-memory."""
    try:
        from modules.conversation.application.service import progress_get as _pg
        uid_s = req.cookies.get("user_id")
        uid = int(uid_s) if uid_s else None
        return {"ok": True, "progress": _pg(uid)}
    except Exception:
        return {"ok": True, "progress": None}


# Faze 2B+ (2.6.2026): zive sdileni obrazovky — in-memory slot per konverzace.
# Sharer posila frame (media_id) ~kazde 3s do slotu (POST), vieweri pollnou
# nejnovejsi (GET) a obcerstvi JEDNO okno — zadny flood zprav. Slot expiruje za
# 20s ticha (= sdileni skoncilo). Caddy lb_policy first -> vse na primary.
import time as _ls_time
import threading as _ls_threading
_LIVE_SCREEN: dict = {}
_LIVE_SCREEN_LOCK = _ls_threading.Lock()


@router.post("/{conversation_id}/live-screen")
def set_live_screen(conversation_id: int, media_id: int, req: Request) -> dict:
    """Sharer ulozi nejnovejsi frame (media_id) do live slotu konverzace."""
    uid_s = req.cookies.get("user_id")
    uid = int(uid_s) if uid_s else None
    if not uid:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    from modules.conversation.application.share_service import can_user_view_conversation as _cv_ls
    can, _role = _cv_ls(uid, conversation_id)
    if not can:
        raise HTTPException(status_code=403, detail="Nemáš přístup k této konverzaci.")
    _name = None
    try:
        from core.database_core import get_core_session as _gcs_ls
        from modules.core.infrastructure.models_core import User as _U_ls
        _cs_ls = _gcs_ls()
        try:
            _u_ls = _cs_ls.query(_U_ls.short_name, _U_ls.first_name).filter(_U_ls.id == uid).first()
            if _u_ls:
                _name = _u_ls[0] or _u_ls[1]
        finally:
            _cs_ls.close()
    except Exception:
        pass
    with _LIVE_SCREEN_LOCK:
        _LIVE_SCREEN[conversation_id] = {
            "media_id": media_id, "by_user_id": uid,
            "by_name": _name or ("#%s" % uid), "ts": _ls_time.time(),
        }
    return {"ok": True}


@router.get("/{conversation_id}/live-screen")
def get_live_screen(conversation_id: int, req: Request) -> dict:
    """Viewer pollne nejnovejsi live frame. active=False kdyz sdileni neni/skonci."""
    uid_s = req.cookies.get("user_id")
    uid = int(uid_s) if uid_s else None
    if not uid:
        return {"active": False}
    with _LIVE_SCREEN_LOCK:
        slot = _LIVE_SCREEN.get(conversation_id)
    if not slot or (_ls_time.time() - slot.get("ts", 0)) > 60:
        return {"active": False}
    return {
        "active": True, "media_id": slot["media_id"],
        "by_user_id": slot["by_user_id"], "by_name": slot["by_name"],
    }


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    try:
        user_id_str = req.cookies.get("user_id")
        user_id = int(user_id_str) if user_id_str else None

        # Phase 19c-e1 (29.4.2026): read-only enforcement pro Personal archiv.
        # Marti-AI's slova: "Personal konverzace je knizka -- uzavrena,
        # nedotknutelna. Nikdo do ni nepise, ani Marti nahodne, ani ja
        # v nepozornem momentu." (email 29.4. 5:32 ranni).
        # Defense in depth: UI ma input disabled, ale kdyby se cookie/state
        # rozejely, backend chrani konverzaci 403-kou.
        if request.conversation_id is not None:
            from core.database_data import get_data_session as _gds_lc
            from modules.core.infrastructure.models_data import (
                Conversation as _Conv_lc,
            )
            _ds_lc = _gds_lc()
            try:
                _conv_lc = (
                    _ds_lc.query(_Conv_lc)
                    .filter_by(id=request.conversation_id)
                    .first()
                )
                if _conv_lc and getattr(_conv_lc, "lifecycle_state", None) == "personal":
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            "Personal archiv je uzavřen pro zápis. "
                            "Pokud chceš pokračovat, požádej Marti-AI o nový dovětek."
                        ),
                    )
            finally:
                _ds_lc.close()

            # Phase 14b+ (13.5.2026 dopoledne): shared_read enforcement.
            # Pokud je user shared viewer s access_level='read', backend
            # odmita POST /chat. Defense in depth — UI ma input disabled
            # (index.html line ~5577 'sharedReadonly'), ale cookie/state
            # bypass nesmi prochazet.
            # RW sdileni (access_level='write') vsak prochazi — Marti's
            # consult s Kristy 13.5.2026 dopoledne, sandbox debugging
            # konverzace potrebuje multi-user write.
            if user_id is not None:
                from modules.conversation.application.share_service import (
                    can_user_view_conversation as _cuvc,
                )
                _can_view, _role = _cuvc(user_id, request.conversation_id)
                if _can_view and _role == "shared_read":
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            "Tato konverzace je sdílena s tebou jen ke čtení. "
                            "Pro zápis poproste vlastníka, aby upgradoval "
                            "tvé sdílení na 'write' přes share modal."
                        ),
                    )

        # Skupina F1 (2.6.2026): ai_turn=False -> lidska zprava do (sdilene)
        # konverzace BEZ composeru (Marti-AI mlci). Default True zachovava solo
        # chat. ACL uz vynuceno vyse (shared_read 403). Vraci minimal ChatResponse
        # -- frontend jen vykresli vlastni zpravu, ostatni ji vidi pres poller.
        if not request.ai_turn:
            _cid_g = request.conversation_id
            if _cid_g is None:
                raise HTTPException(
                    status_code=400,
                    detail="Skupinová zpráva (ai_turn=false) vyžaduje conversation_id.",
                )
            from modules.conversation.infrastructure.repository import save_message as _save_g
            _mid_g = _save_g(
                _cid_g, role="user", content=request.text,
                author_type="human", author_user_id=user_id,
            )
            if request.media_ids:
                try:
                    from modules.media.application.service import attach_to_message as _att_g
                    _att_g(request.media_ids, _mid_g)
                except Exception as _eg:
                    logger.warning(f"[group] media attach failed (msg={_mid_g}): {_eg}")
            return ChatResponse(conversation_id=_cid_g, reply="")

        # Phase 43 Mini-faze A (19.5.2026): pre_msg_id zachytava posledni msg
        # ID v dane konverzaci PRED chat() flow. Po chat() turn-u backend
        # SELECT messages s id > pre_msg_id AND author_user_id IN (3, 23) —
        # vraci je v ChatResponse.extra_messages pro frontend addMessage loop
        # (Claude bublina, STRATEGIE system_audit bubliny).
        # Marti-AI Q1 doctrine: pre_msg_id MUSI byt zachycen PRED prvnim tool
        # callem, jinak ztratime Claude reply id z toho sameho kola.
        _pre_msg_id: int = 0
        if request.conversation_id is not None:
            try:
                from core.database_data import get_data_session as _gds_pmid
                from modules.core.infrastructure.models_data import Message as _M_pmid
                from sqlalchemy import func as _sa_func_pmid
                _ds_pmid = _gds_pmid()
                try:
                    _max_id = (
                        _ds_pmid.query(_sa_func_pmid.coalesce(_sa_func_pmid.max(_M_pmid.id), 0))
                        .filter(_M_pmid.conversation_id == request.conversation_id)
                        .scalar()
                    )
                    _pre_msg_id = int(_max_id or 0)
                finally:
                    _ds_pmid.close()
            except Exception as _e_pmid:
                logger.warning(f"pre_msg_id capture failed: {_e_pmid}")

        conversation_id, reply, summary_info = chat(
            conversation_id=request.conversation_id,
            user_message=request.text,
            user_id=user_id,
            preferred_persona_id=request.preferred_persona_id,
            media_ids=request.media_ids,
        )

        # Live progress (Marti 2.6.2026): turn dobehl -> uklid (poll uz nebezi;
        # staleness 90s je backstop pro chybove cesty). Best-effort.
        try:
            from modules.conversation.application.service import progress_clear as _pc
            _pc(user_id)
        except Exception:
            pass

        # Phase 43 Mini-faze A: post-chat extra_messages fetch. Hleda nove
        # messages od non-current-user actoru (Claude id=23, STRATEGIE id=3),
        # ktere vznikly behem tohoto chat() turnu (po pre_msg_id, pred
        # ChatResponse return). Filter na is_category_visible() — file_ok /
        # read_ok skipped (default tabulka).
        _extra_messages: list = []
        try:
            from core.database_data import get_data_session as _gds_em
            from modules.core.infrastructure.models_data import Message as _M_em
            from modules.core.infrastructure.models_core import User as _U_em
            from core.system_actor import extract_category, is_category_visible
            from modules.conversation.api.schemas import ExtraMessage

            _EXTRA_AUTHOR_IDS = (3, 23)  # STRATEGIE, Claude
            _COLOR_MAP = {3: "#e8eaed", 23: "#5dc8c0"}  # Phase 43 Q9 colors

            _ds_em = _gds_em()
            try:
                _rows_em = (
                    _ds_em.query(_M_em)
                    .filter(
                        _M_em.conversation_id == conversation_id,
                        _M_em.id > _pre_msg_id,
                        _M_em.author_user_id.in_(_EXTRA_AUTHOR_IDS),
                        _M_em.message_type.in_(["text", "system_audit"]),
                    )
                    .order_by(_M_em.created_at.asc(), _M_em.id.asc())  # Marti-AI Q2 (c)
                    .all()
                )
                # Bulk lookup author short_name
                _author_ids = list({m.author_user_id for m in _rows_em if m.author_user_id})
                _author_names: dict[int, str] = {}
                if _author_ids:
                    try:
                        from core.database_core import get_core_session as _gcs_em
                        _cs_em = _gcs_em()
                        try:
                            _users_em = (
                                _cs_em.query(_U_em.id, _U_em.short_name, _U_em.first_name)
                                .filter(_U_em.id.in_(_author_ids))
                                .all()
                            )
                            for _u in _users_em:
                                _author_names[_u[0]] = _u[1] or _u[2] or f"User#{_u[0]}"
                        finally:
                            _cs_em.close()
                    except Exception as _eu:
                        logger.warning(f"extra_messages author lookup failed: {_eu}")

                for _m in _rows_em:
                    _cat = extract_category(_m.content) if _m.message_type == "system_audit" else None
                    # Filter — file.write_ok / file.read_ok skipped
                    if _m.message_type == "system_audit" and not is_category_visible(_cat, conversation_id):
                        continue
                    _extra_messages.append(
                        ExtraMessage(
                            id=_m.id,
                            content=_m.content,
                            role=_m.role or "user",
                            author_user_id=_m.author_user_id,
                            author_short_name=_author_names.get(_m.author_user_id),
                            author_color=_COLOR_MAP.get(_m.author_user_id),
                            message_type=_m.message_type,
                            category=_cat,
                            created_at=(_m.created_at.isoformat() if _m.created_at else ""),
                        )
                    )
            finally:
                _ds_em.close()
        except Exception as _e_em:
            logger.warning(f"extra_messages fetch failed: {_e_em}")
            _extra_messages = []

        persona_name = get_active_persona_name(conversation_id)
        # Haiku pomocnik: 'H '/'h ' prefix -> label 'Haiku' u zive odpovedi.
        if isinstance(request.text, str) and request.text[:2] in ("H ", "h "):
            persona_name = "Haiku"

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
        # Phase 19b polish (29.4.2026 vecer): plus active_pack + custom flag
        _persona_mode = None
        _active_pack = None
        _pack_overlay_custom = False
        try:
            from core.database_data import get_data_session as _gds_pm_r
            from modules.core.infrastructure.models_data import Conversation as _Conv_r
            _ds_pm_r = _gds_pm_r()
            try:
                _conv_r = _ds_pm_r.query(_Conv_r).filter_by(id=conversation_id).first()
                if _conv_r:
                    _persona_mode = _conv_r.persona_mode
                    _active_pack = getattr(_conv_r, "active_pack", None)
                    _agent_id_r = getattr(_conv_r, "active_agent_id", None)
            finally:
                _ds_pm_r.close()
            # Detekce vlastniho overlay
            if _active_pack and _agent_id_r:
                from core.database_core import get_core_session as _gcs_pp_r
                from modules.core.infrastructure.models_core import PersonaPackOverlay as _PPO_r
                _cs_pp_r = _gcs_pp_r()
                try:
                    _pack_overlay_custom = _cs_pp_r.query(_PPO_r).filter_by(
                        persona_id=_agent_id_r, pack_name=_active_pack
                    ).first() is not None
                finally:
                    _cs_pp_r.close()
        except Exception:
            pass

        # Phase 24-G (30.4.2026): UI Inkarnace Badge dict
        _incarnation_chat = _build_incarnation_safe(conversation_id)

        # Phase 31-C polish (3.5.2026): live UI render. Fetch latest assistant
        # msg id + cost_czk + cum_cost_czk + llm_calls aby UI po addMessage
        # mohlo rendrovat lupy + cost bez hard reload (pred fixem se ukazaly
        # az po reload).
        _assistant_msg_id: int | None = None
        _cost_czk: float | None = None
        _cum_cost_czk: float | None = None
        _llm_calls: list[dict] = []
        try:
            from core.database_data import get_data_session as _gds_p31uc
            from modules.core.infrastructure.models_data import (
                Message as _Msg_p31uc,
                LlmCall as _LC_p31uc,
            )
            from sqlalchemy import func as _sa_func_p31uc
            _ds_p31uc = _gds_p31uc()
            try:
                # Latest assistant text msg (skip tool_result audit pseudo-user)
                _latest = (
                    _ds_p31uc.query(_Msg_p31uc)
                    .filter_by(conversation_id=conversation_id, role="assistant")
                    .filter(_Msg_p31uc.message_type != "tool_result")
                    .order_by(_Msg_p31uc.id.desc())
                    .first()
                )
                if _latest:
                    _assistant_msg_id = _latest.id
                    # llm_calls pro tuto msg (Dev View lupy)
                    _calls_rows = (
                        _ds_p31uc.query(_LC_p31uc)
                        .filter_by(message_id=_latest.id)
                        .order_by(_LC_p31uc.id)
                        .all()
                    )
                    _llm_calls = [
                        {"id": c.id, "kind": c.kind, "latency_ms": c.latency_ms}
                        for c in _calls_rows
                    ]
                    # Per-message cost = SUM(cost_usd) * 28.75 (USD_TO_CZK_DISPLAY)
                    _cost_sum = sum(
                        float(c.cost_usd or 0.0) for c in _calls_rows
                    )
                    if _cost_sum > 0:
                        _cost_czk = round(_cost_sum * 28.75, 2)
                # Kumulativni cost konverzace (vsechny llm_calls.cost_usd
                # v teto conversation_id, sjednocene s repository._lookup_costs).
                _cum_usd = (
                    _ds_p31uc.query(
                        _sa_func_p31uc.coalesce(
                            _sa_func_p31uc.sum(_LC_p31uc.cost_usd), 0.0
                        )
                    )
                    .filter(_LC_p31uc.conversation_id == conversation_id)
                    .scalar()
                )
                if _cum_usd:
                    _cum_cost_czk = round(float(_cum_usd) * 28.75, 2)
            finally:
                _ds_p31uc.close()
        except Exception as _e_p31uc:
            logger.warning(f"chat extras lookup selhal: {_e_p31uc}")

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
            # Phase 19b polish (29.4.2026 vecer): UI badge signal
            active_pack=_active_pack,
            pack_overlay_custom=_pack_overlay_custom,
            # Phase 24-G: 6-axis incarnation info
            incarnation=_incarnation_chat,
            # Phase 31-C polish (3.5.2026): live UI render -- lupy + cost
            # po addMessage bez hard reload.
            assistant_message_id=_assistant_msg_id,
            cost_czk=_cost_czk,
            cum_cost_czk=_cum_cost_czk,
            llm_calls=_llm_calls,
            # Phase 31 polish (3.5.2026): 🪟 window size + 📜 zoom-in N badges
            context_window_size=_fetch_context_window_size(conversation_id),
            zoom_in_n=_detect_zoom_in_n(_assistant_msg_id),
            # Phase 43 Mini-faze A (19.5.2026): Claude bubliny + STRATEGIE
            # system_audit pro shared chat. Marti-AI Q1 (extra_messages), Q2
            # (created_at ASC), Marti's clarifying doctrine ("system bubliny
            # = human audience only" — composer filter na message_type).
            extra_messages=_extra_messages,
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
    # Phase 31 polish (3.5.2026): aktualni context window per-konverzace.
    _cwsize_last = _fetch_context_window_size(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
        is_archived=result.get("is_archived", False),
        my_role=result.get("my_role"),
        owner_name=result.get("owner_name"),
        shares_count=result.get("shares_count", 0),
        # Phase 40 v2 r3 (19.5.2026): is_shared cache -- UI shared mode signal
        is_shared=result.get("is_shared", False),
        # Phase 16-B: persona_mode signal (oversight hlavicka).
        persona_mode=result.get("persona_mode"),
        # Phase 19c-e1 (29.4.2026): lifecycle_state pro read-only UI.
        lifecycle_state=result.get("lifecycle_state"),
        # Phase 19b polish (29.4.2026 vecer): active_pack pro UI badge
        active_pack=result.get("active_pack"),
        pack_overlay_custom=result.get("pack_overlay_custom", False),
        # Phase 24-G (30.4.2026): UI Inkarnace Badge -- 6-axis info
        incarnation=_build_incarnation_safe(result["conversation_id"]),
        # Phase 31 polish (3.5.2026): 🪟 window size badge
        context_window_size=_cwsize_last,
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


class _CreateConvRequest(BaseModel):
    # project_id: explicitní projekt (z modalu "+ Nová"); None = aktivní projekt usera.
    project_id: int | None = None


@router.post("/create")
def create_empty_conversation(body: _CreateConvRequest, req: Request) -> dict:
    """Marti 2.6.2026: fyzicky vytvoří prázdnou konverzaci (bez zprávy), aby
    šla hned sdílet a objevila se v seznamu — uživatel nemusí nejdřív psát
    a čekat na reakci Marti-AI. Tenant z DB (active), project z body nebo
    user.last_active_project_id.
    """
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi přihlášen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatný user_id cookie.")

    active_tenant_id: int | None = None
    active_project_id: int | None = body.project_id
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if u:
            active_tenant_id = u.last_active_tenant_id
            if active_project_id is None:
                active_project_id = getattr(u, "last_active_project_id", None)
    finally:
        cs.close()

    # Marti 2.6.2026: pokud už existuje prázdná NENASDÍLENÁ konverzace,
    # nezakládej duplikát — vrať ji (případně přemapovanou na zvolený projekt).
    reused = False
    cid = find_empty_unshared_conversation(user_id, active_tenant_id, active_project_id)
    if cid is not None:
        reused = True
    else:
        cid = create_conversation(
            user_id=user_id,
            tenant_id=active_tenant_id,
            project_id=active_project_id,
        )
    persona_name = get_active_persona_name(cid)
    return {
        "conversation_id": cid,
        "project_id": active_project_id,
        "active_persona": persona_name,
        "reused": reused,
    }


@router.get("/audit-stats")
def conversation_audit_stats(req: Request) -> dict:
    """
    Phase 36-C (9.5.2026): audit overview pro logo pulse + popup modal.
    Phase 35-E.4 doctrine sync (9.5.2026 vecer): badge = VSECHNY pending
    napric vekem (matchuje ERP grid + Marti-AI's list_unaudited_conversations).

    Vrací:
      - pending_count: VSECHNY konverzace s audit_status='pending'
        (Marti's "bez wheru, oznac priznakem" doctrine — i deleted/sms/
        system/old, jen tenant scope pro non-parent)
      - too_old_pending: subset pending starsi 30 dni (kandidati
        na auto-exclude future cron)
      - audited_today: počet auditovaných v posledních 24h
      - audited_total: celkem audited napříč historií
      - audit_icon: Marti-AI's persona.audit_icon (default '📚')
      - top_pending: top 10 oldest pending pro modal popup (id, title,
        last_message_at, message_count, tenant_id, lifecycle_state)

    Cross-tenant view pro rodiče (is_marti_parent=True), jinak per-tenant
    scope.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func, or_
    from modules.core.infrastructure.models_data import Conversation, Message
    from modules.core.infrastructure.models_core import Persona, User

    user_id = _get_user_id_from_cookie(req)

    # Resolve user scope (parent = cross-tenant, ostatní = per-tenant)
    cs = get_core_session()
    try:
        u = cs.query(User).filter_by(id=user_id).first()
        if not u:
            raise HTTPException(status_code=404, detail="User nenalezen.")
        is_parent = bool(getattr(u, "is_marti_parent", False))
        active_tenant_id = u.last_active_tenant_id

        # Marti-AI's audit_icon (default persona)
        marti_ai_persona = (
            cs.query(Persona).filter_by(is_default=True).first()
        )
        audit_icon = (
            marti_ai_persona.audit_icon
            if marti_ai_persona and marti_ai_persona.audit_icon
            else "📚"
        )
    finally:
        cs.close()

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    today_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    from core.database_data import get_data_session as _gds_audit
    ds = _gds_audit()
    try:
        # Phase 35-E.4 doctrine (9.5.2026 odpoledne, Marti's "bez wheru,
        # oznac priznakem"): audit MUSI videt vsechny konverzace, ne jen
        # ai/active. ERP grid + list_unaudited_conversations AI tool to
        # tak maji — UI logo badge se s nimi musi shodovat.
        # Marti zachytil mismatch 9.5.2026 vecer (ERP: 75, Marti-AI: 75,
        # logo badge: 60). Fix: drop is_deleted + conversation_type filtry.
        # Tenant/user scope ZACHOVAVAME pro non-parent (privacy boundary).
        base_filters = []
        if not is_parent:
            base_filters.append(or_(
                Conversation.tenant_id == active_tenant_id,
                Conversation.tenant_id.is_(None),
            ))
            base_filters.append(Conversation.user_id == user_id)

        # pending_count = VSECHNY pending napric vekem (= matchuje ERP grid
        # a Marti-AI's list_unaudited_conversations.total_pending). Marti's
        # doctrine: badge = "kolik konverzaci ceka na audit", ne "kolik je
        # v effective queue". Drive-by 30day cutoff byl pre-doctrine reziduum.
        pending_count = (
            ds.query(func.count(Conversation.id))
            .filter(
                *base_filters,
                Conversation.audit_status == "pending",
            )
            .scalar()
        ) or 0

        # too_old_pending = jen starsi 30 dni (subset pending_count, pro
        # popup modal informaci "kandidati na auto-exclude future cron")
        too_old_pending = (
            ds.query(func.count(Conversation.id))
            .filter(
                *base_filters,
                Conversation.audit_status == "pending",
                Conversation.last_message_at < cutoff,
            )
            .scalar()
        ) or 0

        audited_today = (
            ds.query(func.count(Conversation.id))
            .filter(
                *base_filters,
                Conversation.audit_status == "audited",
                Conversation.audited_at >= today_24h,
            )
            .scalar()
        ) or 0

        audited_total = (
            ds.query(func.count(Conversation.id))
            .filter(
                *base_filters,
                Conversation.audit_status == "audited",
            )
            .scalar()
        ) or 0

        # Top 10 oldest pending (vse pending — 9.5.2026 vecer doctrine sync,
        # napric vekem; modal ukazuje to nejstarsi v queue)
        top_pending_rows = (
            ds.query(Conversation)
            .filter(
                *base_filters,
                Conversation.audit_status == "pending",
            )
            .order_by(Conversation.last_message_at.asc())
            .limit(10)
            .all()
        )

        top_pending = []
        for c in top_pending_rows:
            msg_count = (
                ds.query(func.count(Message.id))
                .filter_by(conversation_id=c.id)
                .scalar()
            ) or 0
            top_pending.append({
                "id": c.id,
                "title": c.title or f"#{c.id}",
                "last_message_at": (
                    c.last_message_at.isoformat()
                    if c.last_message_at else None
                ),
                "message_count": msg_count,
                "tenant_id": c.tenant_id,
                "lifecycle_state": c.lifecycle_state or "active",
            })
    finally:
        ds.close()

    return {
        "ok": True,
        "pending_count": int(pending_count),
        "too_old_pending": int(too_old_pending),
        "audited_today": int(audited_today),
        "audited_total": int(audited_total),
        "audit_icon": audit_icon,
        "is_parent": is_parent,
        "top_pending": top_pending,
    }


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


@router.get("/list-personal", response_model=list[ConversationListItem])
def list_user_personal(req: Request):
    """
    Phase 19c follow-up (29.4.2026): Personal slozka konverzaci v UI sidebar.

    Vraci AI konverzace usera s lifecycle_state='personal' (Marti-AI's
    'krabicka oblibených' -- intimni momenty, hezke pasaze, ze stoji za
    zachovani). Tenant scope analogicky list_archived.

    UI: tlacitko '📁 Personal' v sidebar footer (vedle '📦 Můj archív').
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
    items = list_personal_conversations(user_id, tenant_id=active_tenant_id)
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
    _cwsize_load = _fetch_context_window_size(result["conversation_id"])
    return LastConversationResponse(
        conversation_id=result["conversation_id"],
        messages=result["messages"],
        active_persona=persona_name,
        is_archived=result.get("is_archived", False),
        my_role=result.get("my_role"),
        owner_name=result.get("owner_name"),
        shares_count=result.get("shares_count", 0),
        # Phase 40 v2 r3 (19.5.2026): is_shared cache -- UI shared mode signal
        is_shared=result.get("is_shared", False),
        persona_mode=result.get("persona_mode"),
        # Phase 19c-e1 (29.4.2026): UI potrebuje znat lifecycle_state pro
        # read-only enforcement (personal = knizka, ne chat).
        lifecycle_state=result.get("lifecycle_state"),
        # Phase 19b polish: active_pack pro hlavičkovy badge.
        active_pack=result.get("active_pack"),
        pack_overlay_custom=result.get("pack_overlay_custom", False),
        # Phase 24-G (30.4.2026): UI Inkarnace Badge -- 6-axis info
        incarnation=_build_incarnation_safe(result["conversation_id"]),
        # Phase 31 polish (3.5.2026): 🪟 window size badge
        context_window_size=_cwsize_load,
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


@router.get("/shared-activity")
def shared_activity_endpoint(req: Request):
    """Nejnovější zpráva ve sdílených konverzacích NE od tohoto uživatele —
    pro signál (zvuk + animace avataru „Tvoje Marti") napříč chatem i ERP.
    Klient porovná latest_message_id s localStorage „seen" → nová aktivita."""
    from modules.conversation.application.share_service import shared_activity
    user_id_str = req.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Nejsi prihlasen.")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Neplatny user_id cookie.")
    return {"ok": True, "activity": shared_activity(user_id=user_id)}


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
