# -*- coding: utf-8 -*-
"""tool_registry — modulární registr nástrojů (základ Tool Factory).

Vize (Marti 22.7.2026): místo jednoho 7 420řádkového `tools.py` má každý nástroj
vlastní soubor `tool_registry/defs/<kod>.py` (a generované nástroje Marti-AI
`tool_registry/generated/<kod>.py`). Každý soubor vyexportuje:

    SPEC = {"name": ..., "description": ..., "input_schema": {...}}
    def run(args: dict, ctx) -> str:   # volitelné (generované/nové nástroje)
        ...

Loader posbírá soubory, poskládá seznam speců (v původním pořadí přes SPEC["_order"])
a mapu handlerů. Vzor je 1:1 s tím, co už v repu jede v `modules/eurosoft_mcp`
(TOOL_SPECS + TOOL_HANDLERS per soubor).

STAV: DORMANT. Tento balík zatím NIKDO neimportuje z živé cesty — nemění chování.
Zapnutí (migrace `tools.py` sem + zadrátování do dispatch) = go-live se schválením
rodiče. Loader je BEZPEČNÝ k importu: nic nedělá, dokud nezavoláš load_*().
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Callable, Optional

# Alias balíku pod krátkým jménem, ať `from tool_registry._common import ...` v def
# souborech funguje bez ohledu na to, kde balík fyzicky leží (sandbox = 'tool_registry',
# na boxu = 'modules.conversation.application.tool_registry'). setdefault = nepřepíše.
sys.modules.setdefault("tool_registry", sys.modules[__name__])

HERE = os.path.dirname(os.path.abspath(__file__))
DEFS_DIR = os.path.join(HERE, "defs")
GENERATED_DIR = os.path.join(HERE, "generated")
# Migrace ŽIVÝCH (dřív jen SPEC v defs/) nástrojů na vlastní run() — samoobslužný
# tok Marti-AI (tool_registry/migration.py). Oddělený adresář od GENERATED_DIR,
# ať se migrace existujícího nástroje nikdy neplete s nástrojem zbrusu novým.
MIGRATIONS_DIR = os.path.join(HERE, "generated_migrations")

# Vysoký default_order → nezařazené jdou na konec, ale stabilně (pak dle name).
_DEFAULT_ORDER = 10_000_000


class ToolModule:
    """Jeden načtený nástroj: jeho SPEC + volitelný run() handler + odkud pochází."""

    __slots__ = ("spec", "run", "source", "order")

    def __init__(self, spec: dict, run: Optional[Callable], source: str, order: int):
        self.spec = spec
        self.run = run
        self.source = source
        self.order = order

    @property
    def name(self) -> str:
        return self.spec["name"]


def _load_py_module(path: str):
    """Načti .py soubor jako izolovaný modul (bez zápisu do sys.modules)."""
    mod_name = "tool_registry._loaded_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"nelze načíst {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _validate_spec(spec: Any, source: str) -> None:
    if not isinstance(spec, dict):
        raise ValueError(f"{source}: SPEC musí být dict, je {type(spec).__name__}")
    for key in ("name", "description", "input_schema"):
        if key not in spec:
            raise ValueError(f"{source}: SPEC postrádá klíč '{key}'")
    if not isinstance(spec["name"], str) or not spec["name"]:
        raise ValueError(f"{source}: SPEC['name'] musí být neprázdný string")
    if not isinstance(spec["input_schema"], dict):
        raise ValueError(f"{source}: SPEC['input_schema'] musí být dict")


def load_dir(directory: str) -> list[ToolModule]:
    """Načti všechny nástroje z adresáře (soubory *.py mimo těch s '_' na začátku)."""
    out: list[ToolModule] = []
    if not os.path.isdir(directory):
        return out
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        path = os.path.join(directory, fn)
        module = _load_py_module(path)
        spec = getattr(module, "SPEC", None)
        _validate_spec(spec, fn)
        run = getattr(module, "run", None)
        if run is not None and not callable(run):
            raise ValueError(f"{fn}: run musí být callable nebo None")
        order = spec.get("_order", _DEFAULT_ORDER)
        out.append(ToolModule(spec, run, os.path.join(os.path.basename(directory), fn), int(order)))
    return out


def load_all(include_generated: bool = True) -> list[ToolModule]:
    """Načti defs/ (+ volitelně generated/). Kontroluje kolize jmen."""
    mods = load_dir(DEFS_DIR)
    if include_generated:
        mods += load_dir(GENERATED_DIR)
    seen: dict[str, str] = {}
    for m in mods:
        if m.name in seen:
            raise ValueError(f"kolize jmen nástroje '{m.name}': {seen[m.name]} vs {m.source}")
        seen[m.name] = m.source
    return mods


def _clean_spec(spec: dict) -> dict:
    """SPEC bez interních klíčů (_order apod.) — přesně to, co jde do API."""
    return {k: v for k, v in spec.items() if not k.startswith("_")}


def assemble_specs(mods: list[ToolModule]) -> list[dict]:
    """Poskládej seznam speců ve stabilním pořadí (order, pak name)."""
    ordered = sorted(mods, key=lambda m: (m.order, m.name))
    return [_clean_spec(m.spec) for m in ordered]


def build_handlers(mods: list[ToolModule]) -> dict[str, Callable]:
    """Mapa name → run() jen pro nástroje, které mají vlastní handler."""
    return {m.name: m.run for m in mods if m.run is not None}


def verify_identical(assembled: list[dict], reference: list[dict]) -> tuple[bool, list[str]]:
    """Byte/struktura kontrola: shoduje se poskládaný seznam s referencí?

    Vrací (ok, rozdíly). Používá se při migraci `tools.py` → registr, aby se
    ověřilo, že se to, co jde do API, ANI O PÍSMENO nezměnilo (stejný přístup
    jako g2007 compare-full).
    """
    diffs: list[str] = []
    a_names = [t["name"] for t in assembled]
    r_names = [t["name"] for t in reference]
    if a_names != r_names:
        only_a = [n for n in a_names if n not in set(r_names)]
        only_r = [n for n in r_names if n not in set(a_names)]
        if only_a:
            diffs.append(f"navíc v registru: {only_a}")
        if only_r:
            diffs.append(f"chybí v registru: {only_r}")
        if not only_a and not only_r:
            diffs.append("stejná jména, jiné POŘADÍ")
    ref_by_name = {t["name"]: t for t in reference}
    for t in assembled:
        r = ref_by_name.get(t["name"])
        if r is None:
            continue
        if t.get("description") != r.get("description"):
            diffs.append(f"{t['name']}: jiný description")
        if t.get("input_schema") != r.get("input_schema"):
            diffs.append(f"{t['name']}: jiné input_schema")
    return (len(diffs) == 0), diffs
