r"""
Faze 9.1 -- retence llm_calls tabulky.

Smaze radky starsi 30 dni. Idempotentni -- bezpecne spouset opakovane.

Pouzivani:
  python -m poetry run python scripts/llm_calls_retention.py
  python -m poetry run python scripts/llm_calls_retention.py --days 60   # custom window
  python -m poetry run python scripts/llm_calls_retention.py --dry-run    # jen vypis kolik smazat

Doporuceny scheduling (Windows Task Scheduler, denne ve 3:00):
  Program:   C:\Users\Marti\AppData\Local\Programs\Python\Python312\python.exe
  Arguments: -m poetry run python D:\projekty\strategie\scripts\llm_calls_retention.py
  Start in:  D:\projekty\strategie

Logika:
  DELETE FROM llm_calls WHERE created_at < now() - interval 'N days'
  + vypise pocet smazanych + volitelne vacuum analyze.

Bezpecnost:
  - Nikdy nesmaze radky novejsi nez cutoff (even with --force).
  - Soft-log pred delete (count) pro audit.
  - Pri chybe vrati exit code 1 (pro scheduler alerting).
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _cleanup(days: int, dry_run: bool) -> int:
    from sqlalchemy import text
    from core.database import get_session

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    print(f"[llm_calls_retention] cutoff = {cutoff_iso} (starsi radky se smazou)")

    ds = get_session()
    try:
        # Nejdriv count
        count_row = ds.execute(
            text("SELECT count(*) FROM llm_calls WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        ).scalar()
        count = int(count_row or 0)
        print(f"[llm_calls_retention] radku k smazani: {count}")

        if count == 0:
            print("[llm_calls_retention] nic k mazani, exit 0")
            return 0

        if dry_run:
            print("[llm_calls_retention] DRY RUN -- nic nemazu")
            return 0

        # Delete
        res = ds.execute(
            text("DELETE FROM llm_calls WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        ds.commit()

        deleted = getattr(res, "rowcount", count)
        print(f"[llm_calls_retention] OK -- smazano {deleted} radku")
        return 0
    except Exception as e:
        ds.rollback()
        print(f"[llm_calls_retention] !! CHYBA: {e}", file=sys.stderr)
        return 1
    finally:
        ds.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Retence llm_calls tabulky.")
    parser.add_argument(
        "--days", type=int, default=30,
        help="Smazat radky starsi nez N dni (default 30).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Jen vypise pocet radku k smazani, nic nemaze.",
    )
    args = parser.parse_args()

    if args.days < 1:
        print("!! --days musi byt >= 1", file=sys.stderr)
        return 2

    return _cleanup(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
