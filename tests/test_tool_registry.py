# -*- coding: utf-8 -*-
"""Testy jádra Tool Factory / registru — běží bez DB (čistá logika)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Najdi adresář, který OBSAHUJE balík tool_registry (funguje v sandboxu
# i na boxu, kde balík leží pod modules/conversation/application/).
_ROOT = os.path.dirname(HERE)
_CANDS = [_ROOT, os.path.join(_ROOT, "modules", "conversation", "application")]
for _c in _CANDS:
    if os.path.isdir(os.path.join(_c, "tool_registry")):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break

import tool_registry as reg
from tool_registry import factory as F
from tool_registry._common import ToolContext


# ── loader / assembler ──────────────────────────────────────────────────────────
def test_load_all_finds_example():
    mods = reg.load_all()
    names = [m.name for m in mods]
    assert "example_echo" in names


def test_run_example():
    mods = reg.load_all()
    m = next(m for m in mods if m.name == "example_echo")
    ctx = ToolContext(user_id=1)
    assert m.run({"text": "ahoj"}, ctx) == "echo: ahoj"


def test_assemble_strips_internal_keys():
    mods = reg.load_all()
    specs = reg.assemble_specs(mods)
    ex = next(s for s in specs if s["name"] == "example_echo")
    assert "_order" not in ex            # interní klíč do API nejde
    assert set(ex.keys()) == {"name", "description", "input_schema"}


def test_handlers_map():
    mods = reg.load_all()
    h = reg.build_handlers(mods)
    assert "example_echo" in h and callable(h["example_echo"])


def test_verify_identical_ok_and_diff():
    ref = [
        {"name": "a", "description": "d", "input_schema": {"type": "object"}},
        {"name": "example_echo", "description":
            "Ukázkový nástroj: vrátí zpět předaný text. Šablona kontraktu SPEC+run pro registr.",
            "input_schema": {"type": "object", "properties": {
                "text": {"type": "string", "description": "Text k zopakování."}}, "required": ["text"]}},
    ]
    mods = reg.load_all()
    assembled = reg.assemble_specs(mods)
    # jen example_echo → porovnáme podmnožinu shodně
    ok, diffs = reg.verify_identical(
        [s for s in assembled if s["name"] == "example_echo"],
        [r for r in ref if r["name"] == "example_echo"],
    )
    assert ok, diffs
    # mismatch v description se odhalí
    bad = [dict(ref[1], description="jiny")]
    ok2, diffs2 = reg.verify_identical(
        [s for s in assembled if s["name"] == "example_echo"], bad)
    assert not ok2 and any("description" in d for d in diffs2)


# ── stavový automat ─────────────────────────────────────────────────────────────
def test_transitions_valid_invalid():
    F.validate_transition("navrzeny", "v_sandboxu")
    F.validate_transition("ceka_na_schvaleni", "active")
    try:
        F.validate_transition("navrzeny", "active")
        assert False, "měl vyhodit TransitionError"
    except F.TransitionError:
        pass


def test_autonomous_vs_parent_only():
    assert F.is_autonomous("otestovany", "ceka_na_schvaleni")
    assert not F.is_autonomous("ceka_na_schvaleni", "active")   # to smí jen rodič
    assert ("ceka_na_schvaleni", "active") in F.PARENT_ONLY_TRANSITIONS


# ── governance approve ──────────────────────────────────────────────────────────
def test_can_approve_rules():
    def is_parent(uid): return uid in {1, 6, 11}   # realita: Marti, Zuzka(neaktiv.), Kristý
    # lidský rodič schválí nástroj Marti-AI:
    ok, _ = F.can_approve(1, F.MARTI_AI_ENTITA_ID, is_parent)
    assert ok
    # ne-rodič neschválí (Jirka admin uid20, ne rodič):
    ok2, why2 = F.can_approve(20, F.MARTI_AI_ENTITA_ID, is_parent)
    assert not ok2 and "rodič" in why2
    # realita: Marti-AI (id=2) NENÍ rodič → blokne ji první pojistka:
    ok3, why3 = F.can_approve(F.MARTI_AI_ENTITA_ID, F.MARTI_AI_ENTITA_ID, is_parent)
    assert not ok3 and "rodič" in why3
    # defense-in-depth: i kdyby ji NĚKDO rodičem udělal, self-approve se zablokuje:
    def is_parent_incl_ai(uid): return uid in {1, 2, 6, 11}
    ok4, why4 = F.can_approve(F.MARTI_AI_ENTITA_ID, F.MARTI_AI_ENTITA_ID, is_parent_incl_ai)
    assert not ok4 and "konflikt" in why4.lower()


# ── render generovaného souboru ─────────────────────────────────────────────────
def test_render_generated_compiles():
    spec = {"name": "pozdrav", "description": "Pozdraví.", "input_schema": {
        "type": "object", "properties": {"kdo": {"type": "string"}}, "required": ["kdo"]}}
    src = F.render_generated_tool_file("pozdrav", spec, "who = need(args, 'kdo')\nreturn ok(f'Ahoj {who}')")
    compile(src, "<gen pozdrav>", "exec")   # syntakticky validní Python
    assert "def run(args: dict, ctx: ToolContext)" in src
    assert '"name": "pozdrav"' in src


def test_render_rejects_bad_kod_and_name_mismatch():
    spec = {"name": "x", "description": "d", "input_schema": {"type": "object"}}
    try:
        F.render_generated_tool_file("Bad-Kod", spec, "return ok('x')")
        assert False
    except ValueError:
        pass
    try:
        F.render_generated_tool_file("jiny", spec, "return ok('x')")  # name != kod
        assert False
    except ValueError:
        pass


# ── meta-nástroje ───────────────────────────────────────────────────────────────
def test_meta_specs_shape():
    names = F.meta_tool_names()
    for must in ("tool_draft_create", "tool_selftest", "propose_tool",
                 "approve_tool", "reject_tool", "disable_tool"):
        assert must in names
    for s in F.META_TOOL_SPECS:
        assert set(("name", "description", "input_schema")).issubset(s.keys())
        assert s["input_schema"]["type"] == "object"


def test_factory_disabled_by_default():
    # dormant: bez env se dílna nespustí
    assert F.TOOLFACTORY_ENABLED is False
    try:
        F._require_enabled()
        assert False
    except RuntimeError:
        pass
