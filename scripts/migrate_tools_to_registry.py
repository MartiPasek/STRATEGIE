#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migrace tools.py → tool_registry/defs/ (ready-to-run NA BOXU, kde jsou app deps).

Přečte živý seznam TOOLS z modules.conversation.application.tools, každý nástroj
zapíše jako tool_registry/defs/<name>.py (SPEC = {...} + _order = původní index),
pak načte registr zpět a BYTE-OVĚŘÍ, že složený seznam speců je identický s
originálem (stejný přístup jako g2007 compare-full). Handlery zůstávají prozatím
v _handle_tool — tahle migrace přesouvá jen SPECY (bezpečné, chování beze změny).

POZOR: pusť až po rozhodnutí o go-live. Defaultně běží v --dry-run (nic nezapíše,
jen ověří, kolik nástrojů a jestli by round-trip seděl). Ostrý zápis: --write.

Použití (na boxu, v poetry env):
    python -m poetry run python scripts/migrate_tools_to_registry.py            # dry-run
    python -m poetry run python scripts/migrate_tools_to_registry.py --write    # zapíše defs/
"""
from __future__ import annotations

import argparse
import os
import pprint
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFS_DIR = os.path.join(ROOT, "modules", "conversation", "application", "tool_registry", "defs")

HEADER = (
    "# -*- coding: utf-8 -*-\n"
    '"""Migrovaný nástroj `{name}` (z tools.py). SPEC je zdroj pravdy pro API;\n'
    "handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —\n"
    "cílově je zdrojem g2007.nastroj, tohle je souborová projekce.\n"
    '"""\n\n'
)


def _spec_literal(spec: dict, order: int) -> str:
    d = dict(spec)
    d["_order"] = order
    # pprint → validní Python literál (True/False/None), stabilní pořadí klíčů.
    return "SPEC = " + pprint.pformat(d, width=100, sort_dicts=False, indent=4) + "\n"


def _load_tools_via_import():
    from modules.conversation.application.tools import TOOLS
    return list(TOOLS), "import"


def _load_tools_via_ast():
    """Fallback bez app-deps: přečti TOOLS staticky ze souboru (vše jsou literály).
    Umožňuje běh i mimo poetry venv (např. z Linux VM s namountovaným repem)."""
    import ast
    path = os.path.join(ROOT, "modules", "conversation", "application", "tools.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TOOLS" for t in node.targets
        ):
            if not isinstance(node.value, ast.List):
                raise TypeError("TOOLS není list literal")
            return [ast.literal_eval(e) for e in node.value.elts], "ast"
    raise LookupError("TOOLS v tools.py nenalezen")


def load_tools():
    try:
        return _load_tools_via_import()
    except Exception as e:
        print(f"(import TOOLS selhal: {type(e).__name__}: {e} — zkouším AST)")
        return _load_tools_via_ast()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="Opravdu zapiš defs/ (jinak dry-run).")
    args = ap.parse_args()

    TOOLS, how = load_tools()
    print(f"Nástrojů v TOOLS: {len(TOOLS)} (načteno přes {how})")
    names = [t["name"] for t in TOOLS]
    if len(names) != len(set(names)):
        dup = sorted({n for n in names if names.count(n) > 1})
        print(f"!! DUPLIKÁTNÍ jména v TOOLS: {dup}  — ABORT")
        return 2

    if args.write:
        os.makedirs(DEFS_DIR, exist_ok=True)
        for i, spec in enumerate(TOOLS):
            path = os.path.join(DEFS_DIR, f"{spec['name']}.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(HEADER.format(name=spec["name"]))
                f.write(_spec_literal(spec, i))
        print(f"Zapsáno {len(TOOLS)} souborů do {DEFS_DIR}")

    # ── Ověření round-tripu (funguje po --write; při dry-run nad tím, co je) ──────
    import importlib
    _pkg_parent = os.path.join(ROOT, "modules", "conversation", "application")
    if os.path.isdir(os.path.join(_pkg_parent, "tool_registry")) and _pkg_parent not in sys.path:
        sys.path.insert(0, _pkg_parent)
    import tool_registry as reg  # noqa: E402
    importlib.reload(reg)
    mods = reg.load_all()
    assembled = reg.assemble_specs(mods)
    # porovnej jen migrované (podle jmen z TOOLS)
    tools_by_name = {t["name"]: t for t in TOOLS}
    subset = [s for s in assembled if s["name"] in tools_by_name]
    ok, diffs = reg.verify_identical(subset, list(TOOLS))
    if ok:
        print(f"BYTE-OK: {len(subset)}/{len(TOOLS)} nástrojů, složený seznam identický.")
        return 0
    print(f"ROZDÍLY ({len(diffs)}):")
    for d in diffs[:40]:
        print("  -", d)
    return 1


if __name__ == "__main__":
    sys.exit(main())
