# -*- coding: utf-8 -*-
"""
purge_docs_by_user.py — smaze VSECHNY dokumenty daneho tenanta+uzivatele
(bulk DELETE vektory->chunky->documents + paralelni mazani souboru).
Pouziti pro vymazani mailboxu projects@eurosoft.com = tenant 2, user_id 111 (schvalil Marti 20.8.).

Pouziti (na 188.11, cd C:\\Projekty\\STRATEGIE):
  python scripts\\maintenance\\purge_docs_by_user.py --tenant 2 --user 111            # DRY-RUN
  python scripts\\maintenance\\purge_docs_by_user.py --tenant 2 --user 111 --execute  # SMAZE
Resumovatelne. C23 20.8.2026.
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

BATCH = 2000
THREADS = 24
LOG = Path(__file__).resolve().parent / "purge_by_user_progress.log"


def _log(msg: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " | " + msg
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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
    ap.add_argument("--tenant", type=int, required=True)
    ap.add_argument("--user", type=int, required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    sel = sql_text(
        "SELECT id, storage_path, coalesce(file_size_bytes,0), "
        "CASE WHEN lower(name) LIKE '%.pdf' THEN 'pdf' "
        "WHEN lower(name) ~ '\\.(jpg|jpeg|png)$' THEN 'img' ELSE 'other' END AS kind "
        "FROM documents WHERE tenant_id=:t AND user_id=:u"
    )
    s = get_data_session()
    try:
        rows = s.execute(sel, {"t": args.tenant, "u": args.user}).fetchall()
    finally:
        s.close()

    n = len(rows)
    total = sum((r[2] or 0) for r in rows)
    by = {}
    for r in rows:
        by[r[3]] = by.get(r[3], 0) + 1
    _log("NALEZENO tenant=%d user=%d: %d dokumentu, %.2f GB | %s"
         % (args.tenant, args.user, n, total / 1073741824.0, by))
    if not args.execute:
        _log("DRY-RUN — nic nemazu.")
        return

    _log("EXECUTE — mazu %d dokumentu (batch=%d, threads=%d)..." % (n, BATCH, THREADS))
    t0 = time.time()
    done = 0
    freed = 0
    files_ok = 0
    files_err = 0
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        for start in range(0, n, BATCH):
            chunk = rows[start:start + BATCH]
            ids = [r[0] for r in chunk]
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
            results = list(pool.map(_rm, [r[1] for r in chunk]))
            files_ok += sum(1 for x in results if x)
            files_err += sum(1 for x in results if not x)
            freed += sum((r[2] or 0) for r in chunk)
            done += len(chunk)
            rate = done / max(time.time() - t0, 0.001)
            _log("  ... %d/%d (%.2f GB, %.0f/s, soubory ok=%d err=%d)"
                 % (done, n, freed / 1073741824.0, rate, files_ok, files_err))
    _log("HOTOVO: smazano %d, %.2f GB uvolneno (soubory ok=%d err=%d)."
         % (done, freed / 1073741824.0, files_ok, files_err))


if __name__ == "__main__":
    main()
