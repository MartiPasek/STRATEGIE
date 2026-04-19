"""
Reset script — DROP + CREATE obou databází (css_db i data_db).

Pro identity refactor v2. Používá connection stringy z .env, takže nemusíš mít
v PATH `psql`.

Spustit:
    python -m poetry run python scripts/reset_db.py

DESTRUKTIVNÍ — všechna data v obou DB budou ztracena.
"""
import sys
import os
from urllib.parse import urlparse

# Allow running as `python scripts/reset_db.py` from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from core.config import settings


def _admin_url(target_url: str) -> str:
    """
    Z target_url (např. postgresql://user:pass@host:port/css_db)
    vyrobí admin URL s database 'postgres' (administrativní DB).
    """
    parsed = urlparse(target_url)
    return f"{parsed.scheme}://{parsed.netloc}/postgres"


def _db_name(target_url: str) -> str:
    return urlparse(target_url).path.lstrip("/")


def reset_database(target_url: str) -> None:
    db_name = _db_name(target_url)
    admin_url = _admin_url(target_url)

    print(f"  → admin connect: {admin_url}")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        # Pre-shutdown všech aktivních spojení k cílové DB
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
        """))
        print(f"  → terminated active connections to '{db_name}'")

        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        print(f"  ✓ dropped '{db_name}'")

        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        print(f"  ✓ created '{db_name}'")

    engine.dispose()


def main() -> None:
    if not settings.database_core_url or not settings.database_data_url:
        print("✗ Chybí database_core_url nebo database_data_url v .env")
        sys.exit(1)

    print("══════════════════════════════════════════════════════════")
    print("  DB RESET — DROP + CREATE")
    print("══════════════════════════════════════════════════════════")

    print("\n[1/2] css_db (DB_Core)")
    reset_database(settings.database_core_url)

    print("\n[2/2] data_db (DB_Data)")
    reset_database(settings.database_data_url)

    print("\n✓ Obě DB jsou prázdné a připravené pro alembic upgrade head.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Reset selhal: {type(e).__name__}: {e}")
        sys.exit(1)
