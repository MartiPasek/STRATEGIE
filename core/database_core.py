from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings


engine_core = create_engine(
    settings.database_core_url,
    pool_pre_ping=True,
    echo=False,
)

SessionCore = sessionmaker(bind=engine_core, autocommit=False, autoflush=False)


class BaseCore(DeclarativeBase):
    """Deklarativní základ pro modely v css_db."""
    pass


def get_core_session():
    return SessionCore()
