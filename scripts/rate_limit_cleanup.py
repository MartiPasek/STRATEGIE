"""Phase 38.2 — Cleanup expirovaných verify_rate_buckets.

Spouští se nightly přes Windows Task Scheduler (analog
STRATEGIE-llm-calls-retention z 25.4. večer). Default retention 7d
pro forensic insight.

Usage:
    python -m poetry run python scripts\\rate_limit_cleanup.py
    python -m poetry run python scripts\\rate_limit_cleanup.py --retention-days 14

Registrace v Windows Task Scheduler — viz
scripts\\register_rate_limit_cleanup_task.ps1.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cleanup expirovaných verify_rate_buckets (Phase 38.2)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Kolik dní zachovat expirované buckets (default 7).",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    print(
        f"[{started_at.isoformat()}] rate_limit cleanup START "
        f"retention_days={args.retention_days}"
    )

    try:
        # Lazy import (až po argparse — rychlejší --help)
        from modules.auth.application.rate_limit import cleanup_expired_buckets
        deleted = cleanup_expired_buckets(retention_days=args.retention_days)
    except Exception as e:
        print(f"ERROR: cleanup raised: {e!r}", file=sys.stderr)
        return 1

    finished_at = datetime.now(timezone.utc)
    duration_s = (finished_at - started_at).total_seconds()
    print(
        f"[{finished_at.isoformat()}] rate_limit cleanup DONE "
        f"deleted={deleted} duration={duration_s:.2f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
