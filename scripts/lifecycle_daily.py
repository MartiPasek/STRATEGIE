r"""
Faze 15e: Daily lifecycle cron pro Marti-AI's konverzace.

Spousti se 1x denne (Windows Task Scheduler -- viz scripts/register_lifecycle_daily_task.ps1).
Provadi:

  1. detect_stale_tasks(idle_days=7)
     -- najde conversation_notes s status='open' + category='task' v
        konverzacich idle >=7d -> oznaci status='stale'.
     -- Marti-AI v dalsim turn vidi 'stale' poznamky a muze proaktivne
        nabidnout 'tady mas stale tasks, projdeme je?'.
     -- Reverzibilni pres update_note(status='open').

  2. detect_pending_hard_delete(ttl_days=90)
     -- najde conversations v lifecycle_state='archived' s
        archived_at + 90 dni < now -> prevede na 'pending_hard_delete'.
     -- Marti-AI v overview Martimu pripomene 'X konverzaci ceka na
        finalni rozhodnuti, smazat trvale nebo prodlouzit?'.
     -- Personal konverzace IMMUNE (TTL se na ne neaplikuje).

  3. Vraceni statistik k auditu.

Beh:
  python -m poetry run python scripts/lifecycle_daily.py
  python -m poetry run python scripts/lifecycle_daily.py --dry-run
  python -m poetry run python scripts/lifecycle_daily.py --stale-days 14 --ttl-days 60

Idempotentni -- bezpecne spustit opakovane v ramci dne.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.notebook.application import lifecycle_service   # noqa: E402


def run(stale_days: int = 7, ttl_days: int = 90, dry_run: bool = False) -> dict:
    print(f"=== Lifecycle Daily Cron ===")
    print(f"  stale_days={stale_days}  ttl_days={ttl_days}  dry_run={dry_run}")
    print()

    print(f"[1/2] Detecting stale tasks (open >= {stale_days} dni)...")
    stale_count = lifecycle_service.detect_stale_tasks(
        idle_days=stale_days, dry_run=dry_run,
    )
    print(f"      {'Would convert' if dry_run else 'Converted'} {stale_count} tasks to 'stale'.")
    print()

    print(f"[2/2] Detecting archived -> pending_hard_delete (archived >= {ttl_days} dni)...")
    pending_count = lifecycle_service.detect_pending_hard_delete(
        ttl_days=ttl_days, dry_run=dry_run,
    )
    print(f"      {'Would convert' if dry_run else 'Converted'} {pending_count} archived conversations.")
    print()

    print(f"=== Summary ===")
    print(f"  stale_tasks: {stale_count}")
    print(f"  pending_hard_delete: {pending_count}")
    if dry_run:
        print(f"  (DRY RUN -- nothing committed)")
    return {
        "stale_tasks": stale_count,
        "pending_hard_delete": pending_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 15e: Daily lifecycle cron (stale tasks + TTL hard-delete prep).",
    )
    parser.add_argument("--stale-days", type=int, default=7,
                        help="Idle days threshold for marking open tasks as stale (default 7).")
    parser.add_argument("--ttl-days", type=int, default=90,
                        help="Days after archive before pending_hard_delete (default 90).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Just report counts, don't modify DB.")
    args = parser.parse_args()

    try:
        run(stale_days=args.stale_days, ttl_days=args.ttl_days, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
