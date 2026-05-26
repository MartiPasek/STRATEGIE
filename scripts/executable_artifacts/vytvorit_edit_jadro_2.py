# ============================================================================
# fw.executable_artifact orchestrator
# ID: 2
# CODE: vytvorit_edit_jadro_2
# ============================================================================
"""Krok H+5 — Auto-generate comp_def hierarchy pro drafted edit core.

Spustano z DesignFwForm empty_container dialog "Chces vygenerovat root
komponenty?". Po success: drafted core dostane form root + main panel +
per-column input fields (per target table schema introspekce).

Input (SANDBOX_CONTEXT env var):
  {coreId: int}  — fw.core.id v drafted state (comp_def_root_count=0)

Output (stdout):
  - Resolve chain: core → data_source_op → data_source → data_set → SQL
    parse → target table (schema, table)
  - Introspect: information_schema.columns pro target table
  - Skip system columns (id, created_at, audit fields)
  - INSERT atomic:
      1. comp_def root (type='form', core_id=coreId)
      2. comp_def main panel (type='panel', parent_comp_def_id=root.id,
         region_slot='main')
      3. per column INSERT input (type='edit', parent=main, name=col,
         caption=col, sort_order=position*10)
  - DesignFwForm renderuje hardcoded OK/Storno footer (Krok 5.P-1) — no
    footer panel/buttons generated zde.

Marti's doctrine (26.5.2026 vecer):
  - "git je truth, DB je cache" (file → DB auto-sync v sandbox endpoint)
  - "ID je svaty" (PK is stable, code mutable)
  - "drz minimum" (jen form + panel + inputs, footer hardcoded v DesignFwForm)
"""
import os
import re
import json
import sys
import psycopg2
from datetime import datetime

# ============================================================================
# Configuration — actor identity + skip columns
# ============================================================================
MARTI_AI_USER_ID = 2
MARTI_AI_USER_TEXT = 'Marti-AI'

# System columns to skip when generating inputs (auto-managed by DB or audit)
SKIP_COLUMNS = frozenset({
    'id', 'created_at', 'updated_at',
    'created_by_id', 'created_by_text',
    'updated_by_id', 'updated_by_text',
    'version',
})

# Default field width (px) for generated inputs
DEFAULT_FIELD_WIDTH = 400


def main():
    print("=" * 70)
    print("🪄 Vytvořit edit jádro 2 — Krok H+5: comp_def hierarchy auto-gen")
    print("=" * 70)
    print()

    # ── Step 1: Parse context ──────────────────────────────────────────────
    ctx_raw = os.environ.get('SANDBOX_CONTEXT', '{}')
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        print(f"ERROR: SANDBOX_CONTEXT JSON parse failed: {e}")
        return

    core_id = ctx.get('coreId')
    print(f"Context: coreId = {core_id}")
    print()

    if core_id is None:
        print("⚠ coreId is None — orchestrator nedostal kontext.")
        print("=" * 70)
        return

    # ── Step 2: Connect ─────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        print("ERROR: STRATEGIE_DATA_DB_URL not set v sandbox env.")
        return

    conn = psycopg2.connect(db_url)
    try:
        # ── Step 3: Validate core existuje + je drafted ────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.code, c.label,
                   (SELECT COUNT(*) FROM fw.comp_def cd
                    WHERE cd.core_id = c.id
                      AND cd.parent_comp_def_id IS NULL) AS comp_def_root_count
            FROM fw.core c
            WHERE c.id = %s
        """, (core_id,))
        core_row = cur.fetchone()
        cur.close()

        if not core_row:
            print(f"✗ fw.core #{core_id} NEEXISTUJE v DB.")
            return

        c_id, c_code, c_label, c_root_count = core_row
        print(f"Core #{c_id}:")
        print(f"  code:  {c_code or '(NULL — drafted)'}")
        print(f"  label: {c_label or '(NULL)'}")
        print(f"  comp_def root count: {c_root_count}")
        print()

        if c_root_count > 0:
            print(f"⚠ Core #{c_id} JIZ MA root comp_def ({c_root_count}). "
                  f"Skip — neni drafted.")
            return

        # ── Step 4: Find linked data_source via data_source_op ─────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT op.id, op.operation_kind, op.data_source_id, op.data_set_id,
                   ds.name AS ds_name,
                   dset.sql_text
            FROM fw.data_source_op op
            JOIN fw.data_source ds ON ds.id = op.data_source_id
            LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
            WHERE op.core_id = %s
              AND op.operation_kind IN ('edit', 'insert')
            ORDER BY
              CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END,
              op.id ASC
            LIMIT 1
        """, (core_id,))
        op_row = cur.fetchone()
        cur.close()

        if not op_row:
            print(f"✗ Žádný fw.data_source_op s core_id={core_id} "
                  f"(kind IN edit/insert).")
            print(f"  Spustil jsi vytvor_edit_jadro nejdriv? (Krok F/G)")
            return

        op_id, op_kind, ds_id, ds_set_id, ds_name, sql_text = op_row
        print(f"Linked op:")
        print(f"  op_id:           {op_id} (kind={op_kind})")
        print(f"  data_source_id:  {ds_id} ({ds_name})")
        print(f"  data_set_id:     {ds_set_id or '(NULL — Krok 5.N-2 v2 path?)'}")
        print()

        # ── Step 5: Resolve target table (SQL parse) ───────────────────────
        target_schema = None
        target_table = None

        if sql_text:
            # Krok 5.N-2 path — parse FROM z linked data_set.sql_text
            match = re.search(
                r"\bFROM\s+([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)",
                sql_text, re.IGNORECASE,
            )
            if match:
                target_schema = match.group(1).lower()
                target_table = match.group(2).lower()
                print(f"Target table (z data_set.sql_text):")
                print(f"  {target_schema}.{target_table}")
                print()
            else:
                print(f"⚠ Nelze parse FROM z sql_text (CTE? subquery? composite?).")
        else:
            # Krok 5.N-2 v2 path — fallback resolve via op.data_set_id null,
            # SQL parse z fw.data_set linked to data_source's default
            # 'select' op (mirror _resolve_entity_config_from_db).
            print(f"⚠ op.data_set_id is NULL. Fallback: lookup default 'select' "
                  f"op z data_source #{ds_id}.")
            cur = conn.cursor()
            cur.execute("""
                SELECT dset.sql_text
                FROM fw.data_source_op op
                JOIN fw.data_set dset ON dset.id = op.data_set_id
                WHERE op.data_source_id = %s
                  AND op.operation_kind = 'select'
                ORDER BY op.is_default DESC NULLS LAST, op.id ASC
                LIMIT 1
            """, (ds_id,))
            select_row = cur.fetchone()
            cur.close()

            if select_row and select_row[0]:
                match = re.search(
                    r"\bFROM\s+([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)",
                    select_row[0], re.IGNORECASE,
                )
                if match:
                    target_schema = match.group(1).lower()
                    target_table = match.group(2).lower()
                    print(f"Target table (z default 'select' op):")
                    print(f"  {target_schema}.{target_table}")
                    print()

        if not (target_schema and target_table):
            print(f"✗ Nelze resolve target table pro core #{core_id}.")
            print(f"  Pravdepodobna pricina: data_set sql_text neobsahuje "
                  f"jasny FROM clause.")
            return

        # ── Step 6: Introspect target table columns ─────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type, is_nullable,
                   character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (target_schema, target_table))
        columns = cur.fetchall()
        cur.close()

        if not columns:
            print(f"✗ Target table {target_schema}.{target_table} neexistuje "
                  f"nebo nema sloupce.")
            return

        # Filter — skip system columns
        user_columns = [
            c for c in columns if c[0] not in SKIP_COLUMNS
        ]
        print(f"Target sloupce: {len(columns)} total, "
              f"{len(user_columns)} user-facing (po skip system)")
        for col_name, col_type, col_nullable, col_maxlen in user_columns:
            null_mark = 'NULL' if col_nullable == 'YES' else 'NOT NULL'
            len_mark = f' ({col_maxlen})' if col_maxlen else ''
            print(f"  - {col_name}: {col_type}{len_mark} {null_mark}")
        print()

        # ── Step 7: Resolve comp_type IDs + default_props ──────────────────
        # Phase 38.4 Krok H+5+ (26.5.2026 odp., Marti's "respektovat default
        # parametry"): fw.comp_type.default_props JSONB drzi per-type defaults
        # (layout + default_caption). Pri INSERT noveho comp_def musime tyto
        # defaults pouzit jako baseline, structural overrides aplikujeme jen
        # tam kde to vyzaduje role komponenty (main panel align=client).
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, default_props
            FROM fw.comp_type
            WHERE code IN ('form', 'panel', 'edit', 'input')
        """)
        ct_rows = cur.fetchall()
        cur.close()
        ct_map = {row[1]: row[0] for row in ct_rows}
        # defaults_map[code] = {layout: {...}, default_caption: "..."}
        defaults_map = {row[1]: (row[2] or {}) for row in ct_rows}

        # Required types pro hierarchy
        form_type_id = ct_map.get('form')
        panel_type_id = ct_map.get('panel')
        # Prefer 'edit' (Centrala 1 compat); fallback 'input' (modern)
        input_type_id = ct_map.get('edit') or ct_map.get('input')
        # Code pro defaults lookup (musi sedet s pouzitym type_id)
        input_code = 'edit' if ct_map.get('edit') else 'input'

        if not form_type_id:
            print(f"✗ comp_type 'form' nenalezen v fw.comp_type.")
            return
        if not panel_type_id:
            print(f"✗ comp_type 'panel' nenalezen v fw.comp_type.")
            return
        if not input_type_id:
            print(f"✗ comp_type 'edit' ani 'input' nenalezen v fw.comp_type.")
            return

        print(f"comp_type IDs:")
        print(f"  form:  {form_type_id}")
        print(f"  panel: {panel_type_id}")
        print(f"  input: {input_type_id} (code={input_code})")
        print()

        # Helper — merge per-type defaults.layout + per-instance structural
        # overrides. Defaults FIRST (Marti's "respektovat default parametry"),
        # structural overrides win na klicovem konfliktu (napr. main panel
        # align=client je strukturalni, ne uzivatelska volba).
        def _merge_layout(type_code, structural_overrides=None):
            base = dict((defaults_map.get(type_code) or {}).get('layout') or {})
            if structural_overrides:
                base.update(structural_overrides)
            return base

        # Helper — default_caption fallback chain (per-instance > per-type
        # default_caption > hardcoded fallback).
        def _resolved_caption(type_code, per_instance, hardcoded_fallback):
            if per_instance:
                return per_instance
            return (defaults_map.get(type_code) or {}).get('default_caption') \
                   or hardcoded_fallback

        # Print defaults summary pro audit (Marti vidi co script aplikuje)
        print("Defaults aplikovane z fw.comp_type.default_props:")
        for _code in ('form', 'panel', input_code):
            _dp = defaults_map.get(_code) or {}
            _lay = _dp.get('layout') or {}
            _cap = _dp.get('default_caption') or '(none)'
            print(f"  {_code:5s}: layout={json.dumps(_lay)}  default_caption={_cap}")
        print()

        # ── Step 8: INSERT atomic hierarchy ────────────────────────────────
        print("─" * 70)
        print(f"INSERT atomic — form root + main panel + {len(user_columns)} inputs")
        print("─" * 70)
        print()

        try:
            # 8a — form root
            # NOT NULL columns (per Marti's audit 26.5.):
            #   is_active, created_by_text, updated_by_text → must provide
            #   created_at, updated_at → DB defaults handle
            # Krok H+5 fix #3 (26.5. ~13:15, "data nezobrazene" Marti's catch):
            #   region_slot='main' + data_source_id=ds_id na form root →
            #   backend _resolve_entity_config_from_db matchne form root
            #   (JOIN cd.core_id=c.id AND cd.region_slot='main' AND
            #   cd.data_source_id NOT NULL) → resolve target table →
            #   load data row → inputs zobrazi values.
            # Krok H+5+ (26.5. odp., Marti's "respektovat default parametry"):
            #   layout + caption derived z fw.comp_type.default_props
            #   (defaults_map) — per-instance c_label wins na captionu,
            #   layout je pure defaults (form root nema strukturalni override).
            form_layout = _merge_layout('form')
            form_caption = _resolved_caption('form', c_label, 'Editace záznamu')
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fw.comp_def (
                    type_id, core_id, parent_comp_def_id,
                    name, caption, layout, sort_order, region_slot,
                    data_source_id,
                    is_active,
                    created_by_id, created_by_text,
                    updated_by_id, updated_by_text
                ) VALUES (
                    %s, %s, NULL, %s, %s, %s::jsonb, 0, %s,
                    %s,
                    TRUE,
                    %s, %s, %s, %s
                )
                RETURNING id
            """, (
                form_type_id, core_id,
                'form_root',
                form_caption,
                json.dumps(form_layout),
                'main',  # region_slot
                ds_id,   # data_source_id
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            ))
            root_id = cur.fetchone()[0]
            cur.close()
            print(f"  ✓ comp_def #{root_id} (form root, ds_id={ds_id}, "
                  f"caption='{form_caption}', layout={json.dumps(form_layout)})")

            # 8b — main panel
            # Krok H+5+: defaults FIRST, pak structural override align=client
            # (main panel MUSI fillovat root prostor — nezavisi na user
            # preferenci v default_props). Caption: defaults.default_caption
            # fallback, ale pro main panel chceme zustat prazdny (panel je
            # neviditelny container, caption by se zobrazil jako redundant).
            panel_layout = _merge_layout('panel', {"align": "client"})
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fw.comp_def (
                    type_id, core_id, parent_comp_def_id,
                    name, caption, layout, sort_order, region_slot,
                    is_active,
                    created_by_id, created_by_text,
                    updated_by_id, updated_by_text
                ) VALUES (
                    %s, NULL, %s, %s, %s, %s::jsonb, 0, %s,
                    TRUE,
                    %s, %s, %s, %s
                )
                RETURNING id
            """, (
                panel_type_id, root_id,
                'main_panel', '',
                json.dumps(panel_layout),
                'main',
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            ))
            main_panel_id = cur.fetchone()[0]
            cur.close()
            print(f"  ✓ comp_def #{main_panel_id} (main panel, slot=main, "
                  f"layout={json.dumps(panel_layout)})")

            # 8c — per-column inputs
            # Krok H+5+: input layout FIRST z defaults_map[input_code].layout,
            # fallback DEFAULT_FIELD_WIDTH=400 pokud defaults neobsahuji width
            # ani min_width (zachovava zpetnou kompatibilitu).
            input_defaults_layout = (defaults_map.get(input_code) or {}).get('layout') or {}
            input_ids = []
            for idx, (col_name, col_type, col_nullable, col_maxlen) in enumerate(user_columns):
                # Caption — friendly version of column name (first letter upper)
                caption = col_name.replace('_', ' ').capitalize()
                # Layout — defaults FIRST + fallback min_width
                input_layout = dict(input_defaults_layout)
                if 'width' not in input_layout and 'min_width' not in input_layout:
                    input_layout['min_width'] = DEFAULT_FIELD_WIDTH
                layout_json = json.dumps(input_layout)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id,
                        name, caption, layout, sort_order, region_slot,
                        is_active,
                        created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (
                        %s, NULL, %s, %s, %s, %s::jsonb, %s, NULL,
                        TRUE,
                        %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    input_type_id, main_panel_id,
                    col_name, caption, layout_json,
                    (idx + 1) * 10,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                inp_id = cur.fetchone()[0]
                cur.close()
                input_ids.append((inp_id, col_name))

            print(f"  ✓ {len(input_ids)} input fields v main panel:")
            for inp_id, col_name in input_ids:
                print(f"    - comp_def #{inp_id} ({col_name})")

            conn.commit()
            print()
            print(f"  ✓ TRANSACTION COMMIT — atomic.")
            print()

            print("─" * 70)
            print(f"Status: VYGENEROVÁNO — comp_def hierarchy pro core #{core_id}")
            print(f"  Root #{root_id} → main panel #{main_panel_id} "
                  f"→ {len(input_ids)} inputs")
            print(f"  Hard reload + open form → vidíš plný editovatelný UI.")
            print("─" * 70)

        except Exception as e:
            conn.rollback()
            print(f"  ✗ ROLLBACK — error: {type(e).__name__}: {e}")
            raise

    finally:
        conn.close()

    print()
    print("=" * 70)
    print("Krok H+5 dokončen.")
    print("=" * 70)


try:
    main()
except Exception as e:
    import traceback
    print("=" * 70)
    print(f"ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 70)
    print(traceback.format_exc())
    # Krok H+5 fix #2 (26.5.2026 ~13:00, Marti's "ok=True ale nic v DB"
    # diagnostika): explicit exit code 1 → sandbox vrátí ok=False → frontend
    # ukáže error toast místo silent success.
    sys.exit(1)
