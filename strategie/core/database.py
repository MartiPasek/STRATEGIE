from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # ověří spojení před každým použitím
    echo=False,           # True = loguje SQL dotazy (užitečné při debugování)
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Deklarativní základ pro všechny SQLAlchemy modely."""
    pass


def get_db_session():
    """
    Vytvoří a vrátí DB session.
    Volající je zodpovědný za její uzavření.
    Použití: session = get_db_session(); try: ... finally: session.close()
    """
    return SessionLocal()
