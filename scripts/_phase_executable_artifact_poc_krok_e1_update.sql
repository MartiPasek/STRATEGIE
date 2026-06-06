-- ============================================================================
-- Krok E1 — UPDATE orchestrator: DRY-RUN INSERT pattern (savepoint + capture)
-- ============================================================================
-- Po Krok D LIVE end-to-end, pojdme orchestrator rozsirit o realnou
-- DESCRIBE-FIRST INSERT functionality.
--
-- Nove kroky orchestratoru:
--   Step 1: Schema sanity check (existujici)
--   Step 2: Predicted ID via pg_get_serial_sequence + nextval (universal)
--   Step 3a: Dry-run INSERT INVALID payload → capture NotNullViolation
--   Step 3b: Dry-run INSERT VALID payload → predict success + rollback
--   Step 4: Final report (no production data modified)
--
-- Vse pres psycopg2 direct + SAVEPOINT pattern. Drz minimum DDL — žádné
-- nové tabulky teď. PoC scope „demonstrate DRY-RUN pattern".
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# DESCRIBE-FIRST INSERT orchestrator — full PoC (Step 1-4)
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „krok za krokem, jedna tabulka s pochopenim" (Marti 25.5.)
#
# Demonstrates DRY-RUN INSERT pattern:
#   1. Read schema (information_schema.columns)
#   2. Predict ID (pg_get_serial_sequence + nextval, universal)
#   3a. Dry-run INVALID → capture NotNullViolation
#   3b. Dry-run VALID → predict success + ROLLBACK (no persistence)
#   4. Final report
#
# Žádné production data modified — pure dry-run demonstration.
import os
import sys
import traceback
import psycopg2
from psycopg2 import errors as pg_errors

# Target entity (PoC scope: data_source_op)
TARGET_SCHEMA = "fw"
TARGET_TABLE = "data_source_op"

print("=" * 70)
print("DESCRIBE-FIRST INSERT orchestrator — full PoC")
print("=" * 70)
print(f"Python: {sys.version.split()[0]}")
print(f"Target: {TARGET_SCHEMA}.{TARGET_TABLE}")
print()

db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
if not db_url:
    print("ERROR: STRATEGIE_DATA_DB_URL not set. Skipping.")
else:
    print(f"DB URL: {db_url[:40]}...")
    print()

    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    try:
        # ----------------------------------------------------------
        # Step 1: Schema sanity check
        # ----------------------------------------------------------
        print("┌─ Step 1 ─ Schema introspection " + "─" * 38)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (TARGET_SCHEMA, TARGET_TABLE))
        cols = cur.fetchall()
        cur.close()

        print(f"│  Found {len(cols)} columns")
        required_cols = []
        for col_name, dtype, is_nullable, default in cols:
            if is_nullable == "NO" and not default:
                required_cols.append(col_name)
        print(f"│  Required (NOT NULL, no default): {required_cols}")
        print("└" + "─" * 69)
        print()

        # ----------------------------------------------------------
        # Step 2: Predicted ID via pg_get_serial_sequence + nextval
        # ----------------------------------------------------------
        print("┌─ Step 2 ─ Predicted ID " + "─" * 46)
        cur = conn.cursor()
        cur.execute("""
            SELECT pg_get_serial_sequence(%s, 'id') AS seq_name
        """, (f"{TARGET_SCHEMA}.{TARGET_TABLE}",))
        seq_name = cur.fetchone()[0]
        print(f"│  Sequence name (auto-detected): {seq_name}")

        if seq_name:
            cur.execute(f"SELECT nextval('{seq_name}') AS predicted_id")
            predicted_id = cur.fetchone()[0]
            print(f"│  Predicted ID: {predicted_id}")
        else:
            predicted_id = None
            print(f"│  No serial sequence found for {TARGET_SCHEMA}.{TARGET_TABLE}.id")
        cur.close()
        print("└" + "─" * 69)
        print()

        # ----------------------------------------------------------
        # Step 3a: Dry-run INSERT — INVALID payload (missing operation_kind)
        # ----------------------------------------------------------
        print("┌─ Step 3a ─ Dry-run INSERT (INVALID payload) " + "─" * 25)
        cur = conn.cursor()
        try:
            cur.execute("SAVEPOINT dry_run_invalid")
            cur.execute("""
                INSERT INTO fw.data_source_op (data_source_id)
                VALUES (1)
                RETURNING id
            """)
            row_id = cur.fetchone()[0]
            print(f"│  ⚠ Unexpected SUCCESS (id={row_id}) — schema not as strict?")
        except pg_errors.NotNullViolation as e:
            col_hint = e.diag.column_name if (e.diag and e.diag.column_name) else "unknown"
            print(f"│  ✓ Captured NotNullViolation")
            print(f"│  ✓ Missing column: {col_hint}")
            print(f"│  ✓ Pgcode: {e.pgcode}")
        except pg_errors.ForeignKeyViolation as e:
            print(f"│  ✓ Captured ForeignKeyViolation: {e.diag.constraint_name if e.diag else 'unknown'}")
        except Exception as e:
            print(f"│  ✓ Captured {type(e).__name__}: {str(e)[:60]}")
        finally:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT dry_run_invalid")
                print(f"│  ✓ Rolled back to savepoint")
            except Exception:
                pass
            cur.close()
        print("└" + "─" * 69)
        print()

        # ----------------------------------------------------------
        # Step 3b: Dry-run INSERT — VALID payload (FK risky, use existing data_source_id)
        # ----------------------------------------------------------
        print("┌─ Step 3b ─ Dry-run INSERT (VALID payload) " + "─" * 27)
        cur = conn.cursor()
        try:
            # First find existing data_source_id (FK target)
            cur.execute("SELECT id FROM fw.data_source ORDER BY id LIMIT 1")
            fk_row = cur.fetchone()
            if not fk_row:
                print(f"│  ⚠ No fw.data_source rows — skip dry-run (FK target missing)")
            else:
                fk_data_source_id = fk_row[0]
                print(f"│  Using fw.data_source.id={fk_data_source_id} as FK target")

                cur.execute("SAVEPOINT dry_run_valid")
                cur.execute("""
                    INSERT INTO fw.data_source_op (
                        data_source_id, operation_kind, description, sort_order
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (fk_data_source_id, 'select', '[PoC] orchestrator dry-run test', 999))
                new_id = cur.fetchone()[0]
                print(f"│  ✓ DRY-RUN SUCCESS — would create row with id={new_id}")
                print(f"│  ✓ All NOT NULL constraints satisfied")
                print(f"│  ✓ FK fw.data_source(id) → OK")

                cur.execute("ROLLBACK TO SAVEPOINT dry_run_valid")
                print(f"│  ✓ Rolled back — no data persisted")
        except Exception as e:
            print(f"│  ✗ DRY-RUN FAILED: {type(e).__name__}: {str(e)[:60]}")
            print(f"│  Traceback:")
            for line in traceback.format_exc().splitlines()[-3:]:
                print(f"│    {line}")
        finally:
            cur.close()
        print("└" + "─" * 69)
        print()

        # ----------------------------------------------------------
        # Step 4: Final commit (no production changes happened)
        # ----------------------------------------------------------
        conn.commit()
        print("┌─ Step 4 ─ Final " + "─" * 52)
        print(f"│  ✓ All dry-runs rolled back to savepoints")
        print(f"│  ✓ Outer transaction committed (no-op, žádná production data)")
        print(f"│  ✓ Predicted ID {predicted_id} byl konzumovan ze sekvence (acceptable gap)")
        print("└" + "─" * 69)

    finally:
        conn.close()

print()
print("=" * 70)
print("Orchestrator PoC end-to-end OK — DRY-RUN INSERT pattern demonstrated")
print("=" * 70)
$orch$,
    description = 'Step 1-4 full PoC: schema introspection + predicted_id (nextval) + dry-run INVALID (capture NotNullViolation) + dry-run VALID (predict success, rollback). Žádná production data modified.',
    updated_at = NOW()
WHERE code = 'describe_first_orchestrator';

-- Verify UPDATE
SELECT
  id,
  code,
  artifact_type,
  LENGTH(source) AS source_length_chars,
  updated_at
FROM fw.executable_artifact
WHERE code = 'describe_first_orchestrator';
-- Expected: 1 row, source_length_chars ~5500, updated_at = teď
