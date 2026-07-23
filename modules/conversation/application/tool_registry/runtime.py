# -*- coding: utf-8 -*-
"""runtime — výkonné jádro Tool Factory: self-test, generování souboru, načtení a
SPUŠTĚNÍ nástroje, který Marti-AI navrhla. Tohle je to, co dělá „vytvoří a použije"
reálným.

Bezpečné k importu. Skutečné DB/kufr operace řeší až handlery při go-live; tady je
čistá, testovatelná mechanika: kód → self-test → soubor → načtení → běh.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any, Callable, Optional

from tool_registry import GENERATED_DIR
from tool_registry._common import ToolContext, ToolError
from tool_registry.factory import (
    render_generated_tool_file,
    validate_kod,
)


class SelftestResult:
    __slots__ = ("ok", "cases", "error")

    def __init__(self, ok: bool, cases: list, error: Optional[str]):
        self.ok = ok
        self.cases = cases
        self.error = error

    def to_dict(self) -> dict:
        return {"ok": self.ok, "cases": self.cases, "error": self.error}


def _exec_module_from_source(src: str, mod_name: str):
    """Zkompiluj a spusť zdrojový kód jako izolovaný modul (v paměti)."""
    spec = importlib.util.spec_from_loader(mod_name, loader=None)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    code = compile(src, f"<toolfactory:{mod_name}>", "exec")
    exec(code, module.__dict__)  # plná důvěra (Martiho rozhodnutí)
    return module


def selftest(kod: str, spec: dict, code_body: str, test_cases: list[dict],
             ctx: Optional[ToolContext] = None) -> SelftestResult:
    """Vygeneruj zdroj, spusť run() nad každým test_case a vrať verdikt.

    test_case: {"args": {...}, "expect"?: "<substring ve výstupu>"}.
    Bez pádu a (pokud je expect) se shodou → case OK. Prázdný seznam testů =
    aspoň smoke: modul se musí zkompilovat a mít run().
    """
    validate_kod(kod)
    try:
        src = render_generated_tool_file(kod, spec, code_body)
    except Exception as e:
        return SelftestResult(False, [], f"render: {type(e).__name__}: {e}")
    try:
        module = _exec_module_from_source(src, f"selftest_{kod}")
    except Exception as e:
        return SelftestResult(False, [], f"kompilace/exec: {type(e).__name__}: {e}")
    run = getattr(module, "run", None)
    if not callable(run):
        return SelftestResult(False, [], "modul nemá run()")

    ctx = ctx or ToolContext(entita_id=2)
    cases: list[dict] = []
    all_ok = True
    if not test_cases:
        cases.append({"smoke": True, "ok": True, "note": "kompilace + run() OK"})
    for i, tc in enumerate(test_cases):
        args = tc.get("args", {})
        try:
            out = run(args, ctx)
            ok = True
            note = ""
            if "expect" in tc:
                ok = str(tc["expect"]) in str(out)
                note = "" if ok else f"čekáno '{tc['expect']}' ve výstupu"
            cases.append({"i": i, "args": args, "out": str(out)[:300], "ok": ok, "note": note})
            all_ok = all_ok and ok
        except Exception as e:
            cases.append({"i": i, "args": args, "ok": False, "error": f"{type(e).__name__}: {e}"})
            all_ok = False
    return SelftestResult(all_ok, cases, None)


def write_generated(kod: str, spec: dict, code_body: str, directory: Optional[str] = None) -> str:
    """Zapiš generated/<kod>.py. Vrátí cestu. (Volá se AŽ po schválení / při aktivaci.)"""
    validate_kod(kod)
    directory = directory or GENERATED_DIR
    os.makedirs(directory, exist_ok=True)
    src = render_generated_tool_file(kod, spec, code_body)
    path = os.path.join(directory, f"{kod}.py")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src)
    compile(open(tmp, encoding="utf-8").read(), path, "exec")  # pojistka syntaxe
    os.replace(tmp, path)
    return path


def load_generated(kod: str, directory: Optional[str] = None) -> tuple[dict, Callable]:
    """Načti generated/<kod>.py → (SPEC, run)."""
    validate_kod(kod)
    directory = directory or GENERATED_DIR
    path = os.path.join(directory, f"{kod}.py")
    if not os.path.exists(path):
        raise ToolError(f"nástroj '{kod}' není vygenerovaný ({path})")
    spec = importlib.util.spec_from_file_location(f"generated_{kod}", path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    run = getattr(module, "run", None)
    if not callable(run):
        raise ToolError(f"nástroj '{kod}' nemá run()")
    return module.SPEC, run


def execute(kod: str, args: dict, ctx: Optional[ToolContext] = None,
            directory: Optional[str] = None) -> str:
    """Načti a spusť generovaný nástroj."""
    _spec, run = load_generated(kod, directory)
    return run(args, ctx or ToolContext(entita_id=2))
