-- ============================================================================
-- Krok G++ DEFENSIVE — context vs DB row mismatch detection
-- ============================================================================
-- Marti's volba B (po Q+A analyzy):
--   "Detekce coreId/coreCode mismatch + vraceni jasne error message
--    misto silent wrong work."
--
-- ROOT CAUSE (dnesni buggy smoke):
--   Drop-up menu v nested detail gridu (data_source_op_detail.js z Volby A)
--   poslalo:
--     - coreId=44   ← outer Diag log's fw.core.id (NAHODNA collision)
--     - coreCode='system_new.framework_data_source_ops'  ← nested context
--     - coreLabel='Operace data sourcu #35'              ← nested context
--   Orchestrator polozil DB v inconsistent state (core #50 s wrong label).
--
-- FIX (Step 2.5 — new defensive check):
--   Po Step 2 (connect) + pred Step 3 (chain), porovnat:
--     SELECT code, label FROM fw.core WHERE id = coreId
--   vs received coreCode, coreLabel.
--   Pokud mismatch (a oba fields jsou non-NULL na obou stranach) → error message
--   + return (no destructive work).
--
-- Edge cases:
--   - DB fw.core #coreId NEEXISTUJE → error "coreId odkazuje na neexistujici fw.core"
--   - Context coreCode/coreLabel jsou NULL → skip check pro chybejici field
--   - DB code/label jsou NULL → skip check pro chybejici field
--   (= bezpecne, conservative comparison)
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok G++: defensive context validation
#
# Step 2.5 (new): Validate received coreId/coreCode/coreLabel proti DB row.
# Pokud mismatch → error + return (chrani pred dnesni buggy smoke z nested
# detail context, kde drop-up posila outer master's coreId + detail's
# coreCode/coreLabel).
import os
import json
import psycopg2
from datetime import datetime


MARTI_AI_USER_ID = 2
MARTI_AI_USER_TEXT = 'Marti-AI'


def main():
    print("=" * 70)
    print("✨ Vytvořit edit jádro — Krok G++: defensive + check + backfill")
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
        # ── Step 2.5 (NEW): Defensive context vs DB validation ─────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, label
            FROM fw.core
            WHERE id = %s
        """, (core_id,))
        db_core = cur.fetchone()
        cur.close()

        if not db_core:
            print(f"✗ KONTEXT INVALID: fw.core #{core_id} NEEXISTUJE v DB.")
            print(f"  Drop-up menu poslalo coreId, ktery odkazuje na neexistujici")
            print(f"  fw.core. Pravdepodobna pricina: stale grid render po DELETE,")
            print(f"  nebo nested detail bez vlastniho fw.core.")
            print()
            print(f"  Cesta vpred: hard reload gridu + zkusit znovu.")
            print("=" * 70)
            return

        db_id, db_code, db_label = db_core

        # Mismatch check: porovna jen pokud OBE strany maji non-NULL value
        mismatches = []
        if core_code and db_code and core_code != db_code:
            mismatches.append((
                'coreCode', core_code, db_code
            ))
        if core_label and db_label and core_label != db_label:
            mismatches.append((
                'coreLabel', core_label, db_label
            ))

        if mismatches:
            print(f"✗ KONTEXT MISMATCH: fw.core #{core_id} v DB nematchuje context.")
            print()
            for field_name, ctx_val, db_val in mismatches:
                print(f"  {field_name}:")
                print(f"    drop-up:  {ctx_val}")
                print(f"    DB:       {db_val}")
            print()
            print(f"  Pravdepodobna pricina:")
            print(f"  - Drop-up menu spusten z NESTED DETAIL gridu, ktery nema")
            print(f"    vlastni fw.core.")
            print(f"  - coreId odkazuje na OUTER MASTER grid's fw.core,")
            print(f"    ale coreCode/coreLabel jsou z nested detail context.")
            print()
            print(f"  Orchestrator NEMUZE pokracovat — chranil by inkonzistenci DB.")
            print()
            print(f"  Cesta vpred (Krok H — pozdejsi iterace):")
            print(f"  - Povysit nested na standalone prehled (fw.menu_node +")
            print(f"    fw.core + comp_def grid root) → bude mit vlastni coreId")
            print(f"    a drop-up bude posilat consistent context.")
            print("=" * 70)
            return

        # ✓ Context match — pokracujeme do chain
        if core_code or core_label:
            print(f"✓ Context match s fw.core #{core_id} (code='{db_code}', label='{db_label}')")
            print()

        cur = conn.cursor()

        # ── Step 3: fw.comp_def grid root ──────────────────────────────────
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
            print(f"⚠ Žádný fw.comp_def s core_id={core_id} + data_source_id NOT NULL.")
            print("=" * 70)
            return

        print(f"Grid root(s) pro fw.core #{core_id}:")
        for gr in grid_roots:
            gr_id, gr_name, gr_caption, gr_ds_id = gr
            print(f"  comp_def #{gr_id} | name={gr_name} | data_source_id={gr_ds_id}")
        print()

        primary_root = grid_roots[0]
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
            print(f"⚠ ORPHAN data_source_id={primary_ds_id}.")
            print("=" * 70)
            return

        ds_id, ds_code, ds_name, ds_status = ds_row
        print(f"Data source: fw.data_source #{ds_id}")
        print(f"  name:   {ds_name}")
        print(f"  status: {ds_status}")
        print()

        # ── Step 5: SELECT all ops (edit + insert) ─────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT id, operation_kind, variant_code, core_id, description
            FROM fw.data_source_op
            WHERE data_source_id = %s
              AND operation_kind IN ('edit', 'insert')
            ORDER BY operation_kind, id ASC
        """, (ds_id,))
        ops = cur.fetchall()
        cur.close()

        edit_op = next((op for op in ops if op[1] == 'edit'), None)
        insert_op = next((op for op in ops if op[1] == 'insert'), None)

        print(f"Existing ops pro data_source_id={ds_id}:")
        print(f"  edit:   {'#' + str(edit_op[0]) + ' (core_id=' + str(edit_op[3]) + ')' if edit_op else '✗ chybi'}")
        print(f"  insert: {'#' + str(insert_op[0]) + ' (core_id=' + str(insert_op[3]) + ')' if insert_op else '✗ chybi'}")
        print()

        # ─────────────────────────────────────────────────────────────────────
        # ROZCESTI — 4 paths
        # ─────────────────────────────────────────────────────────────────────
        if not edit_op and not insert_op:
            print("─" * 70)
            print(f"Status: EDIT JÁDRO NEEXISTUJE → AUTO-CREATE")
            print("─" * 70)
            print()
            create_edit_core_and_both_ops(conn, ds_id, ds_name, core_label)

        elif edit_op and not insert_op:
            print("─" * 70)
            print(f"Status: INSERT OP CHYBÍ → BACKFILL insert")
            print("─" * 70)
            print()
            if edit_op[3] is None:
                print(f"⚠ edit op #{edit_op[0]} ma core_id=NULL — nelze backfill insert.")
            else:
                backfill_op(conn, ds_id, 'insert', edit_op[3])

        elif insert_op and not edit_op:
            print("─" * 70)
            print(f"Status: EDIT OP CHYBÍ → BACKFILL edit")
            print("─" * 70)
            print()
            if insert_op[3] is None:
                print(f"⚠ insert op #{insert_op[0]} ma core_id=NULL — nelze backfill edit.")
            else:
                backfill_op(conn, ds_id, 'edit', insert_op[3])

        else:
            if edit_op[3] is not None and insert_op[3] is not None and edit_op[3] != insert_op[3]:
                print(f"⚠ WARNING: edit.core_id={edit_op[3]} != insert.core_id={insert_op[3]}")
                print(f"  Ops ukazuji na rozdilne fw.core. Marti by mel sjednotit.")
                print()
            check_existing_core(conn, edit_op)

    finally:
        conn.close()

    print()
    print("=" * 70)
    print("Krok G++ dokončen.")
    print("=" * 70)


def check_existing_core(conn, op):
    """Check fw.core existence for given op."""
    op_id, op_kind, _, op_core_id, _ = op

    print(f"Primary op (priorita 'edit' > 'insert'):")
    print(f"  op_id = {op_id}")
    print(f"  operation_kind = '{op_kind}'")
    print(f"  core_id = {op_core_id if op_core_id is not None else 'NULL'}")
    print()

    if op_core_id is None:
        print(f"⚠ Op #{op_id} NENÍ sparován s fw.core.")
        print(f"Status: SPÁROVÁNÍ CHYBÍ")
        return

    cur = conn.cursor()
    cur.execute("""
        SELECT id, code, label, description_user
        FROM fw.core
        WHERE id = %s
    """, (op_core_id,))
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
        print(f"Vazba: fw.data_source_op #{op_id} → fw.core #{c_id}")
        print(f"Status: PŘIPRAVENO — edit jádro lze otevřít (CRUD C button).")
    else:
        print(f"⚠ ORPHAN: op #{op_id} → core_id={op_core_id} NEEXISTUJE.")
        print(f"Status: ORPHAN")


def create_edit_core_and_both_ops(conn, ds_id, ds_name, core_label):
    """Path 1: atomic create new fw.core + 2x data_source_op."""
    new_core_label = f"Editace: {core_label or ds_name or 'neznámé'}"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    desc_text = (
        f"Auto-vytvořeno orchestrátorem 'vytvor_edit_jadro' {timestamp} "
        f"pro data_source #{ds_id} ({ds_name})."
    )

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fw.core (
                code, label, description_user,
                created_by_id, created_by_text,
                updated_by_id, updated_by_text
            ) VALUES (NULL, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            new_core_label, desc_text,
            MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
        ))
        new_core_id = cur.fetchone()[0]
        cur.close()
        print(f"  ✓ fw.core #{new_core_id} vytvořen | label='{new_core_label}'")

        op_ids = {}
        for op_kind in ('edit', 'insert'):
            op_id = _insert_op(conn, ds_id, op_kind, new_core_id, auto_label='AUTO')
            op_ids[op_kind] = op_id

        conn.commit()
        print()
        print(f"  ✓ TRANSACTION COMMIT — atomic create.")
        print()
        print("─" * 70)
        print(f"Status: VYTVOŘENO — edit jádro #{new_core_id} připraveno")
        print(f"  op_edit #{op_ids['edit']} + op_insert #{op_ids['insert']}")
        print("─" * 70)

    except Exception as e:
        conn.rollback()
        print(f"  ✗ ROLLBACK — error: {type(e).__name__}: {e}")
        raise


def backfill_op(conn, ds_id, op_kind, existing_core_id):
    """Path 2/3: insert single missing op linked to existing core."""
    try:
        op_id = _insert_op(conn, ds_id, op_kind, existing_core_id, auto_label='BACKFILL')
        conn.commit()
        print()
        print(f"  ✓ TRANSACTION COMMIT — backfill atomic.")
        print()
        print("─" * 70)
        print(f"Status: BACKFILL DOPLNĚNO — op_{op_kind} #{op_id}")
        print(f"  Linked to existing fw.core #{existing_core_id}")
        print("─" * 70)

    except Exception as e:
        conn.rollback()
        print(f"  ✗ ROLLBACK — error: {type(e).__name__}: {e}")
        raise


def _insert_op(conn, ds_id, op_kind, core_id, auto_label='AUTO'):
    """Helper: insert single data_source_op."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fw.data_source_op (
            data_source_id, operation_kind, core_id, data_set_id,
            variant_code, is_default, sort_order, description
        ) VALUES (
            %s, %s, %s, NULL, 'default', TRUE, 0, %s
        )
        RETURNING id
    """, (
        ds_id, op_kind, core_id,
        f"[{auto_label}] Auto-vytvořeno orchestrátorem (kind={op_kind})",
    ))
    new_op_id = cur.fetchone()[0]
    cur.close()
    print(f"  ✓ fw.data_source_op #{new_op_id} | kind={op_kind} | "
          f"data_source_id={ds_id} → core_id={core_id}")
    return new_op_id


try:
    main()
except Exception as e:
    import traceback
    print("=" * 70)
    print(f"ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 70)
    print(traceback.format_exc())
$orch$,
    description = 'Krok G++ defensive: Step 2.5 — porovna context coreCode/coreLabel proti DB fw.core[coreId].code/label. Pokud mismatch (typicky nested detail context posilajici outer master coreId) → error message + no destructive work. Plus Krok G+ paths 1-4 (CREATE/BACKFILL/CHECK).',
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
