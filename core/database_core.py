"""
Phase 18 backward-compat shim (29.4.2026 rano).

Driv mel vlastni engine pro css_db. Po DB merge je to alias na sjednocene
core.database (data_db). Modules/ kod muze pokracovat s BaseCore /
get_core_session bez refactor; Phase 18.1 se postupne sjednoti.

scripts/ byly updatnute explicitne na get_session (Marti's A volba).
"""
from core.database import (
    Base as BaseCore,
    SessionLocal as SessionCore,
    engine as engine_core,
    get_session as get_core_session,
)

__all__ = ["BaseCore", "SessionCore", "engine_core", "get_core_session"]
