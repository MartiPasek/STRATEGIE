"""
Phase 18 backward-compat shim (29.4.2026 rano).

Drive mel vlastni engine pro data_db. Po DB merge je to alias na
sjednocene core.database. Modules/ kod muze pokracovat s BaseData /
get_data_session bez refactor.
"""
from core.database import (
    Base as BaseData,
    SessionLocal as SessionData,
    engine as engine_data,
    get_session as get_data_session,
)

__all__ = ["BaseData", "SessionData", "engine_data", "get_data_session"]
