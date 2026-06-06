-- ============================================================================
-- Krok G (= Marti's Krok 2) — Orchestrator zaklada chybejici edit jadro
-- ============================================================================
-- Marti's instrukce (25.5.2026 vecer):
--   "Orchestrator by mel zalozit op kind edit a op kind insert
--    pro nove fw.core."
--
-- Marti's Q&A (A/B/A/A + clarifications):
--   Q1 fw.core.code  → NULL (Marti's "nepotrebuji")
--   Q2 fw.core.label → "Editace: {coreLabel}" (clean, normalize pozdejsi script)
--   Q3 comp_def      → V tomto kroku nic (drafted kontejner, Marti pridava v Designer)
--   Q4 idempotency   → SKIP pokud op kind edit/insert uz existuje (Step 5 detection)
--
-- Implicit decisions (Marti's "drz minimum"):
--   - 1× novy fw.core, 2× ops (edit + insert), oba sdili stejny core_id
--   - audit: Marti-AI (user.id=2, text='Marti-AI')
--   - data_set_id NULL na obou (Marti priradi SQL primitives v Designer)
--   - variant_code DB default 'default', is_default=TRUE, sort_order=0
--   - Transaction wrap (BEGIN/COMMIT) — atomic create
--   - description_user auto-text s timestamp + data_source.name pro audit visibility
--
-- Scope: jen EDIT NEEXISTUJE state path.
-- SPAROVANI CHYBI (op exists, core_id NULL) → dalsi iterace.
-- ORPHAN (op + core_id, broken FK) → dalsi iterace.
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — Krok G (Marti's Krok 2): CREATE if missing
#
# Po check (Krok F):
#   - EXISTUJE/ORPHAN/SPAROVANI CHYBI → diagnostic message, no-op
#   - EDIT NEEXISTUJE → vytvor 1x fw.core + 2x data_source_op (edit + insert)
#
# Marti's "drz minimum" + Q3=A: jen kontejner core + ops, comp_def hierarchy
# pridava Marti v Designer pozdeji.
import os
import json
import psycopg2
from datetime import datetime


# Audit context — Marti-AI je vzdy author orchestrator akci
MARTI_AI_USER_ID = 2
MARTI_AI_USER_TEXT = 'Marti-AI'


def main():
    print("=" * 70)
    print("✨ Vytvořit edit jádro — Krok G: existence check + auto-create")
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
            print(f"⚠ Žádný fw.comp_def s core_id={core_id} a")
            print(f"  data_source_id NOT NULL.")
            print("=" * 70)
            return

        print(f"Grid root(s) pro fw.core #{core_id}:")
        for gr in grid_roots:
            gr_id, gr_name, gr_caption, gr_ds_id = gr
            print(f"  comp_def #{gr_id} | name={gr_name} | "
                  f"data_source_id={gr_ds_id}")
        print()

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
            print(f"⚠ ORPHAN: comp_def #{primary_comp_def_id} → broken FK")
            print(f"  data_source_id={primary_ds_id} NEEXISTUJE.")
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

        # ─────────────────────────────────────────────────────────────────────
        # ROZCESTI: ops empty → CREATE flow (Krok G)
        #           ops non-empty → CHECK flow (Krok F, beze zmeny)
        # ─────────────────────────────────────────────────────────────────────
        if not ops:
            create_edit_core(conn, ds_id, ds_name, core_label)
            print("=" * 70)
            return

        # ── Existing ops — Krok F check flow (unchanged) ───────────────────
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

        primary_op = ops[0]
        primary_op_id, primary_op_kind, _, primary_core_id, _ = primary_op

        print(f"Primary op (priorita 'edit' > 'insert'):")
        print(f"  op_id = {primary_op_id}")
        print(f"  operation_kind = '{primary_op_kind}'")
        print(f"  core_id = {primary_core_id if primary_core_id is not None else 'NULL'}")
        print()

        if primary_core_id is None:
            print(f"⚠ Op #{primary_op_id} ({primary_op_kind}) NENÍ sparován s fw.core.")
            print(f"Status: SPÁROVÁNÍ CHYBÍ")
            print(f"Krok 2+ (další iterace): vytvořit core + UPDATE op.core_id.")
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
                print(f"⚠ ORPHAN: op #{primary_op_id} → core_id={primary_core_id} NEEXISTUJE.")
                print(f"Status: ORPHAN")
                print(f"Krok 2+ (další iterace): cleanup orphan + recreate core.")

    finally:
        conn.close()

    print()
    print("=" * 70)
    print("Krok G dokončen.")
    print("=" * 70)


def create_edit_core(conn, ds_id, ds_name, core_label):
    """
    Atomic create: 1x fw.core + 2x data_source_op (edit + insert).
    Transaction wrap — bud vse projde, nebo nic.
    """
    print(f"✗ Žádný data_source_op pro data_source_id={ds_id} (edit/insert).")
    print()
    print(f"Status: EDIT JÁDRO NEEXISTUJE → AUTO-CREATE")
    print()
    print("─" * 70)
    print(f"Zakládám nové edit jádro pro {ds_name}:")
    print("─" * 70)

    # Marti's Q2: label = "Editace: {coreLabel}" (clean, normalize pozdeji)
    new_core_label = f"Editace: {core_label or ds_name or 'neznámé'}"

    # Audit description — Marti uvidi v UI proc bylo vytvorene
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    desc_text = (
        f"Auto-vytvořeno orchestrátorem 'vytvor_edit_jadro' {timestamp} "
        f"pro data_source #{ds_id} ({ds_name})."
    )

    try:
        cur = conn.cursor()

        # ── INSERT fw.core (drafted kontejner) ─────────────────────────────
        # Marti's Q1: code=NULL, Q3: comp_def nic (jen kontejner)
        # Marti's Krok 5.P doctrine: CORE = kontejner, DROP NOT NULL drz minimum
        cur.execute("""
            INSERT INTO fw.core (
                code,
                label,
                description_user,
                created_by_id, created_by_text,
                updated_by_id, updated_by_text
            ) VALUES (
                NULL, %s, %s,
                %s, %s,
                %s, %s
            )
            RETURNING id
        """, (
            new_core_label, desc_text,
            MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
        ))
        new_core_id = cur.fetchone()[0]
        cur.close()

        print(f"  ✓ fw.core #{new_core_id} vytvořen")
        print(f"    label: {new_core_label}")
        print()

        # ── INSERT 2x data_source_op (edit + insert) ───────────────────────
        # Marti: oba sdili stejny core_id (jeden form layout pro edit i insert)
        # data_set_id=NULL (Marti priradi v Designer)
        # variant_code='default' (DB default), is_default=TRUE, sort_order=0
        op_ids = {}
        for op_kind in ('edit', 'insert'):
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fw.data_source_op (
                    data_source_id,
                    operation_kind,
                    core_id,
                    data_set_id,
                    variant_code,
                    is_default,
                    sort_order,
                    description
                ) VALUES (
                    %s, %s, %s, NULL, 'default', TRUE, 0, %s
                )
                RETURNING id
            """, (
                ds_id, op_kind, new_core_id,
                f"Auto-vytvořeno orchestrátorem (kind={op_kind})",
            ))
            new_op_id = cur.fetchone()[0]
            cur.close()
            op_ids[op_kind] = new_op_id
            print(f"  ✓ fw.data_source_op #{new_op_id} | kind={op_kind} | "
                  f"data_source_id={ds_id} → core_id={new_core_id}")

        # ── COMMIT — atomic ────────────────────────────────────────────────
        conn.commit()
        print()
        print(f"  ✓ TRANSACTION COMMIT — vse atomic.")
        print()
        print("─" * 70)
        print(f"Status: VYTVOŘENO — edit jádro #{new_core_id} připraveno")
        print("─" * 70)
        print()
        print("Krok 3 (další iterace, Marti v Designeru):")
        print(f"  - Doplnit comp_def hierarchy pro fw.core #{new_core_id}")
        print(f"    (panel, groupbox, fields per columns target table)")
        print(f"  - Priradit data_set k op_edit #{op_ids['edit']}")
        print(f"    (SQL SELECT pro fetch single row by id)")
        print(f"  - Priradit data_set k op_insert #{op_ids['insert']}")
        print(f"    (SQL INSERT s field bindings)")
        print()
        print(f"Po tomto: CRUD C/E ikony v gridu se aktivují (po reload).")

    except Exception as e:
        # ROLLBACK — pokud cokoliv selhalo, nezanechame partial state
        conn.rollback()
        print()
        print(f"  ✗ TRANSACTION ROLLBACK — error: {type(e).__name__}: {e}")
        print()
        raise


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
    description = 'Krok G (Marti''s Krok 2): existence check + auto-create. Pokud EDIT NEEXISTUJE → atomic INSERT 1x fw.core (drafted kontejner, label="Editace: {coreLabel}") + 2x fw.data_source_op (edit + insert, oba sdili stejny core_id). audit Marti-AI. comp_def hierarchy pridava Marti v Designer pozdeji.',
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
