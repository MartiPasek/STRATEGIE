-- ============================================================================
-- Krok F hotfix #3 — fw.comp_def schema fix (drop nonexistent columns)
-- ============================================================================
-- Marti's catch (25.5.2026 vecer):
--   UndefinedColumn: column "code" does not exist
--   LINE 2:             SELECT id, code, label, data_source_id
--                                ^
--
-- ROOT CAUSE moje chyba:
--   Predpokladal jsem ze fw.comp_def ma sloupce 'code' a 'label' (analog
--   fw.core/fw.data_source). Realita: comp_def ma jine sloupce
--   (comp_id, caption, comp_type_id, atd.), 'code' a 'label' tam nejsou.
--
-- FIX:
--   Drop 'code' a 'label' z SELECT v Step 3. Pro chain potrebujeme jen
--   'id' (PK) a 'data_source_id' (FK k fw.data_source). Zbytek byl jen
--   pro popup verbose info — nahradime za '#<id>'.
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok F hotfix #3: comp_def schema fix
#
# Marti's algoritmus chain (potvrzeno 25.5.2026):
#   fw.core → fw.comp_def → data_source → data_source_op → vazba edit/insert na core_id
#
# HOTFIX #3: fw.comp_def nema 'code' ani 'label' columns. Drop je.
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

    core_id = ctx.get('coreId')
    core_code = ctx.get('coreCode')
    core_label = ctx.get('coreLabel')

    print("Context z drop-up menu:")
    print(f"  coreId:    {core_id}")
    print(f"  coreCode:  {core_code}")
    print(f"  coreLabel: {core_label}")
    print()

    if core_id is None:
        print("⚠ coreId is None — orchestrator nedostal kontext gridu.")
        print()
        print("=" * 64)
        return

    # ── Step 2: Connect ─────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        print("ERROR: STRATEGIE_DATA_DB_URL not set v sandbox env.")
        print()
        print("=" * 64)
        return

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        # ── Step 3: fw.comp_def → data_source_id ───────────────────────────
        # Grid root = comp_def s parent_core_id=coreId a data_source_id NOT NULL.
        # Minimal SELECT — jen id + data_source_id (zbytek schemy varies).
        cur.execute("""
            SELECT id, data_source_id
            FROM fw.comp_def
            WHERE parent_core_id = %s
              AND data_source_id IS NOT NULL
              AND COALESCE(is_active, true) = true
            ORDER BY id ASC
            LIMIT 5
        """, (core_id,))
        grid_roots = cur.fetchall()

        if not grid_roots:
            print(f"⚠ Žádný comp_def s parent_core_id={core_id} a")
            print(f"  data_source_id NOT NULL.")
            print()
            print(f"  fw.core #{core_id} ({core_label}) možná nemá grid root,")
            print(f"  nebo grid root nemá vazbu na data_source.")
            print()
            print("=" * 64)
            return

        print(f"Nalezeno {len(grid_roots)} grid root(s) pro fw.core #{core_id}:")
        for gr in grid_roots:
            gr_id, gr_ds_id = gr
            print(f"  comp_def #{gr_id} → data_source_id={gr_ds_id}")
        print()

        # Primary grid root = prvni v poradi
        primary_root = grid_roots[0]
        primary_comp_def_id = primary_root[0]
        primary_ds_id = primary_root[1]

        print(f"Primary grid root: comp_def #{primary_comp_def_id}")
        print(f"  → data_source_id = {primary_ds_id}")
        print()

        # ── Step 4: fw.data_source lookup ──────────────────────────────────
        cur.execute("""
            SELECT id, code, label
            FROM fw.data_source
            WHERE id = %s
        """, (primary_ds_id,))
        ds_row = cur.fetchone()

        if not ds_row:
            print(f"⚠ ORPHAN: comp_def ukazuje na data_source_id={primary_ds_id},")
            print(f"  ALE fw.data_source #{primary_ds_id} NEEXISTUJE (broken FK).")
            print()
            print("=" * 64)
            return

        ds_id, ds_code, ds_label = ds_row
        print(f"Data source: fw.data_source #{ds_id}")
        print(f"  code:  {ds_code}")
        print(f"  label: {ds_label or 'NULL'}")
        print()

        # ── Step 5: SELECT data_source_op (kind IN edit, insert) ───────────
        cur.execute("""
            SELECT id, operation_kind, variant_code, core_id, description
            FROM fw.data_source_op
            WHERE data_source_id = %s
              AND operation_kind IN ('edit', 'insert')
            ORDER BY
              CASE operation_kind WHEN 'edit' THEN 0 ELSE 1 END,
              id ASC
        """, (ds_id,))
        ops = cur.fetchall()
        cur.close()

        if not ops:
            print(f"✗ Žádný data_source_op pro data_source_id={ds_id} s")
            print(f"  operation_kind IN ('edit', 'insert').")
            print()
            print(f"Status: EDIT JÁDRO NEEXISTUJE")
            print(f"Krok 2 (další iterace): orchestrator založí op + edit core.")
            print()
            print("=" * 64)
            return

        print(f"Nalezeno {len(ops)} op(s) pro data_source_id={ds_id}:")
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

        # ── Step 6: Use primary op (priority 'edit' > 'insert') ────────────
        primary_op = ops[0]
        primary_op_id, primary_op_kind, _, primary_core_id, _ = primary_op

        print(f"Primary op (priorita 'edit' > 'insert'):")
        print(f"  op_id = {primary_op_id}")
        print(f"  operation_kind = '{primary_op_kind}'")
        print(f"  core_id = {primary_core_id if primary_core_id is not None else 'NULL'}")
        print()

        # ── Step 7: Check core_id existence ────────────────────────────────
        if primary_core_id is None:
            print(f"⚠ Op #{primary_op_id} ({primary_op_kind}) NENÍ sparován s fw.core.")
            print(f"  core_id = NULL")
            print()
            print(f"Status: SPÁROVÁNÍ CHYBÍ")
            print(f"Krok 2 (další iterace): orchestrator vytvoří fw.core a spáruje.")
        else:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, layout_type
                FROM fw.core
                WHERE id = %s
            """, (primary_core_id,))
            core_row = cur.fetchone()
            cur.close()

            if core_row:
                c_id, c_code, c_label, c_layout = core_row
                print(f"✓ Edit jádro EXISTUJE")
                print(f"  fw.core.id:     {c_id}")
                print(f"  code:           {c_code or '(NULL)'}")
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
try:
    main()
except Exception as e:
    import traceback
    print("=" * 64)
    print(f"ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 64)
    print(traceback.format_exc())
$orch$,
    description = 'Krok F hotfix #3: comp_def schema fix (drop code/label z SELECT — nonexistent columns). Chain: coreId → fw.comp_def (id+data_source_id) → fw.data_source (code+label) → fw.data_source_op → vazba core_id.',
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
