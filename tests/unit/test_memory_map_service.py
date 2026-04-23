"""
Unit tests pro memory_map_service (Fáze 9.2).

Většina funkcí hitá DB, takže plné testy = integration. Tady testujeme:
  - dispatcher (build_memory_map_for_mode) -- volá správnou funkci
  - system_memory_map -- čistě statický text
  - _resolve_entity_names -- edge case prázdný input
"""
from unittest.mock import patch

import pytest

from modules.conversation.application.memory_map_service import (
    build_memory_map_for_mode,
    system_memory_map,
    _resolve_entity_names,
)


# ── system_memory_map (no DB) ──────────────────────────────────────────────

def test_system_memory_map_returns_text():
    out = system_memory_map()
    assert out is not None
    assert "SYSTEM SCOPE" in out
    assert "Backup" in out


def test_system_memory_map_has_no_personal_info():
    """System mode is admin-only — no family/personal content."""
    out = system_memory_map()
    assert "rodina" not in out.lower()
    assert "diár" not in out.lower()


# ── _resolve_entity_names edge cases ───────────────────────────────────────

def test_resolve_entity_names_empty_input():
    out = _resolve_entity_names([])
    assert out == {}


# ── dispatcher ─────────────────────────────────────────────────────────────

def test_dispatcher_unknown_mode_returns_none():
    out = build_memory_map_for_mode(mode="invalid_mode")
    assert out is None


def test_dispatcher_system_mode_returns_text():
    """System mode je čistě statický (žádná DB) -- full dispatcher test."""
    out = build_memory_map_for_mode(mode="system")
    assert out is not None
    assert "SYSTEM SCOPE" in out


def test_dispatcher_personal_calls_personal():
    """Dispatcher volá personal_memory_map když mode='personal'."""
    with patch(
        "modules.conversation.application.memory_map_service.personal_memory_map",
        return_value="STUBBED_PERSONAL",
    ) as mocked:
        out = build_memory_map_for_mode(
            mode="personal",
            user_id=1,
            tenant_id=2,
            is_parent=True,
        )
        assert out == "STUBBED_PERSONAL"
        mocked.assert_called_once_with(user_id=1, tenant_id=2, is_parent=True)


def test_dispatcher_project_calls_project():
    with patch(
        "modules.conversation.application.memory_map_service.project_memory_map",
        return_value="STUBBED_PROJECT",
    ) as mocked:
        out = build_memory_map_for_mode(
            mode="project",
            project_id=42,
            user_id=1,
        )
        assert out == "STUBBED_PROJECT"
        mocked.assert_called_once_with(project_id=42, user_id=1)


def test_dispatcher_work_calls_work():
    with patch(
        "modules.conversation.application.memory_map_service.work_memory_map",
        return_value="STUBBED_WORK",
    ) as mocked:
        out = build_memory_map_for_mode(
            mode="work",
            tenant_id=5,
            user_id=1,
        )
        assert out == "STUBBED_WORK"
        mocked.assert_called_once_with(tenant_id=5, user_id=1)


def test_dispatcher_propagates_none():
    """Pokud vnitřní mapa vrátí None, dispatcher taky None."""
    with patch(
        "modules.conversation.application.memory_map_service.personal_memory_map",
        return_value=None,
    ):
        out = build_memory_map_for_mode(mode="personal", user_id=1, tenant_id=2)
        assert out is None


def test_dispatcher_catches_exception_in_map_fn():
    """Pokud vnitřní mapa throwne, dispatcher vrací None (composer fallback)."""
    with patch(
        "modules.conversation.application.memory_map_service.personal_memory_map",
        side_effect=RuntimeError("boom"),
    ):
        out = build_memory_map_for_mode(mode="personal", user_id=1)
        assert out is None
