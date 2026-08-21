# -*- coding: utf-8 -*-
"""
purge_docs_by_tenant.py — smaze VSECHNY dokumenty danych tenantu z DB
(bulk DELETE vektory->chunky->documents + pokus o smazani souboru).
Pouziti pro uklid osirelych zaznamu tenantu 2 a 12 (Marti rucne smazal slozky \\2 a \\12
na disku 21.8. → soubory uz nejsou, tady se doklizi DB). Schvalil Marti 21.8.2026.

Pouziti (na 188.11, cd C:\\Projekty\\STRATEGIE):
  python scripts\\maintenance\\purge_docs_by_tenant.py --tenants 2,12            # DRY-RUN
  python scripts\\maintenance\\purge_docs_by_tenant.py --tenants 2,12 --execute  # SMAZE
Resumovatelne. C23 21.8.2026.
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
LOG = Path(__file__).resolve().parent / "purge_by_tenant_progress.log"


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
    ap.add_argument("--tenants", required=True, help="comma list, napr. 2,12")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    tenants = [int(x) for x in args.tenants.split(",") if x.strip()]

    sel = sql_text("SELECT id, storage_path FROM documents WHERE tenant_id = ANY(:t)")
    s = get_data_session()
    try:
        rows = s.execute(sel, {"t": tenants}).fetchall()
    finally:
        s.close()

    n = len(rows)
    _log("NALEZENO tenants=%s: %d dokumentu (DB zaznamy; soubory uz smazane rucne)" % (tenants, n))
    if not args.execute:
        _log("DRY-RUN — nic nemazu.")
        return

    _log("EXECUTE — mazu %d dokumentu (batch=%d)..." % (n, BATCH))
    t0 = time.time()
    done = 0
    files_ok = 0
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
            files_ok += sum(1 for x in list(pool.map(_rm, [r[1] for r in chunk])) if x)
            done += len(chunk)
            _log("  ... %d/%d (%.0f/s)" % (done, n, done / max(time.time() - t0, 0.001)))
    _log("HOTOVO: smazano %d DB zaznamu (tenants=%s)." % (done, tenants))


if __name__ == "__main__":
    main()
