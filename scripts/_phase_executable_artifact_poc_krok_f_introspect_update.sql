-- ============================================================================
-- Krok F hotfix #4 — Schema introspection FIRST (stop guessing)
-- ============================================================================
-- Marti's catches (25.5.2026 vecer, 3x v rade):
--   #1: fw.comp_def nema 'code' ani 'label'
--   #2: fw.comp_def nema 'parent_core_id'
--   → MOJE PAMET SCHEMA JE NESPOLEHLIVA
--
-- DOCTRINE shift:
--   Orchestrator NEJDRIV introspectuje skutecne sloupce (information_schema),
--   teprve POTOM Marti rozhodne, jak chain napsat.
--
-- Marti's chain z predchozi zpravy (potvrzeny LOGICKY, NE column names):
--   fw.core -> fw.comp_def -> data_source -> data_source_op -> vazba core_id
--
-- Tahle verze:
--   1. Print columns vsech 4 tabulek (fw.core, fw.comp_def, fw.data_source,
--      fw.data_source_op).
--   2. Marti se na to podiva, rekne ktere sloupce jsou pro chain.
--   3. Pristi iterace orchestratoru napise spravny chain.
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok F hotfix #4: SCHEMA INTROSPECTION
#
# Marti's chain z predchozi zpravy (LOGIKA, ne column names):
#   fw.core -> fw.comp_def -> fw.data_source -> fw.data_source_op -> vazba core_id
#
# Claudova pamet schema je nespolehliva (2x guess fail v rade).
# Doctrine: introspect FIRST, Marti decide column names, then chain.
import os
import json
import psycopg2


def main():
    print("=" * 70)
    print("✨ Vytvořit edit jádro — Krok F: SCHEMA INTROSPECTION")
    print("=" * 70)
    print()

    # ── Step 1: Parse context ──────────────────────────────────────────────
    ctx_raw = os.environ.get('SANDBOX_CONTEXT', '{}')
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        print(f"ERROR: SANDBOX_CONTEXT JSON parse failed: {e}")
        ctx = {}

    core_id = ctx.get('coreId')
    core_code = ctx.get('coreCode')
    core_label = ctx.get('coreLabel')

    print("Context z drop-up menu:")
    print(f"  coreId:    {core_id}")
    print(f"  coreCode:  {core_code}")
    print(f"  coreLabel: {core_label}")
    print()

    # ── Step 2: Connect ─────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        print("ERROR: STRATEGIE_DATA_DB_URL not set v sandbox env.")
        print()
        print("=" * 70)
        return

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        # ── Step 3: Introspect 4 tabulek ───────────────────────────────────
        tables = ['core', 'comp_def', 'data_source', 'data_source_op']

        for tbl in tables:
            print("─" * 70)
            print(f"fw.{tbl}")
            print("─" * 70)

            cur.execute("""
                SELECT
                  column_name,
                  data_type,
                  is_nullable,
                  column_default
                FROM information_schema.columns
                WHERE table_schema = 'fw'
                  AND table_name = %s
                ORDER BY ordinal_position
            """, (tbl,))
            cols = cur.fetchall()

            if not cols:
                print(f"  ⚠ Tabulka fw.{tbl} NEEXISTUJE nebo nema sloupce")
                print()
                continue

            print(f"  {'column':<30} {'type':<20} {'null':<6} default")
            print(f"  {'-' * 30} {'-' * 20} {'-' * 6} {'-' * 20}")
            for col in cols:
                col_name, col_type, col_null, col_default = col
                null_str = 'YES' if col_null == 'YES' else 'NO'
                default_str = (str(col_default)[:20] if col_default else '')
                print(f"  {col_name:<30} {col_type:<20} {null_str:<6} {default_str}")
            print()

        cur.close()

        # ── Step 4: Ukazat row count pro context ───────────────────────────
        print("─" * 70)
        print("ROW COUNTS:")
        print("─" * 70)
        for tbl in tables:
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT COUNT(*) FROM fw.{tbl}")
                cnt = cur.fetchone()[0]
                print(f"  fw.{tbl:<25} {cnt:>10} rows")
            except Exception as e:
                print(f"  fw.{tbl:<25} ERROR: {e}")
            cur.close()
        print()

        # ── Step 5: Pokud coreId existuje, ukazat konkretni core row ───────
        if core_id is not None:
            print("─" * 70)
            print(f"fw.core WHERE id = {core_id}:")
            print("─" * 70)
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM fw.core WHERE id = %s", (core_id,))
                row = cur.fetchone()
                if row:
                    col_names = [desc[0] for desc in cur.description]
                    for cname, cval in zip(col_names, row):
                        val_str = str(cval)[:60] if cval is not None else 'NULL'
                        print(f"  {cname:<30} = {val_str}")
                else:
                    print(f"  (žádný row s id={core_id})")
                cur.close()
            except Exception as e:
                print(f"  ERROR: {e}")
            print()

    finally:
        conn.close()

    print("=" * 70)
    print("Introspection dokončena.")
    print("Marti: rozhodni, ktere sloupce jsou pro chain")
    print("  core → comp_def → data_source → data_source_op → core_id")
    print("=" * 70)


# Top-level: catch broad exceptions
try:
    main()
except Exception as e:
    import traceback
    print("=" * 70)
    print(f"ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 70)
    print(traceback.format_exc())
$orch$,
    description = 'Krok F hotfix #4 INTROSPECTION: vypise skutecne sloupce fw.core/comp_def/data_source/data_source_op + row counts + konkretni core row. Marti rozhodne, ktere sloupce jsou pro chain (Claudova pamet schema je 2x v rade fail).',
    updated_at = NOW()
WHERE code = 'vytvor_edit_jadro';

-- Verify
SELECT
  id,
  code,
  LENGTH(source) AS source_length_chars,
  updated_at
FROM fw.executable_artifact
WHERE code = 'vytvor_edit_jadro';
