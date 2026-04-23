"""
Unit tests pro router_service (Fáze 9.1).

Testuje parsing + validaci + prior-only klasifikaci. NETESTUJE live API call
(to by vyžadovalo anthropic_api_key + rate limit + flaky).
"""
import pytest

from modules.conversation.application.router_service import (
    _parse_router_output,
    _validate_and_normalize,
    infer_prior_mode,
    DEFAULT_MODE,
    VALID_MODES,
)


# ── Parser tests ───────────────────────────────────────────────────────────

def test_parse_plain_json():
    raw = '{"mode": "personal", "confidence": 0.9, "project_id": null, "reason": "ok", "secondary_hints": []}'
    out = _parse_router_output(raw)
    assert out is not None
    assert out["mode"] == "personal"
    assert out["confidence"] == 0.9


def test_parse_markdown_wrapped_json():
    raw = '```json\n{"mode": "project", "confidence": 0.8, "project_id": 42, "reason": "x"}\n```'
    out = _parse_router_output(raw)
    assert out is not None
    assert out["mode"] == "project"
    assert out["project_id"] == 42


def test_parse_json_with_trailing_text():
    raw = '{"mode": "system", "confidence": 0.6} \n\nAdditional explanation here'
    out = _parse_router_output(raw)
    assert out is not None
    assert out["mode"] == "system"


def test_parse_unparseable_returns_none():
    assert _parse_router_output("not a json at all") is None
    assert _parse_router_output("") is None
    assert _parse_router_output(None) is None


# ── Validator tests ────────────────────────────────────────────────────────

def test_validate_valid_mode_passes():
    raw = {"mode": "project", "confidence": 0.85, "project_id": 12, "reason": "OK"}
    out = _validate_and_normalize(raw, ui_state=None)
    assert out["mode"] == "project"
    assert out["project_id"] == 12
    assert out["confidence"] == 0.85


def test_validate_invalid_mode_falls_back():
    raw = {"mode": "WEIRD_MODE", "confidence": 0.9}
    out = _validate_and_normalize(raw, ui_state=None)
    assert out["mode"] == DEFAULT_MODE


def test_validate_confidence_clamped():
    raw = {"mode": "personal", "confidence": 1.5}
    assert _validate_and_normalize(raw, None)["confidence"] == 1.0

    raw2 = {"mode": "personal", "confidence": -0.2}
    assert _validate_and_normalize(raw2, None)["confidence"] == 0.0


def test_validate_project_id_from_ui_when_mode_project_missing():
    raw = {"mode": "project", "confidence": 0.8, "project_id": None}
    ui = {"active_project_id": 99}
    out = _validate_and_normalize(raw, ui_state=ui)
    assert out["project_id"] == 99


def test_validate_secondary_hints_list_capped():
    raw = {
        "mode": "personal",
        "confidence": 0.5,
        "secondary_hints": ["a", "b", "c", "d", "e", "f", "g"],  # 7
    }
    out = _validate_and_normalize(raw, None)
    assert len(out["secondary_hints"]) == 5


def test_validate_non_dict_secondary_becomes_empty():
    raw = {"mode": "personal", "confidence": 0.5, "secondary_hints": "not a list"}
    out = _validate_and_normalize(raw, None)
    assert out["secondary_hints"] == []


# ── Prior-only (deterministic) classifier tests ────────────────────────────

def test_prior_active_project_returns_project_mode():
    ui = {"active_project_id": 7, "active_tenant_id": 1}
    out = infer_prior_mode(ui)
    assert out["mode"] == "project"
    assert out["project_id"] == 7


def test_prior_personal_tenant_returns_personal():
    ui = {"active_tenant_id": 1, "tenant_type": "personal"}
    out = infer_prior_mode(ui)
    assert out["mode"] == "personal"


def test_prior_work_tenant_no_project_returns_work():
    ui = {"active_tenant_id": 2, "tenant_type": "business"}
    out = infer_prior_mode(ui)
    assert out["mode"] == "work"


def test_prior_empty_ui_falls_back_personal():
    out = infer_prior_mode(None)
    assert out["mode"] == DEFAULT_MODE
    assert out["confidence"] < 0.5


def test_prior_project_id_invalid_becomes_none():
    ui = {"active_project_id": "not-an-int"}
    out = infer_prior_mode(ui)
    # Mode se stále nastavi na project (UI říká že je aktivní),
    # ale project_id fallbackne na None
    assert out["mode"] == "project"
    assert out["project_id"] is None


# ── Sanity ─────────────────────────────────────────────────────────────────

def test_valid_modes_set():
    assert VALID_MODES == {"personal", "project", "work", "system"}


def test_default_mode_is_valid():
    assert DEFAULT_MODE in VALID_MODES
