r"""
Task worker -- out-of-process runner pro AI task queue.

Polluje data_db.tasks (WHERE status='open') v pravidelnem intervalu, kazdy
otevreny task spousti pres modules.tasks.application.executor.execute_task().

Beh:
    python -m poetry run python scripts/task_worker.py
    python -m poetry run python scripts/task_worker.py --poll 3 --batch 5

Nebo pouzij .ps1 wrapper:
    .\scripts\task_worker.ps1

Graceful shutdown: Ctrl+C (SIGINT). Worker dokonci aktualni task a pak skonci.

Proc out-of-process:
  - Restart uvicornu (napr. po code change) neshodi bezici task. Kazdy task
    si executor atomicky naclaimuje a provadi samostatne.
  - Produkce: pusti se vedle uvicornu jako samostatna systemd/Task Scheduler
    sluzba.

Jak handlujeme chyby:
  - Vyjimka uvnitr execute_task() se zapise do task.error, task.status='failed'
    -- exekutor sam. Worker jen zalog, pokracuje na dalsi task.
  - Vyjimka mimo execute_task() (napr. DB connection error pri polling) --
    worker zalog, pocka poll interval, zkusi znovu. Po 10 consecutive chybach
    se ukonci (aby se v systemd restart smyckovani nepropalilo).
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# sys.path setup -- stejny pattern jako _diag_conversations.py / backfill_*.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.logging import setup_logging, get_logger   # noqa: E402

setup_logging()
logger = get_logger("task_worker")


# ── Graceful shutdown state ────────────────────────────────────────────────

_shutdown_requested = False


def _handle_sigint(signum, frame):
    """Nastavi flag, hlavni smyčka ho zkontroluje mezi task batchy."""
    global _shutdown_requested
    if _shutdown_requested:
        # Druhy Ctrl+C -- tvrdy exit (user chce skoncit hned)
        logger.warning("TASK WORKER | second Ctrl+C -- hard exit")
        sys.exit(130)
    logger.info("TASK WORKER | SIGINT -- graceful shutdown po aktualnim batchi")
    _shutdown_requested = True


# ── Hlavni smyčka ──────────────────────────────────────────────────────────

def run_worker(poll_interval: float = 5.0, batch_size: int = 3) -> int:
    """
    Hlavni worker loop. Vraci exit code:
      0  -- cisty shutdown (Ctrl+C)
      1  -- fatal error (prilis mnoho consecutive chyb)
    """
    # Importy uvnitr funkce, aby se worker nepaddal jeste pred setup_logging().
    from modules.tasks.application import executor

    logger.info(
        f"TASK WORKER | start | poll={poll_interval}s | batch={batch_size}"
    )

    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 10

    while not _shutdown_requested:
        try:
            task_ids = executor.fetch_open_task_ids(limit=batch_size)
        except Exception as e:
            consecutive_errors += 1
            logger.error(
                f"TASK WORKER | fetch failed ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}) "
                f"| error={e!r}",
                exc_info=True,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.critical(
                    "TASK WORKER | too many consecutive errors -- exiting"
                )
                return 1
            time.sleep(poll_interval)
            continue

        # Reset counter -- uspesne DB spojeni
        consecutive_errors = 0

        if not task_ids:
            # Zadne open tasky -- cekame do dalsiho pollu
            time.sleep(poll_interval)
            continue

        logger.info(f"TASK WORKER | batch | {len(task_ids)} tasks | ids={task_ids}")
        for tid in task_ids:
            if _shutdown_requested:
                # User chtel graceful -- task nesebereme, zustane v 'open' a
                # dalsi startup workera ho popadne.
                logger.info(f"TASK WORKER | skip | task_id={tid} | shutdown requested")
                break

            try:
                result = executor.execute_task(tid)
                logger.info(
                    f"TASK WORKER | processed | task_id={tid} | "
                    f"status={result.get('status')}"
                )
            except Exception as e:
                # Neocekavana chyba (executor by ji mel chytit sam, ale
                # defensive safety net -- ochrana pred zabijou workera).
                logger.error(
                    f"TASK WORKER | executor raised | task_id={tid} | error={e!r}",
                    exc_info=True,
                )

        # Hned po batchi polluj znovu -- nebuder zbytecne spat, pokud jsou
        # dalsi tasky ve fronte.

    logger.info("TASK WORKER | shutdown complete")
    return 0


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Task worker pro STRATEGIE AI task queue."
    )
    parser.add_argument(
        "--poll", "--poll-interval", type=float, default=5.0, dest="poll_interval",
        help="Jak casto pollovat DB kdyz je fronta prazdna (sekundy). Default 5.",
    )
    parser.add_argument(
        "--batch", "--batch-size", type=int, default=3, dest="batch_size",
        help="Max kolik tasku pobrat v jednom pollu. Default 3.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="DEBUG loglevel (default INFO).",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT, _handle_sigint)
    # SIGTERM (systemd stop) -- stejny handler
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sigint)

    return run_worker(
        poll_interval=args.poll_interval,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    sys.exit(main())
