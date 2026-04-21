"""
Backfill AI-generovanych nazvu pro existujici konverzace bez title.

Pouziti:
    python scripts/backfill_conversation_titles.py [--dry-run] [--limit N]

Co dela:
- Najde vsechny konverzace v data_db kde title IS NULL.
- Filtruje jen ty s >= 4 textovymi zpravami (jako title_service: dost kontextu).
- Pro kazdou zavola maybe_generate_title -- generuje pres Claude Haiku, ulozi.
- Vypisuje progress (id, novy title, OK/FAIL).
- Na konci summary (kolik OK, kolik skipped, kolik failed).

Cost: ~$0.0001 / konverzace. Pro 50 konverzaci = $0.005, prakticky zdarma.
Trvani: serial, ~0.5-1s na konverzaci. Pro 50 conv = pod minutu.

Bezpecne pustit OPAKOVANE -- maybe_generate_title je idempotentni,
po prvni generaci uz ne-volá API znovu.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# Project root pro sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func

from core.database_data import get_data_session
from modules.core.infrastructure.models_data import Conversation, Message
from modules.conversation.application.title_service import (
    maybe_generate_title, MIN_MESSAGES_FOR_TITLE,
)


def find_eligible_conversations(limit: int | None = None) -> list[int]:
    """
    Vraci seznam conversation_id splnujicich kriteria pro backfill:
    - title IS NULL (zadny rucni rename, zadna predchozi generace)
    - >= MIN_MESSAGES_FOR_TITLE textovych zprav
    Razeni: nejnovejsi prvni (uzivateli budou divat hlavne na recent).
    """
    session = get_data_session()
    try:
        # Subquery: pocet text zprav per konverzace
        msg_counts = (
            session.query(
                Message.conversation_id,
                func.count(Message.id).label("cnt"),
            )
            .filter(Message.message_type == "text")
            .group_by(Message.conversation_id)
            .subquery()
        )
        q = (
            session.query(Conversation.id)
            .outerjoin(msg_counts, msg_counts.c.conversation_id == Conversation.id)
            .filter(
                Conversation.title.is_(None),
                Conversation.is_deleted == False,  # noqa: E712
                msg_counts.c.cnt >= MIN_MESSAGES_FOR_TITLE,
            )
            .order_by(Conversation.id.desc())
        )
        if limit is not None:
            q = q.limit(limit)
        return [row[0] for row in q.all()]
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Jen vypis ktere konverzace by se zpracovaly, neprovadej API call")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max pocet konverzaci k zpracovani (defalut: vsechny)")
    parser.add_argument("--sleep", type=float, default=0.3,
                        help="Pauza mezi konverzacemi (default 0.3s -- ohleduplne k Anthropic API)")
    args = parser.parse_args()

    print("=" * 60)
    print("STRATEGIE -- backfill conversation titles")
    print("=" * 60)
    if args.dry_run:
        print("[DRY RUN] -- nebudu volat API, jen vypsu kandidaty\n")

    ids = find_eligible_conversations(limit=args.limit)
    print(f"Nalezeno {len(ids)} konverzaci bez title (s >= {MIN_MESSAGES_FOR_TITLE} zpravami).\n")
    if not ids:
        print("Nic ke zpracovani. Hotovo.")
        return

    if args.dry_run:
        for cid in ids:
            print(f"  conv #{cid}")
        print(f"\nDry run -- celkem {len(ids)} konverzaci by se zpracovalo.")
        return

    ok = 0
    skipped = 0
    failed = 0
    started_at = time.time()

    for i, cid in enumerate(ids, start=1):
        try:
            title = maybe_generate_title(cid)
            if title:
                # Mohl byt uz ulozen (race), nebo prave vygenerovan
                ok += 1
                print(f"  [{i}/{len(ids)}] conv #{cid:>4} -> {title!r}")
            else:
                skipped += 1
                print(f"  [{i}/{len(ids)}] conv #{cid:>4} -- skipped (no result)")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(ids)}] conv #{cid:>4} -- FAILED: {e}")
        if args.sleep > 0 and i < len(ids):
            time.sleep(args.sleep)

    elapsed = time.time() - started_at
    print()
    print("=" * 60)
    print(f"HOTOVO za {elapsed:.1f}s")
    print(f"  OK:      {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
