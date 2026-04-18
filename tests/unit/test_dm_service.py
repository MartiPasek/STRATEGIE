"""
Unit testy pro DM service (business vrstva user-to-user chatu).

Všechny I/O závislosti (repository funkce + save_message) jsou namockované.
Testy pokrývají: pairing, tenant guard, self-chat guard, disabled user guard,
existence check, send_dm flow, NotParticipant guard.
"""
from unittest.mock import MagicMock, patch

import pytest

from modules.conversation.application import dm_service
from modules.conversation.application.dm_service import (
    SelfChatNotAllowed,
    TargetUserDisabled,
    TargetUserNotFound,
    TenantMismatch,
    NotParticipant,
    DMError,
)


# ── START DM ─────────────────────────────────────────────────────────────

@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_rejects_self_chat(mock_repo):
    with pytest.raises(SelfChatNotAllowed):
        dm_service.start_dm(1, 1)
    mock_repo.get_user_basic.assert_not_called()


@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_rejects_missing_target(mock_repo):
    mock_repo.get_user_basic.return_value = None
    with pytest.raises(TargetUserNotFound):
        dm_service.start_dm(1, 99)


@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_rejects_disabled_target(mock_repo):
    mock_repo.get_user_basic.return_value = {
        "user_id": 2, "first_name": "X", "last_name": "Y", "email": "x@y", "status": "disabled",
    }
    with pytest.raises(TargetUserDisabled):
        dm_service.start_dm(1, 2)


@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_rejects_tenant_mismatch(mock_repo):
    mock_repo.get_user_basic.return_value = {
        "user_id": 2, "first_name": "X", "last_name": "Y", "email": "x@y", "status": "active",
    }
    mock_repo.get_user_tenants.return_value = [1]
    mock_repo.are_users_in_same_tenant.return_value = False
    with pytest.raises(TenantMismatch):
        dm_service.start_dm(1, 2)


@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_returns_existing(mock_repo):
    mock_repo.get_user_basic.return_value = {
        "user_id": 2, "first_name": "X", "last_name": "Y", "email": "x@y", "status": "active",
    }
    mock_repo.get_user_tenants.return_value = [5]
    mock_repo.are_users_in_same_tenant.return_value = True
    mock_repo.find_dm_conversation.return_value = 123

    result = dm_service.start_dm(1, 2)

    assert result == {"conversation_id": 123, "created": False, "tenant_id": 5}
    mock_repo.create_dm_conversation.assert_not_called()


@patch("modules.conversation.application.dm_service.dm_repo")
def test_start_dm_creates_new_when_missing(mock_repo):
    mock_repo.get_user_basic.return_value = {
        "user_id": 2, "first_name": "X", "last_name": "Y", "email": "x@y", "status": "active",
    }
    mock_repo.get_user_tenants.return_value = [5]
    mock_repo.are_users_in_same_tenant.return_value = True
    mock_repo.find_dm_conversation.return_value = None
    mock_repo.create_dm_conversation.return_value = 456

    result = dm_service.start_dm(1, 2)

    assert result == {"conversation_id": 456, "created": True, "tenant_id": 5}
    mock_repo.create_dm_conversation.assert_called_once_with(1, 2, 5)


# ── PAIRING (order-insensitive) ──────────────────────────────────────────

def test_pair_function_is_order_insensitive():
    from modules.conversation.infrastructure.dm_repository import _pair
    assert _pair(1, 2) == (1, 2)
    assert _pair(2, 1) == (1, 2)
    assert _pair(7, 7) == (7, 7)  # edge, nepoužíváme v praxi (blokováno výš)


# ── SEND DM ──────────────────────────────────────────────────────────────

@patch("modules.conversation.application.dm_service.save_message")
@patch("modules.conversation.application.dm_service.dm_repo")
def test_send_dm_saves_human_message(mock_repo, mock_save):
    conv = MagicMock()
    conv.conversation_type = "dm"
    mock_repo.get_conversation.return_value = conv
    mock_repo.is_participant.return_value = True
    mock_save.return_value = 999

    result = dm_service.send_dm(requester_user_id=1, conversation_id=42, content="Ahoj!")

    assert result == {"message_id": 999, "conversation_id": 42}
    mock_save.assert_called_once()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["author_type"] == "human"
    assert kwargs["author_user_id"] == 1
    assert kwargs["agent_id"] is None
    assert kwargs["role"] == "user"
    assert kwargs["message_type"] == "text"


@patch("modules.conversation.application.dm_service.save_message")
@patch("modules.conversation.application.dm_service.dm_repo")
def test_send_dm_rejects_non_dm_conversation(mock_repo, mock_save):
    conv = MagicMock()
    conv.conversation_type = "ai"
    mock_repo.get_conversation.return_value = conv
    with pytest.raises(DMError):
        dm_service.send_dm(1, 42, "hi")
    mock_save.assert_not_called()


@patch("modules.conversation.application.dm_service.save_message")
@patch("modules.conversation.application.dm_service.dm_repo")
def test_send_dm_rejects_non_participant(mock_repo, mock_save):
    conv = MagicMock()
    conv.conversation_type = "dm"
    mock_repo.get_conversation.return_value = conv
    mock_repo.is_participant.return_value = False
    with pytest.raises(NotParticipant):
        dm_service.send_dm(1, 42, "hi")
    mock_save.assert_not_called()


@patch("modules.conversation.application.dm_service.save_message")
@patch("modules.conversation.application.dm_service.dm_repo")
def test_send_dm_rejects_empty_content(mock_repo, mock_save):
    conv = MagicMock()
    conv.conversation_type = "dm"
    mock_repo.get_conversation.return_value = conv
    mock_repo.is_participant.return_value = True
    with pytest.raises(DMError):
        dm_service.send_dm(1, 42, "   ")
    mock_save.assert_not_called()


# ── FETCH / READ ─────────────────────────────────────────────────────────

@patch("modules.conversation.application.dm_service.dm_repo")
def test_fetch_dm_messages_requires_participant(mock_repo):
    conv = MagicMock()
    conv.conversation_type = "dm"
    mock_repo.get_conversation.return_value = conv
    mock_repo.is_participant.return_value = False
    with pytest.raises(NotParticipant):
        dm_service.fetch_dm_messages(1, 42)


@patch("modules.conversation.application.dm_service.dm_repo")
def test_mark_read_requires_participant(mock_repo):
    conv = MagicMock()
    conv.conversation_type = "dm"
    mock_repo.get_conversation.return_value = conv
    mock_repo.mark_dm_read.return_value = False
    with pytest.raises(NotParticipant):
        dm_service.mark_read(1, 42, 100)


# ── USER SEARCH ──────────────────────────────────────────────────────────

@patch("modules.conversation.application.dm_service.dm_repo")
def test_search_excludes_self(mock_repo):
    mock_repo.get_user_tenants.return_value = [5]
    mock_repo.search_users_in_tenant.return_value = [
        {"user_id": 1, "first_name": "Me", "last_name": "Self", "email": "me@x", "status": "active"},
        {"user_id": 2, "first_name": "Other", "last_name": "Person", "email": "o@x", "status": "active"},
    ]
    out = dm_service.search_users_for_dm(1, "query")
    assert [u["user_id"] for u in out] == [2]


@patch("modules.conversation.application.dm_service.dm_repo")
def test_search_returns_empty_when_no_tenant(mock_repo):
    mock_repo.get_user_tenants.return_value = []
    out = dm_service.search_users_for_dm(1, "query")
    assert out == []
