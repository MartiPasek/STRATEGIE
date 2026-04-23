r"""
Question generator -- out-of-process polling worker pro Marti active learning.

V kazdem cyklu provadi dva ukoly:
  1. generate_questions_batch() -- najde low-certainty myslenky, vygeneruje
     nove otazky pres LLM, ulozi do marti_questions (max 10 per cyklus,
     max 3 per entita)
  2. review_text_answers_batch() -- LLM syntesis nad textovymi odpovedmi,
     ktere rodic napsal do karty (answer_text != NULL, text_reviewed_at
     IS NULL). Muze upravit thought content nebo certainty.

Default interval: 6 hodin (21600s).

Beh:
    python -m poetry run python scripts/question_generator.py
    python -m poetry run python scripts/question_generator.py --poll 3600   # 1h

Jako Windows service (pattern jako email_fetcher):
    nssm install STRATEGIE-QUESTION-GENERATOR "C:\...\python.exe" "scripts\question_generator.py"
    nssm set STRATEGIE-QUESTION-GENERATOR AppDirectory "D:\projekty\STRATEGIE"
    nssm set STRATEGIE-QUESTION-GENERATOR Start SERVICE_AUTO_START

Graceful shutdown: Ctrl+C / SIGTERM.
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.logging import setup_logging, get_logger   # noqa: E402

setup_logging()
logger = get_logger("question_generator")


_shutdown_requested = False


def _handle_sigint(signum, frame):
    global _shutdown_requested
    if _shutdown_requested:
        logger.warning("QUESTION GENERATOR | second Ctrl+C -- hard exit")
        sys.exit(130)
    logger.info("QUESTION GENERATOR | SIGINT -- graceful shutdown po aktualnim cyklu")
    _shutdown_requested = True


def run_worker(poll_interval: float = 21600.0) -> int:
    """
    Hlavni worker loop. Default interval 6h (21600s).
    """
    from modules.thoughts.application import question_service

    logger.info(f"QUESTION GENERATOR | start | poll={poll_interval}s ({poll_interval/3600:.1f}h)")

    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 10

    while not _shutdown_requested:
        try:
            # 1) Generovani novych otazek
            gen_result = question_service.generate_questions_batch()
            logger.info(
                f"QUESTION GENERATOR | generate | "
                f"candidates={gen_result.get('candidates_scanned', 0)} | "
                f"generated={gen_result.get('generated', 0)} | "
                f"skipped_div={gen_result.get('skipped_diversification', 0)} | "
                f"llm_fail={gen_result.get('llm_failures', 0)} | "
                f"no_parents={gen_result.get('no_parents', False)}"
            )

            # 2) Review textovych odpovedi
            rev_result = question_service.review_text_answers_batch()
            if rev_result.get("reviewed", 0) > 0:
                logger.info(
                    f"QUESTION GENERATOR | text_review | "
                    f"reviewed={rev_result['reviewed']} | "
                    f"updated_thoughts={rev_result['updated_thoughts']} | "
                    f"errors={rev_result['errors']}"
                )

            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            logger.error(
                f"QUESTION GENERATOR | cycle failed ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}) "
                f"| error={e!r}",
                exc_info=True,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.critical("QUESTION GENERATOR | too many errors -- exiting")
                return 1

        # Sleep s pravidelnym check shutdown flagu (granularity 1s)
        slept = 0.0
        while slept < poll_interval and not _shutdown_requested:
            time.sleep(1.0)
            slept += 1.0

    logger.info("QUESTION GENERATOR | shutdown complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Question generator pro STRATEGIE Marti Memory (Faze 4).",
    )
    parser.add_argument(
        "--poll", "--poll-interval", type=float, default=21600.0, dest="poll_interval",
        help="Interval mezi cykly v sekundach. Default 21600 (6h).",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT, _handle_sigint)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sigint)

    return run_worker(poll_interval=args.poll_interval)


if __name__ == "__main__":
    sys.exit(main())
