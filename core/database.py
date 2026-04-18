"""
LEGACY — testovací databáze 'strategie'.

Tato databáze slouží POUZE pro původní testy.
Pro nový vývoj používej:
  - core/database_core.py  →  css_db
  - core/database_data.py  →  data_db

Tento soubor je zachován kvůli alembic/env.py (testovací migrace).
Nepřidávej sem nové modely ani nové tabulky.
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
