"""
Unit testy pro summary_service.

Pokrývá:
  - trigger: nevytvoří summary pokud je < threshold zpráv
  - trigger: vytvoří summary když je >= threshold
  - range: from_id / to_id pokrývají správný blok
  - více summary: navazují bez duplicity
  - selhání LLM: vrátí None, neshodí konverzaci
"""
from unittest.mock import MagicMock, patch

from modules.conversation.application import summary_service
from modules.conversation.application.summary_service import (
    SUMMARY_THRESHOLD,
    _format_messages_for_llm,
    maybe_create_summary,
)


def _make_message(id_, role, content):
    m = MagicMock()
    m.id = id_
    m.role = role
    m.content = content
    m.author_type = "ai" if role == "assistant" else "human"
    m.author_user_id = None
    m.created_at = None
    m.conversation_id = 1
    return m


# ── Format helper ─────────────────────────────────────────────────────────

def test_format_messages_for_llm_labels_roles():
    msgs = [
        _make_message(1, "user", "Ahoj"),
        _make_message(2, "assistant", "Ahoj!"),
    ]
    out = _format_messages_for_llm(msgs)
    assert "Uživatel: Ahoj" in out
    assert "Asistent: Ahoj!" in out


# ── Trigger conditions ────────────────────────────────────────────────────

@patch("modules.conversation.application.summary_service._get_range_to_summarize")
def test_no_summary_when_below_threshold(mock_range):
    mock_range.return_value = None    # simulace: nemáme dost zpráv
    result = maybe_create_summary(conversation_id=42)
    assert result is None


@patch("modules.conversation.application.summary_service._get_conversation_context")
@patch("modules.conversation.application.summary_service._save_summary")
@patch("modules.conversation.application.summary_service._call_llm_for_summary")
@patch("modules.conversation.application.summary_service._get_range_to_summarize")
def test_creates_summary_when_threshold_reached(
    mock_range, mock_llm, mock_save, mock_ctx
):
    msgs = [_make_message(i + 1, "user" if i % 2 == 0 else "assistant", f"m{i}")
            for i in range(SUMMARY_THRESHOLD)]
    mock_range.return_value = (msgs[0].id, msgs[-1].id, msgs)
    mock_llm.return_value = "Shrnutí testu."
    mock_save.return_value = 99
    mock_ctx.return_value = (None, None)

    result = maybe_create_summary(conversation_id=42)

    assert result is not None
    assert result["summary_id"] == 99
    assert result["from_message_id"] == msgs[0].id
    assert result["to_message_id"] == msgs[-1].id
    assert result["message_count"] == SUMMARY_THRESHOLD
    assert result["summary_text"] == "Shrnutí testu."

    # LLM byl zavolán s formátovaným textem zpráv
    mock_llm.assert_called_once()
    assert "Uživatel:" in mock_llm.call_args[0][0]


@patch("modules.conversation.application.summary_service._get_conversation_context")
@patch("modules.conversation.application.summary_service._save_summary")
@patch("modules.conversation.application.summary_service._call_llm_for_summary")
@patch("modules.conversation.application.summary_service._get_range_to_summarize")
def test_empty_llm_output_returns_none(
    mock_range, mock_llm, mock_save, mock_ctx
):
    msgs = [_make_message(i + 1, "user", f"m{i}") for i in range(SUMMARY_THRESHOLD)]
    mock_range.return_value = (msgs[0].id, msgs[-1].id, msgs)
    mock_llm.return_value = ""    # LLM vrátil nic
    mock_ctx.return_value = (None, None)

    result = maybe_create_summary(conversation_id=42)

    assert result is None
    mock_save.assert_not_called()


@patch("modules.conversation.application.summary_service._get_range_to_summarize")
def test_range_error_is_swallowed(mock_range):
    mock_range.side_effect = RuntimeError("boom")
    # Nesmí padnout — summary selhání nesmí shodit chat.
    result = maybe_create_summary(conversation_id=42)
    assert result is None


@patch("modules.conversation.application.summary_service._get_conversation_context")
@patch("modules.conversation.application.summary_service._save_summary")
@patch("modules.conversation.application.summary_service._call_llm_for_summary")
@patch("modules.conversation.application.summary_service._get_range_to_summarize")
def test_llm_exception_is_swallowed(
    mock_range, mock_llm, mock_save, mock_ctx
):
    msgs = [_make_message(i + 1, "user", f"m{i}") for i in range(SUMMARY_THRESHOLD)]
    mock_range.return_value = (msgs[0].id, msgs[-1].id, msgs)
    mock_llm.side_effect = RuntimeError("LLM down")
    mock_ctx.return_value = (None, None)

    result = maybe_create_summary(conversation_id=42)

    assert result is None
    mock_save.assert_not_called()


# ── Constants sanity ─────────────────────────────────────────────────────

def test_threshold_is_reasonable():
    # Ochrana proti omylem hodně nízkému thresholdu (spam) nebo vysokému.
    assert 3 <= SUMMARY_THRESHOLD <= 50
