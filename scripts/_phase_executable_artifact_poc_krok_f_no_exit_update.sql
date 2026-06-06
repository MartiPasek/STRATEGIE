-- ============================================================================
-- Krok F hotfix — Replace sys.exit() with main() + return
-- ============================================================================
-- ROOT CAUSE (25.5.2026 vecer):
--   Orchestrator pouzival sys.exit(0) ve 3 mistech (row_id is None, !db_url,
--   !ops). sys.exit() raises SystemExit, ktere je BaseException, ne Exception.
--   Runner template (python_runner.py) ma try/except pro ImportError,
--   MemoryError, Exception — ale NE BaseException/SystemExit.
--   → subprocess exit pred JSON dump → empty stdout/stderr → popup "(žádný výstup)"
--
-- TOHLE JE STEJNA GOTCHA jako Krok D fix (raise SystemExit(1) → dropped).
-- Tentokrat wrap do main() funkce s return misto sys.exit.
--
-- Marti's test pattern:
--   1. Klik z STRATEGIE Users grid (jine nez Data Sources) → orchestrator
--      ma vratit info "Žádný op pro data_source_id=X" (rowId neni data_source.id).
--   2. Dnes ale vraci EMPTY (sys.exit crash).
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok F (no-exit hotfix): existence check
#
# Marti's algoritmus (25.5.2026 vecer):
#   1. parse SANDBOX_CONTEXT env (z F2 backend inject)
#   2. SELECT fw.data_source_op WHERE data_source_id=rowId AND kind IN ('edit','insert')
#   3. Pokud row + core_id IS NOT NULL → check fw.core existence
#   4. Pokud row + core_id IS NULL → "není sparovaný"
#   5. Pokud žádný row → "žádný op"
#
# HOTFIX (25.5.2026 vecer + 2): wrap do main() s return misto sys.exit.
# sys.exit raises SystemExit (BaseException), runner template necatch → empty stdout.
import os
import json
import psycopg2


def main():
    print("=" * 64)
    print("✨ Vytvořit edit jádro — Krok F: existence check")
    print("=" * 64)
    print()

    # ── Step 1: Parse context ──────────────────────────────────────────────
    ctx_raw = os.environ.get('SANDBOX_CONTEXT', '{}')
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        print(f"ERROR: SANDBOX_CONTEXT JSON parse failed: {e}")
        print(f"Raw: {ctx_raw!r}")
        ctx = {}

    core_id_grid = ctx.get('coreId')
    core_code_grid = ctx.get('coreCode')
    core_label_grid = ctx.get('coreLabel')
    row_id = ctx.get('rowId')

    print("Context z drop-up menu:")
    print(f"  coreId (grid):    {core_id_grid}")
    print(f"  coreCode (grid):  {core_code_grid}")
    print(f"  coreLabel (grid): {core_label_grid}")
    print(f"  rowId:            {row_id}")
    print()

    if row_id is None:
        print("⚠ rowId is None — orchestrator nedostal kontext řádku.")
        print("  Drop-up menu se musi klikat z řádku gridu (s vybranou row).")
        print()
        print("=" * 64)
        return  # ← BYLO sys.exit(0), HOTFIX: return

    # ── Step 2: Connect ─────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        print("ERROR: STRATEGIE_DATA_DB_URL not set v sandbox env.")
        print()
        print("=" * 64)
        return  # ← BYLO sys.exit(0), HOTFIX: return

    conn = psycopg2.connect(db_url)
    try:
        # ── Step 3: Lookup data_source_op ─────────────────────────────────
        # Predpoklad: rowId = fw.data_source.id (master Data Sources grid).
        # Pokud klikneme z jineho gridu (napr. STRATEGIE Users), rowId NENI
        # data_source.id, takze ops bude prazdne → orchestrator vrati info.
        cur = conn.cursor()
        cur.execute("""
            SELECT id, operation_kind, variant_code, core_id, description
            FROM fw.data_source_op
            WHERE data_source_id = %s
              AND operation_kind IN ('edit', 'insert')
            ORDER BY
              CASE operation_kind WHEN 'edit' THEN 0 ELSE 1 END,
              id ASC
        """, (row_id,))
        ops = cur.fetchall()
        cur.close()

        if not ops:
            print(f"✗ Žádný data_source_op pro data_source_id={row_id} s")
            print(f"  operation_kind IN ('edit', 'insert').")
            print()
            print("Možné příčiny:")
            print(f"  - Klik z jiného než Data Sources gridu (rowId != data_source.id)")
            print(f"  - Tento data_source ještě nemá edit/insert op")
            print()
            print("Krok 2 (další iterace): orchestrator založí op + edit core.")
            print()
            print("=" * 64)
            return  # ← BYLO sys.exit(0), HOTFIX: return

        print(f"Nalezeno {len(ops)} op(s) pro data_source_id={row_id}:")
        print()
        print(f"  {'op_id':>6} {'kind':<8} {'variant':<12} {'core_id':>8}  description")
        print(f"  {'-' * 6} {'-' * 8} {'-' * 12} {'-' * 8}  {'-' * 30}")
        for op in ops:
            op_id, op_kind, variant, c_id, desc = op
            c_id_str = str(c_id) if c_id is not None else "NULL"
            desc_short = (desc[:30] if desc else "") or ""
            variant_str = variant or "NULL"
            print(f"  {op_id:>6} {op_kind:<8} {variant_str:<12} {c_id_str:>8}  {desc_short}")
        print()

        # ── Step 4: Use primary op (priority 'edit' > 'insert') ───────────
        primary_op = ops[0]
        primary_op_id, primary_op_kind, _, primary_core_id, _ = primary_op

        print(f"Primary op (priorita 'edit' > 'insert'):")
        print(f"  op_id = {primary_op_id}")
        print(f"  operation_kind = '{primary_op_kind}'")
        print(f"  core_id = {primary_core_id if primary_core_id is not None else 'NULL'}")
        print()

        # ── Step 5: Check core_id existence ───────────────────────────────
        if primary_core_id is None:
            print(f"⚠ Op #{primary_op_id} ({primary_op_kind}) NENÍ sparován s fw.core.")
            print(f"  core_id = NULL")
            print()
            print(f"Status: SPÁROVÁNÍ CHYBÍ")
            print(f"Krok 2 (další iterace): orchestrator vytvoří fw.core a spáruje.")
        else:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, label, layout_type
                FROM fw.core
                WHERE id = %s
            """, (primary_core_id,))
            core_row = cur.fetchone()
            cur.close()

            if core_row:
                c_id, c_label, c_layout = core_row
                print(f"✓ Edit jádro EXISTUJE")
                print(f"  fw.core.id:     {c_id}")
                print(f"  label:          {c_label or '(NULL)'}")
                print(f"  layout_type:    {c_layout or '(NULL)'}")
                print()
                print(f"Vazba: fw.data_source_op #{primary_op_id} → fw.core #{c_id}")
                print(f"Status: PŘIPRAVENO — edit jádro lze otevřít (CRUD C button).")
            else:
                print(f"⚠ ORPHAN: op #{primary_op_id} ukazuje na core_id={primary_core_id},")
                print(f"  ALE fw.core #{primary_core_id} NEEXISTUJE (broken FK).")
                print()
                print(f"Status: ORPHAN")
                print(f"Krok 2 (další iterace): cleanup orphan + recreate core.")

    finally:
        conn.close()

    print()
    print("=" * 64)
    print("Krok F dokončen.")
    print("=" * 64)


# Top-level: catch broad exceptions, print traceback to stdout
# (runner template by mel chytit, ale defensive print pro debugging).
try:
    main()
except Exception as e:
    import traceback
    print("=" * 64)
    print(f"ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 64)
    print(traceback.format_exc())
$orch$,
    description = 'Krok F hotfix (no sys.exit): existence check edit jádra. Wrap do main() funkce s return misto sys.exit (sys.exit=SystemExit=BaseException → subprocess crash pred JSON dump). PoC scope: rowId = data_source.id (master Data Sources grid). Z jineho gridu vraci info "Žádný op".',
    updated_at = NOW()
WHERE code = 'vytvor_edit_jadro';

-- Verify UPDATE
SELECT
  id,
  code,
  artifact_type,
  LENGTH(source) AS source_length_chars,
  updated_at
FROM fw.executable_artifact
WHERE code = 'vytvor_edit_jadro';
-- Expected: 1 row, source_length_chars ~4200, updated_at = teď
