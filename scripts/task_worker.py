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

def _reap_unprocessed_sms(lookback_hours: int = 24) -> None:
    """
    Faze 12b+: Recovery -- najde sms_inbox kde processed_at IS NULL a chybi
    pro ni task, vytvori chybejici. Plus reset failed tasku s attempts<3.

    Lazy import sms_service / models -- aby task worker neselhal hned na
    startu kdyby modul mel chybu.
    """
    from datetime import datetime, timezone, timedelta
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_data import SmsInbox, Task
    from modules.notifications.application.sms_service import (
        _maybe_create_task_from_inbound_sms,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    ds = get_data_session()
    try:
        rows = (
            ds.query(SmsInbox)
            .filter(
                SmsInbox.processed_at.is_(None),
                SmsInbox.received_at >= cutoff,
            )
            .all()
        )
        if not rows:
            return

        created = 0
        retried = 0
        for sms in rows:
            existing = (
                ds.query(Task)
                .filter(
                    Task.source_type == "sms_inbox",
                    Task.source_id == sms.id,
                )
                .first()
            )
            if existing is None:
                tid = _maybe_create_task_from_inbound_sms(
                    sms_id=sms.id,
                    from_phone=sms.from_phone,
                    body=sms.body,
                    persona_id=sms.persona_id,
                    tenant_id=sms.tenant_id,
                )
                if tid:
                    created += 1
            elif existing.status == "failed" and (existing.attempts or 0) < 3:
                existing.status = "pending"
                existing.error = None
                existing.started_at = None
                ds.commit()
                retried += 1

        if created or retried:
            logger.info(
                f"REAPER | sms | created={created} | retried={retried} | "
                f"scanned={len(rows)} | lookback={lookback_hours}h"
            )
    finally:
        ds.close()


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

    # Faze 12b+: SMS recovery reaper -- periodicky scan unprocessed SMS,
    # vytvor chybejici tasky / reset failed s attempts<3 na pending.
    # Pricina: gateway vypadek nebo deploy bug muze nechat SMS bez tasku.
    # Marti princip: 'SMS worker musi bezet nezavisle na gateway, snazit
    # se nevyresene SMSky odbavit.'
    REAP_EVERY_N_POLLS = 12   # ~60s pri default poll=5s
    REAP_LOOKBACK_HOURS = 24
    _reap_counter = REAP_EVERY_N_POLLS  # priste reapovat hned pri startu

    while not _shutdown_requested:
        # Recovery reap (periodic)
        _reap_counter += 1
        if _reap_counter >= REAP_EVERY_N_POLLS:
            _reap_counter = 0
            try:
                _reap_unprocessed_sms(REAP_LOOKBACK_HOURS)
            except Exception as _re:
                logger.warning(f"REAPER | sms scan failed | {_re!r}")

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
