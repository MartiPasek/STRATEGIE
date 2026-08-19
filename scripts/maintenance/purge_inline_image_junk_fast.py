# -*- coding: utf-8 -*-
"""
purge_inline_image_junk_fast.py — RYCHLA verze uklidu inline e-mailovych obrazku
(image001.jpg apod.) tenant 2. Stejny bezpecnostni filtr jako purge_inline_image_junk.py,
ale mnohem rychlejsi: bulk DELETE v DB po davkach (vektory->chunky->documents, explicitne,
nezavisle na cascade) + PARALELNI mazani souboru (ThreadPool).

Filtr: tenant_id=2 AND name ~ '^image[0-9]+\\.(jpg|jpeg|png)$'
       AND (extracted_text_length IS NULL OR <= 800).  (max text v setu = 228 -> zadny realny doc)

Pouziti (na 188.11, cd C:\\Projekty\\STRATEGIE):
  python scripts\\maintenance\\purge_inline_image_junk_fast.py            # DRY-RUN
  python scripts\\maintenance\\purge_inline_image_junk_fast.py --execute  # SMAZE
Resumovatelne. C23 19.8.2026, schvalil Marti Pasek.
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text as sql_text
from core.database_data import get_data_session

TENANT = 2
PATTERN = r'^[Ii]mage[0-9]+\.(jpg|jpeg|png)$'
TEXT_GUARD = 800
BATCH = 2000
THREADS = 24
LOG = Path(__file__).resolve().parent / "purge_junk_fast_progress.log"


def _log(msg: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " | " + msg
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


SEL = sql_text(
    "SELECT id, storage_path, coalesce(file_size_bytes,0) "
    "FROM documents WHERE tenant_id=:t AND name ~ :pat "
    "AND (extracted_text_length IS NULL OR extracted_text_length <= :tg)"
)


def _rm(path):
    try:
        if path:
            os.remove(path)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    s = get_data_session()
    try:
        rows = s.execute(SEL, {"t": TENANT, "pat": PATTERN, "tg": TEXT_GUARD}).fetchall()
    finally:
        s.close()

    n = len(rows)
    total = sum((r[2] or 0) for r in rows)
    _log("NALEZENO junk: %d souboru, %.2f GB" % (n, total / 1073741824.0))
    if not args.execute:
        _log("DRY-RUN — nic nemazu.")
        return

    _log("EXECUTE (fast) — mazu %d dokumentu, batch=%d, threads=%d..." % (n, BATCH, THREADS))
    t0 = time.time()
    done = 0
    freed = 0
    files_ok = 0
    files_err = 0
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        for start in range(0, n, BATCH):
            chunk = rows[start:start + BATCH]
            ids = [r[0] for r in chunk]
            # 1) DB bulk delete (explicitne: vektory -> chunky -> documents)
            s = get_data_session()
            try:
                s.execute(sql_text(
                    "DELETE FROM document_vectors WHERE chunk_id IN "
                    "(SELECT id FROM document_chunks WHERE document_id = ANY(:ids))"), {"ids": ids})
                s.execute(sql_text(
                    "DELETE FROM document_chunks WHERE document_id = ANY(:ids)"), {"ids": ids})
                s.execute(sql_text(
                    "DELETE FROM documents WHERE id = ANY(:ids)"), {"ids": ids})
                s.commit()
            except Exception as e:
                s.rollback()
                _log("  CHYBA DB batch @%d: %s: %s" % (start, type(e).__name__, str(e)[:150]))
                s.close()
                continue
            finally:
                s.close()
            # 2) soubory paralelne
            results = list(pool.map(_rm, [r[1] for r in chunk]))
            files_ok += sum(1 for x in results if x)
            files_err += sum(1 for x in results if not x)
            freed += sum((r[2] or 0) for r in chunk)
            done += len(chunk)
            rate = done / max(time.time() - t0, 0.001)
            _log("  ... %d/%d (%.2f GB uvolneno, %.0f/s, soubory ok=%d err=%d)"
                 % (done, n, freed / 1073741824.0, rate, files_ok, files_err))
    _log("HOTOVO: smazano %d dokumentu, %.2f GB uvolneno (soubory ok=%d err=%d)."
         % (done, freed / 1073741824.0, files_ok, files_err))


if __name__ == "__main__":
    main()
