"""
Sjednoceny database access -- Phase 18 (29.4.2026 rano).

Po DB merge (css_db + data_db -> data_db) je jediny SQLAlchemy engine
+ jediny Base + jediny session getter. Drive byly dva (BaseCore/BaseData,
get_core_session/get_data_session) -- viz git history pre-Phase 18.

Backward compat: core/database_core.py + core/database_data.py jsou
zachovány jako thin alias shim (re-export z core/database). To umozni
modules/ kódu fungovat bez okamzite refactor. scripts/ jsou updatnute
explicitne na get_session (Marti's volba A pro scripty).

Phase 18.1 (po stable provoze): grep replace v modules/ aby zmizely
poslední odkazy na BaseCore/BaseData/get_core_session/get_data_session.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings


# Single engine -- po Phase 18 merge je vsechno v data_db.
# Pouzivame `database_data_url` jako primary connection string;
# `database_core_url` je deprecated (ukazuje na drop-pending css_db).
engine = create_engine(
    settings.database_data_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Deklarativni zaklad pro vsechny modely (po Phase 18 merge)."""
    pass


def get_session():
    """
    Jediny session getter pro celou aplikaci.

    Po Phase 18 nahrazuje get_core_session() i get_data_session() -- vsechny
    tabulky jsou v jedne DB.

    Vraci novou Session instanci. Volajici je odpovedny za commit/rollback
    a close (typicky pres try/finally pattern -- viz workflow gotcha #8).
    """
    return SessionLocal()
