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
    """Deklarativní základ pro všechny SQLAlchemy modely."""
    pass


def get_db_session():
    """Vytvoří a vrátí DB session. Volající ji musí zavřít."""
    return SessionLocal()