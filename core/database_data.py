from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings


engine_data = create_engine(
    settings.database_data_url,
    pool_pre_ping=True,
    echo=False,
)

SessionData = sessionmaker(bind=engine_data, autocommit=False, autoflush=False)


class BaseData(DeclarativeBase):
    """Deklarativní základ pro modely v data_db."""
    pass


def get_data_session():
    return SessionData()
