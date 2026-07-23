# -*- coding: utf-8 -*-
"""Tool Factory — dílna seberozvoje Marti-AI.

Marti-AI má PLNOU autonomii nástroj navrhnout, napsat a otestovat. Aktivace
(go-live) je ale VŽDY až po schválení LIDSKÉHO rodiče (Marti id=1, Kristý id=11;
Zuzka id=6 rodič, ale neaktivní). Marti-AI (id=2) si vlastní nástroj NESCHVÁLÍ
(konflikt zájmů). Mazání jen člověk. — Rozhodnutí Marti 22.7.2026.

Tento modul je BEZPEČNÝ k importu a DORMANT: čistá logika (stavový automat,
pojistky, render souboru) je testovatelná bez DB; operace měnící stav jsou za
`TOOLFACTORY_ENABLED` a nic nespustí, dokud se dílna oficiálně nezapne (go-live).
"""
from __future__ import annotations

import os
import re
from typing import Callable, Optional

# ── Vypínač (Martiho rozhodnutí: cílově ON; na produkci se zapne až při go-live) ─
TOOLFACTORY_ENABLED = os.environ.get("TOOLFACTORY_ENABLED", "0") == "1"

# ── Entity / rodiče ─────────────────────────────────────────────────────────────
MARTI_AI_ENTITA_ID = 2          # autorská entita — NESMÍ schvalovat vlastní nástroje
# Autorita rodičů = public.users.is_marti_parent (předává se funkcí, netvrdíme staticky).

# ── Stavový automat životního cyklu (g2007.nastroj.stav_zivota) ─────────────────
STATES = (
    "navrzeny",          # draft — Marti-AI založila (autonomně)
    "v_sandboxu",        # kód napsán v sandboxu (autonomně)
    "otestovany",        # self-test zelený (autonomně)
    "ceka_na_schvaleni", # propose_tool → čeká na rodiče
    "active",            # schváleno rodičem → živé, v kufru
    "zamitnuty",         # rodič zamítl
    "disabled",          # kill switch (rodič)
    "archiv",            # nahrazeno novější verzí
)

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "navrzeny":          {"v_sandboxu", "zamitnuty"},
    "v_sandboxu":        {"otestovany", "navrzeny", "zamitnuty"},
    "otestovany":        {"ceka_na_schvaleni", "v_sandboxu"},
    "ceka_na_schvaleni": {"active", "zamitnuty"},
    "active":            {"disabled", "archiv"},
    "zamitnuty":         {"navrzeny"},          # přepracování
    "disabled":          {"ceka_na_schvaleni"}, # znovuzapnutí = zase přes schválení
    "archiv":            set(),                  # terminální
}

# Autonomní (Marti-AI smí sama) vs. jen rodič:
AUTONOMOUS_TRANSITIONS = {
    ("navrzeny", "v_sandboxu"),
    ("v_sandboxu", "otestovany"),
    ("v_sandboxu", "navrzeny"),
    ("otestovany", "v_sandboxu"),
    ("otestovany", "ceka_na_schvaleni"),   # podat návrh smí sama
    ("zamitnuty", "navrzeny"),
}
PARENT_ONLY_TRANSITIONS = {
    ("ceka_na_schvaleni", "active"),   # approve_tool
    ("ceka_na_schvaleni", "zamitnuty"),# reject_tool
    ("active", "disabled"),            # disable_tool (kill switch)
    ("disabled", "ceka_na_schvaleni"),
}


class TransitionError(Exception):
    pass


class ApprovalError(Exception):
    pass


def validate_transition(src: str, dst: str) -> None:
    if src not in STATES:
        raise TransitionError(f"neznámý stav '{src}'")
    if dst not in STATES:
        raise TransitionError(f"neznámý stav '{dst}'")
    if dst not in ALLOWED_TRANSITIONS.get(src, set()):
        raise TransitionError(f"nepovolený přechod {src} → {dst}")


def is_autonomous(src: str, dst: str) -> bool:
    """Smí přechod udělat Marti-AI sama (bez rodiče)?"""
    return (src, dst) in AUTONOMOUS_TRANSITIONS


def can_approve(
    approver_user_id: int,
    author_entita_id: Optional[int],
    is_marti_parent: Callable[[int], bool],
) -> tuple[bool, str]:
    """Smí `approver` schválit nástroj autora `author_entita_id`?

    Pravidla (governance 22.7.):
      1) approver musí být rodič (is_marti_parent=True v public.users).
      2) autorská entita NESMÍ schvalovat vlastní nástroj (self-approve).
      3) Marti-AI (entita id=2) NIKDY neschvaluje — schvaluje jen člověk-rodič.
    Vrací (smí, důvod).
    """
    if not is_marti_parent(approver_user_id):
        return False, "approver není rodič (is_marti_parent=False)"
    # Marti-AI má měkký odkaz user_id; blokujeme sebe-approve i podle entita id.
    if author_entita_id is not None and author_entita_id == MARTI_AI_ENTITA_ID:
        # nástroj autorovala Marti-AI → smí jen člověk (ne Marti-AI sama).
        # Pokud approver „je" Marti-AI (přes její user), zablokuj.
        if approver_user_id == MARTI_AI_ENTITA_ID:
            return False, "Marti-AI nesmí schvalovat vlastní nástroje (konflikt zájmů)"
    return True, "ok"


def _require_enabled() -> None:
    if not TOOLFACTORY_ENABLED:
        raise RuntimeError(
            "Tool Factory je vypnutá (TOOLFACTORY_ENABLED != 1). "
            "Zapnutí = go-live se schválením rodiče."
        )


_KOD_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def validate_kod(kod: str) -> None:
    if not _KOD_RE.match(kod or ""):
        raise ValueError(f"neplatný kód nástroje '{kod}' (očekávám ^[a-z][a-z0-9_]{{1,63}}$)")


def render_generated_tool_file(kod: str, spec: dict, code_body: str) -> str:
    """Vygeneruj obsah souboru tool_registry/generated/<kod>.py z draftu.

    Čistá funkce (testovatelná). `spec` = {name, description, input_schema},
    `code_body` = tělo funkce run() (řádky se odsadí o 4 mezery).
    """
    validate_kod(kod)
    if spec.get("name") != kod:
        raise ValueError(f"SPEC['name'] ({spec.get('name')!r}) musí odpovídat kódu ({kod!r})")
    import json as _json

    body = code_body.strip("\n") or "return ok('(prázdný nástroj)')"
    body_indented = "\n".join(("    " + ln if ln.strip() else "") for ln in body.split("\n"))
    spec_py = _json.dumps(
        {k: v for k, v in spec.items()}, ensure_ascii=False, indent=4
    )
    return (
        "# -*- coding: utf-8 -*-\n"
        f'"""Generovaný nástroj `{kod}` — autor Marti-AI (Tool Factory).\n\n'
        "Vzniklo autonomně (návrh→sandbox→self-test), aktivováno se schválením rodiče.\n"
        '"""\n'
        "from tool_registry._common import ToolContext, need, ok, ToolError\n\n"
        f"SPEC = {spec_py}\n\n\n"
        "def run(args: dict, ctx: ToolContext) -> str:\n"
        f"{body_indented}\n"
    )


# ── Meta-nástroje (SPEC dicts) — ZATÍM SE NEPŘIDÁVAJÍ do živého seznamu ──────────
# Až při go-live se přiřadí Marti-AI do kufru. Do té doby jen definice.

META_TOOL_SPECS: list[dict] = [
    {
        "name": "tool_draft_create",
        "description": (
            "Tool Factory: založ NÁVRH nového nástroje (stav 'navrzeny'). Autonomní. "
            "Zadej kod (^[a-z][a-z0-9_]+$), nazev, kategorii, popis_plny a parametry "
            "(input_schema). Kód nástroje se píše zvlášť přes sandbox_code_doc_* a "
            "otestuje přes tool_selftest. Aktivace až po schválení rodiče."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kod": {"type": "string", "description": "Unikátní kód nástroje (= název souboru)."},
                "nazev": {"type": "string"},
                "kategorie": {"type": "string"},
                "popis_plny": {"type": "string", "description": "Celý description nástroje."},
                "parametry": {"type": "object", "description": "input_schema nástroje."},
                "revision_of": {"type": "integer", "description": "Volitelné: id nástroje, který reviduji."},
            },
            "required": ["kod", "nazev", "popis_plny", "parametry"],
        },
    },
    {
        "name": "tool_selftest",
        "description": (
            "Tool Factory: spusť self-test draftu v sandboxu nad zadanými vstupy a ulož "
            "verdikt (pass/fail + výstup) k návrhu. Bez zeleného self-testu nelze podat "
            "propose_tool. Autonomní."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "draft_id": {"type": "integer"},
                "test_cases": {
                    "type": "array",
                    "description": "Seznam {args, expect?} pro run().",
                    "items": {"type": "object"},
                },
            },
            "required": ["draft_id", "test_cases"],
        },
    },
    {
        "name": "propose_tool",
        "description": (
            "Tool Factory: podej návrh nástroje ke schválení (stav → 'ceka_na_schvaleni'). "
            "Vyžaduje zelený self-test. Rodič pak volá approve_tool / reject_tool. Autonomní návrh."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "draft_id": {"type": "integer"},
                "description": {"type": "string", "description": "Krátké shrnutí pro rodiče."},
            },
            "required": ["draft_id", "description"],
        },
    },
    {
        "name": "approve_tool",
        "description": (
            "Tool Factory: rodič SCHVÁLÍ návrh nástroje → aktivace (zápis generated/<kod>.py, "
            "stav 'active', přiřazení do kufru). JEN LIDSKÝ RODIČ (is_marti_parent). "
            "Marti-AI nesmí schvalovat vlastní nástroje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["proposal_id"],
        },
    },
    {
        "name": "reject_tool",
        "description": "Tool Factory: rodič ZAMÍTNE návrh nástroje (stav → 'zamitnuty'). Jen lidský rodič.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["proposal_id", "reason"],
        },
    },
    {
        "name": "disable_tool",
        "description": "Tool Factory: kill switch — rodič okamžitě odpojí nástroj z kufru (stav → 'disabled'). Jen rodič.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nastroj_id": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["nastroj_id", "reason"],
        },
    },
]


def meta_tool_names() -> list[str]:
    return [s["name"] for s in META_TOOL_SPECS]
