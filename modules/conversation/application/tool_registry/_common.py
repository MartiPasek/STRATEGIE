# -*- coding: utf-8 -*-
"""Sdílené helpery pro nástroje v registru (aby se soubory neduplikovaly).

Zatím minimální — sem se při migraci `tools.py` přesunou společné pomůcky
(formátování, přístup k DB session, běžné validace). `ToolContext` je kontrakt
kontextu, který dostane run(args, ctx): plná důvěra jako u ostatních toolů
(Martiho rozhodnutí 22.7.), s timeoutem a eskalací chyby na LLM řeší dispatcher.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolContext:
    """Kontext předaný do run(args, ctx). Plná důvěra (jako ostatní tooly)."""

    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    entita_id: Optional[int] = None          # kdo nástroj volá (entita v g2007)
    persona: Optional[str] = None
    extra: dict = field(default_factory=dict)
    # Volitelné napojení na okolní systém (nastaví dispatcher při zapnutí):
    db_session_factory: Optional[Callable[[], Any]] = None
    call_tool: Optional[Callable[[str, dict], str]] = None  # vnořené volání nástroje


class ToolError(Exception):
    """Řízená chyba nástroje → dispatcher ji přeloží na pri_chybe='eskaluj_llm'."""


def ok(text: str) -> str:
    return text


def need(args: dict, key: str) -> Any:
    """Povinný argument nebo ToolError (čistá hláška pro eskalaci)."""
    if key not in args or args[key] in (None, ""):
        raise ToolError(f"chybí povinný argument '{key}'")
    return args[key]
