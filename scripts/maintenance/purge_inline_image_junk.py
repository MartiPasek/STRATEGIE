# -*- coding: utf-8 -*-
"""
purge_inline_image_junk.py — jednorazovy uklid: smaz inline e-mailove obrazky
(image001.jpg apod.) tenant 2 z tabulky documents (DB cascade chunky+vektory + fyzicky soubor).

Bezpecnostni filtr: name ~ '^image[0-9]+\\.(jpg|jpeg|png)$'  AND
(extracted_text_length IS NULL OR <= 800).  Overeno 19.8.2026: max extracted_text_length
napric CELYM setem = 228 => zadny realny dokument se nechyta. Vse storage_only obrazky z mailu.

Pouziti (na 188.11, cd C:\\Projekty\\STRATEGIE):
  python scripts\\maintenance\\purge_inline_image_junk.py            # DRY-RUN (nic nemaze)
  python scripts\\maintenance\\purge_inline_image_junk.py --execute  # SMAZE
Detached (70k mazani trva dele nez exec timeout):
  Start-Process -WindowStyle Hidden <python.exe> -ArgumentList "scripts\\maintenance\\purge_inline_image_junk.py --execute"
Resumovatelne: re-run dobere zbytek. C23 19.8.2026, schvalil Marti Pasek.
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import or_
from core.database_data import get_data_session
from modules.core.infrastructure.models_data import Document
from modules.rag.application.service import delete_document

TENANT = 2
PATTERN = r'^[Ii]mage[0-9]+\.(jpg|jpeg|png)$'
TEXT_GUARD = 800
LOG = Path(__file__).resolve().parent / "purge_junk_progress.log"


def _log(msg: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " | " + msg
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def fetch(session):
    return session.query(Document.id, Document.file_size_bytes).filter(
        Document.tenant_id == TENANT,
        Document.name.op('~')(PATTERN),
        or_(Document.extracted_text_length.is_(None),
            Document.extracted_text_length <= TEXT_GUARD),
    ).all()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="skutecne smazat (jinak dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="strop poctu (test)")
    args = ap.parse_args()

    s = get_data_session()
    try:
        rows = fetch(s)
    finally:
        s.close()

    n = len(rows)
    total = sum((r[1] or 0) for r in rows)
    _log("NALEZENO junk: %d souboru, %.2f GB (tenant=%d, pattern=%s, text<=%d)"
         % (n, total / 1073741824.0, TENANT, PATTERN, TEXT_GUARD))
    for r in rows[:5]:
        _log("  vzorek id=%s size=%s" % (r[0], r[1]))

    if not args.execute:
        _log("DRY-RUN — nic nemazu. Pro smazani spust s --execute.")
        return

    ids = [r[0] for r in rows]
    if args.limit:
        ids = ids[:args.limit]
    _log("EXECUTE — mazu %d dokumentu..." % len(ids))
    ok = 0
    fail = 0
    for i, did in enumerate(ids, 1):
        try:
            if delete_document(document_id=did, tenant_id=TENANT):
                ok += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            if fail <= 20:
                _log("  CHYBA id=%s: %s: %s" % (did, type(e).__name__, str(e)[:150]))
        if i % 2000 == 0:
            _log("  ... %d/%d (ok=%d fail=%d)" % (i, len(ids), ok, fail))
    _log("HOTOVO: smazano ok=%d, chyby=%d, z %d." % (ok, fail, len(ids)))


if __name__ == "__main__":
    main()
