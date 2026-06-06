-- ============================================================================
-- Krok F hotfix #5 — Chain LIVE (po schema introspection)
-- ============================================================================
-- Marti's "SIKOVNEJ!!!!" potvrzeni introspection result (25.5.2026 vecer):
--
-- SKUTECNE SLOUPCE (z introspection #4):
--   fw.core         : id, code, label, description_user, is_active, ...
--                     (NEMA layout_type — Marti dropnul v Krok 5.P 17.5.)
--   fw.comp_def     : id, parent_id, type_id, name, caption, layout,
--                     parent_comp_def_id, CORE_ID (← KLIC), data_source_id
--   fw.data_source  : id, code, version, name, status, ...
--   fw.data_source_op: id, data_source_id, data_set_id, operation_kind,
--                      variant_code, CORE_ID (← VAZBA NA EDIT JADRO)
--
-- CHAIN (Marti's algoritmus implementovany na realne schema):
--   1. fw.core #coreId (z context)
--   2. fw.comp_def WHERE core_id=coreId AND data_source_id IS NOT NULL
--      (grid root — pouze 1 row pro daný core)
--   3. fw.data_source WHERE id = comp_def.data_source_id
--   4. fw.data_source_op WHERE data_source_id=X
--                          AND operation_kind IN ('edit','insert')
--   5. IF op.core_id IS NOT NULL:
--        SELECT fw.core WHERE id = op.core_id
--        → EXISTUJE (popis) / ORPHAN (broken FK)
--      ELIF op.core_id IS NULL:
--        SPAROVANI CHYBI (op existuje, ale neni napojen)
--   6. IF zadny op: EDIT JADRO NEEXISTUJE (krok 2 vytvori)
--
-- HOTFIX z hotfix #4 (introspection):
--   - Zmena parent_core_id → core_id (jeden radek v Step 3 SELECT)
--   - Drop layout_type z fw.core SELECT v Step 7 (Marti dropnul 17.5.)
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok F hotfix #5: CHAIN LIVE
#
# Po schema introspection (hotfix #4) — chain napsany na realne sloupce.
#
# Marti's algoritmus:
#   fw.core → fw.comp_def (core_id, data_source_id NOT NULL)
#          → fw.data_source → fw.data_source_op (kind edit/insert)
#          → vazba op.core_id na fw.core (existence check)
import os
import json
import psycopg2


def main():
    print("=" * 70)
    print("✨ Vytvořit edit jádro — Krok F: existence check")
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

    if core_id is None:
        print("⚠ coreId is None — orchestrator nedostal kontext gridu.")
        print("=" * 70)
        return

    # ── Step 2: Connect ─────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        print("ERROR: STRATEGIE_DATA_DB_URL not set v sandbox env.")
        print("=" * 70)
        return

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        # ── Step 3: fw.comp_def WHERE core_id=X AND data_source_id NOT NULL ─
        # Grid root = comp_def asociovany s core, ktery ma vazbu na data_source.
        cur.execute("""
            SELECT id, name, caption, data_source_id
            FROM fw.comp_def
            WHERE core_id = %s
              AND data_source_id IS NOT NULL
              AND COALESCE(is_active, true) = true
            ORDER BY id ASC
            LIMIT 5
        """, (core_id,))
        grid_roots = cur.fetchall()
        cur.close()

        if not grid_roots:
            print(f"⚠ Žádný fw.comp_def s core_id={core_id} a")
            print(f"  data_source_id NOT NULL.")
            print()
            print(f"  fw.core #{core_id} ({core_label}) možná nemá grid root,")
            print(f"  nebo grid root nemá vazbu na data_source.")
            print()
            print("=" * 70)
            return

        print(f"Grid root(s) pro fw.core #{core_id}:")
        for gr in grid_roots:
            gr_id, gr_name, gr_caption, gr_ds_id = gr
            print(f"  comp_def #{gr_id} | name={gr_name} | "
                  f"caption={gr_caption or 'NULL'} | "
                  f"data_source_id={gr_ds_id}")
        print()

        # Primary grid root = prvni v poradi (po sort_order/id)
        primary_root = grid_roots[0]
        primary_comp_def_id = primary_root[0]
        primary_ds_id = primary_root[3]

        # ── Step 4: fw.data_source lookup ──────────────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, name, status
            FROM fw.data_source
            WHERE id = %s
        """, (primary_ds_id,))
        ds_row = cur.fetchone()
        cur.close()

        if not ds_row:
            print(f"⚠ ORPHAN: comp_def #{primary_comp_def_id} ukazuje na")
            print(f"  data_source_id={primary_ds_id}, ALE fw.data_source")
            print(f"  #{primary_ds_id} NEEXISTUJE (broken FK).")
            print()
            print("=" * 70)
            return

        ds_id, ds_code, ds_name, ds_status = ds_row
        print(f"Data source: fw.data_source #{ds_id}")
        print(f"  code:   {ds_code or 'NULL'}")
        print(f"  name:   {ds_name}")
        print(f"  status: {ds_status}")
        print()

        # ── Step 5: SELECT data_source_op (kind IN edit, insert) ───────────
        cur = conn.cursor()
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
            print("=" * 70)
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

        # ── Step 7: Check core_id existence (vazba na edit jadro) ──────────
        if primary_core_id is None:
            print(f"⚠ Op #{primary_op_id} ({primary_op_kind}) NENÍ sparován s fw.core.")
            print(f"  core_id = NULL")
            print()
            print(f"Status: SPÁROVÁNÍ CHYBÍ")
            print(f"Krok 2 (další iterace): orchestrator vytvoří fw.core a spáruje.")
        else:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, label, description_user
                FROM fw.core
                WHERE id = %s
            """, (primary_core_id,))
            core_row = cur.fetchone()
            cur.close()

            if core_row:
                c_id, c_code, c_label, c_desc = core_row
                print(f"✓ Edit jádro EXISTUJE")
                print(f"  fw.core.id:     {c_id}")
                print(f"  code:           {c_code or '(NULL)'}")
                print(f"  label:          {c_label or '(NULL)'}")
                desc_short = (c_desc[:60] if c_desc else '(NULL)') or '(NULL)'
                print(f"  description:    {desc_short}")
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
    print("=" * 70)
    print("Krok F dokončen.")
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
    description = 'Krok F hotfix #5 CHAIN LIVE: po schema introspection (#4). Chain: fw.core → fw.comp_def (core_id, data_source_id NOT NULL) → fw.data_source → fw.data_source_op (edit/insert) → vazba op.core_id na fw.core (EXISTUJE/ORPHAN/SPAROVANI CHYBI/EDIT NEEXISTUJE).',
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
