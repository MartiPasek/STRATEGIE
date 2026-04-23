"""
Unit testy pro scope_overlays (Fáze 9.3).
"""
import pytest

from modules.conversation.application.scope_overlays import (
    build_overlay_for_mode,
    list_overlay_names,
    VALID_MODES,
    PERSONAL_OVERLAY,
    SYSTEM_OVERLAY,
)


def test_valid_modes_set():
    assert VALID_MODES == {"personal", "project", "work", "system"}


def test_list_overlay_names():
    assert list_overlay_names() == ["personal", "project", "system", "work"]


# ── personal ──────────────────────────────────────────────────────────────

def test_personal_overlay_basic():
    out = build_overlay_for_mode("personal")
    assert out is not None
    assert "PERSONAL MODE" in out
    assert "record_thought" in out
    assert "record_diary_entry" in out


def test_personal_overlay_no_template_vars_needed():
    """Personal mode je stateless -- bez parametrů funguje."""
    assert build_overlay_for_mode("personal") is not None


# ── project ───────────────────────────────────────────────────────────────

def test_project_overlay_with_name():
    out = build_overlay_for_mode(
        "project",
        project_name="STRATEGIE",
        project_id=42,
    )
    assert out is not None
    assert "STRATEGIE" in out
    assert "id=42" in out
    assert "rag_search" in out


def test_project_overlay_missing_name_uses_fallback():
    out = build_overlay_for_mode("project", project_id=42)
    assert out is not None
    assert "(neznámý projekt)" in out
    assert "id=42" in out


def test_project_overlay_missing_id_uses_fallback():
    out = build_overlay_for_mode("project", project_name="X")
    assert out is not None
    assert "X" in out
    assert "id=?" in out


# ── work ──────────────────────────────────────────────────────────────────

def test_work_overlay_with_name():
    out = build_overlay_for_mode("work", tenant_name="EUROSOFT", tenant_id=2)
    assert out is not None
    assert "EUROSOFT" in out
    assert "id=2" in out


def test_work_overlay_no_params_fallback():
    out = build_overlay_for_mode("work")
    assert out is not None
    assert "(neznámý tenant)" in out


# ── system ────────────────────────────────────────────────────────────────

def test_system_overlay_basic():
    out = build_overlay_for_mode("system")
    assert out is not None
    assert "SYSTEM MODE" in out
    assert "backup" in out.lower() or "Backup" in out


def test_system_overlay_no_personal_content():
    """
    System mode nemá obsahovat vyloženě osobní / rodinná témata
    (diář, vzpomínky, rodinné události). Zmínka "rodiče" v kontextu
    oprávnění (is_marti_parent) je legitimní -- proto kontrolujeme
    konkrétnější slova.
    """
    out = build_overlay_for_mode("system").lower()
    assert "diář" not in out
    assert "vzpomín" not in out     # vzpomínky, vzpomínáš
    assert "rodinn" not in out      # rodinný, rodinné (ne "rodiče")
    assert "record_diary_entry" not in out
    assert "record_thought" not in out


# ── dispatcher edge cases ─────────────────────────────────────────────────

def test_unknown_mode_returns_none():
    assert build_overlay_for_mode("invalid") is None
    assert build_overlay_for_mode("") is None
    assert build_overlay_for_mode("PERSONAL") is None  # case-sensitive


def test_all_valid_modes_return_text():
    """Každý validní mode vrátí nějaký text (ne None)."""
    for mode in VALID_MODES:
        out = build_overlay_for_mode(
            mode,
            project_name="test", project_id=1,
            tenant_name="test", tenant_id=1,
        )
        assert out is not None
        assert len(out) > 100  # nenulový obsah


# ── sanity ────────────────────────────────────────────────────────────────

def test_constants_are_strings():
    assert isinstance(PERSONAL_OVERLAY, str)
    assert isinstance(SYSTEM_OVERLAY, str)
    assert len(PERSONAL_OVERLAY) > 200
    assert len(SYSTEM_OVERLAY) > 200
