"""
LEGACY — testovací databáze 'strategie' (Phase 18 archive).

Před Phase 18 (29.4.2026) byl tento modul v `core/database.py` a sloužil
pro testovací DB `strategie` (mimo css_db / data_db). Po Phase 18 merge
je primary `core/database.py` reservovaný pro sjednocený access do
mergované data_db.

Tento soubor je zachován jen pro nostalgii / případnou regression
diagnostiku původních testů. Žádný produkční kód ho nepoužívá.

Pokud by někdo potřeboval testovací 'strategie' DB, importuje odsud
explicitně:
    from core.database_legacy import Base, get_db_session, engine
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """LEGACY — Base pro testovací DB. Nepoužívat v nových modulech."""
    pass


def get_db_session():
    """LEGACY — session pro testovací DB."""
    return SessionLocal()
