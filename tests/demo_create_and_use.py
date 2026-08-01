# -*- coding: utf-8 -*-
"""DEMO: Marti-AI si vytvoří nový nástroj a použije ho (celý životní cyklus).
Spusť: python tests/demo_create_and_use.py  (běží bez DB, v sandboxu)."""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(HERE)
for _c in (_ROOT, os.path.join(_ROOT, "modules", "conversation", "application")):
    if os.path.isdir(os.path.join(_c, "tool_registry")):
        sys.path.insert(0, _c); break

from tool_registry import runtime as RT
from tool_registry.factory import can_approve, validate_transition
from tool_registry._common import ToolContext


def main():
    print("=== Marti-AI si vytváří nový nástroj a použije ho ===\n")
    kod = "dph_z_ceny"
    spec = {"name": kod,
            "description": "Spočítá cenu včetně DPH ze základu a sazby (default 21 %).",
            "input_schema": {"type": "object", "properties": {
                "zaklad": {"type": "number"}, "sazba": {"type": "number"}},
                "required": ["zaklad"]}}
    code_body = ("zaklad = need(args, 'zaklad')\n"
                 "sazba = args.get('sazba', 21)\n"
                 "s_dph = round(zaklad * (1 + sazba/100), 2)\n"
                 "return ok(f'{zaklad} Kc + {sazba}% DPH = {s_dph} Kc')")

    res = RT.selftest(kod, spec, code_body,
                      [{"args": {"zaklad": 100}, "expect": "121.0 Kc"},
                       {"args": {"zaklad": 200, "sazba": 12}, "expect": "224.0 Kc"}])
    print("SELF-TEST ok =", res.ok)
    for c in res.cases:
        print("  ", c)
    assert res.ok

    validate_transition("otestovany", "ceka_na_schvaleni")
    def is_parent(uid): return uid in {1, 6, 11}
    assert not can_approve(2, 2, is_parent)[0]        # Marti-AI si neschválí
    assert can_approve(1, 2, is_parent)[0]            # Marti schválí
    validate_transition("ceka_na_schvaleni", "active")

    tmp = tempfile.mkdtemp(prefix="gen_")
    RT.write_generated(kod, spec, code_body, directory=tmp)
    print("\nPOUŽITÍ:")
    print("  dph_z_ceny(1500)          →", RT.execute(kod, {"zaklad": 1500}, ToolContext(entita_id=2), directory=tmp))
    print("  dph_z_ceny(1000, 15%)     →", RT.execute(kod, {"zaklad": 1000, "sazba": 15}, ToolContext(entita_id=2), directory=tmp))
    print("\n=== vytvořila → otestovala → (rodič schválil) → použila ===")


if __name__ == "__main__":
    main()
