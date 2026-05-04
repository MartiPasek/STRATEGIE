r"""
Email fetcher -- out-of-process polling worker pro EWS -> email_inbox.

Polluje persona_channels (channel_type='email', is_enabled=True) v pravidelnem
intervalu, za kazdou personu fetchne unread z INBOX a ulozi do email_inbox.

Beh:
    python -m poetry run python scripts/email_fetcher.py
    python -m poetry run python scripts/email_fetcher.py --poll 30

Nebo pouzij .ps1 wrapper (pokud existuje), nebo stejny pattern jako task_worker:
    .\scripts\email_fetcher.ps1

Graceful shutdown: Ctrl+C / SIGTERM. Worker dokonci aktualni poll cycle a skonci.

Proc out-of-process:
  - Restart uvicornu neshodi bezici fetch. Mame nezavisly proces.
  - Production: bude to bezet jako systemd / Task Scheduler service vedle task_workera.

Jak handlujeme chyby:
  - ews_fetcher.fetch_all_active_personas() sam logguje per-persona chyby a
    pokracuje dal. Tzn. jedna persona s nefunkcnim emailem nezabije poll cycle.
  - Pokud sam fetch_all_active_personas() vyhodi (napr. DB connection down),
    worker zalog, pocka poll interval, zkusi znovu. Po 10 consecutive chybach
    exit (aby se v systemd restart smyckovani nepropalilo).

Interval:
  Default 60s. To je kompromis mezi latenci (nejhorsi pripad = 60s od prijeti
  emailu do zapsani do DB) a zatezi Exchange serveru. User ma v UI "Fetch now"
  tlacitko, kdyz chce okamzite zkontrolovat -- neni potreba kratky polling.
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# sys.path setup -- stejny pattern jako task_worker.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.logging import setup_logging, get_logger   # noqa: E402

setup_logging()
logger = get_logger("email_fetcher")


# ── Graceful shutdown state ────────────────────────────────────────────────

_shutdown_requested = False


def _handle_sigint(signum, frame):
    """Nastavi flag, hlavni smycka ho zkontroluje mezi polly."""
    global _shutdown_requested
    if _shutdown_requested:
        logger.warning("EMAIL FETCHER | second Ctrl+C -- hard exit")
        sys.exit(130)
    logger.info("EMAIL FETCHER | SIGINT -- graceful shutdown po aktualnim pollu")
    _shutdown_requested = True


# ── Hlavni smycka ──────────────────────────────────────────────────────────

def run_worker(poll_interval: float = 60.0) -> int:
    """
    Hlavni worker loop. Vraci exit code:
      0  -- cisty shutdown
      1  -- fatal error (prilis mnoho consecutive chyb)
    """
    # Importy uvnitr funkce, aby se nepadlo jeste pred setup_logging().
    from modules.notifications.application import ews_fetcher, email_service

    logger.info(f"EMAIL FETCHER | start | poll={poll_interval}s")

    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 10

    while not _shutdown_requested:
        try:
            # 1) Inbound -- stahne unread z Exchange do email_inbox.
            # Phase 29-D (4.5.2026): clean cut na mailbox-based variant.
            # Pollne mailboxes (active=True) misto persona_channels.
            # Shared mailbox = single EWS connection, multiple authorized
            # personas vidi inbox skrz mailbox_id FK + AI tools filter.
            result_in = ews_fetcher.fetch_all_active_mailboxes()
            logger.info(
                f"EMAIL FETCHER | inbound | mailboxes={result_in['mailboxes']} | "
                f"new={result_in['total_new']} | deduped={result_in['total_deduped']} | "
                f"errors={result_in['total_errors']}"
            )
            # 2) Outbound -- odesle pending radky z email_outbox pres EWS
            result_out = email_service.flush_outbox_pending(batch_size=10)
            if result_out["claimed"] > 0:
                logger.info(
                    f"EMAIL FETCHER | outbound | claimed={result_out['claimed']} | "
                    f"sent={result_out['sent']} | failed={result_out['failed']} | "
                    f"retry={result_out['retry']}"
                )
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            logger.error(
                f"EMAIL FETCHER | cycle failed ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}) "
                f"| error={e!r}",
                exc_info=True,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.critical(
                    "EMAIL FETCHER | too many consecutive errors -- exiting"
                )
                return 1

        # Sleep s pravidelnym checkem shutdown flagu, at SIGINT nezacne cekat
        # cely poll interval. 1s granularity postaci.
        slept = 0.0
        while slept < poll_interval and not _shutdown_requested:
            time.sleep(1.0)
            slept += 1.0

    logger.info("EMAIL FETCHER | shutdown complete")
    return 0


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Email fetcher pro STRATEGIE (EWS -> email_inbox)."
    )
    parser.add_argument(
        "--poll", "--poll-interval", type=float, default=60.0, dest="poll_interval",
        help="Jak casto pollovat Exchange (sekundy). Default 60.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="DEBUG loglevel (default INFO).",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT, _handle_sigint)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sigint)

    return run_worker(poll_interval=args.poll_interval)


if __name__ == "__main__":
    sys.exit(main())
