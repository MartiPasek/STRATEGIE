# ============================================================================
# fw.executable_artifact orchestrator
# ID: 2
# CODE: vytvorit_edit_jadro_2
# ============================================================================
"""Auto-generate comp_def hierarchy pro drafted edit core.

Spuštěno z DesignFwForm empty-core dialogu „Chceš vygenerovat root komponenty?".
Po success: drafted core dostane form root + main panel + per-column inputs
(per target table schema introspekce). Footer (OK/Storno) renderuje DesignFwForm
hardcoded — zde se negeneruje.

Vstup (SANDBOX_CONTEXT env var, JSON):
  {
    "coreId": int,          # POVINNÉ — fw.core.id v drafted state (root_count=0)
    "force": bool optional  # když true, smaže existující root hierarchii a re-gen
  }

Resolve chain:
  core → fw.data_source_op (edit/insert) → data_source → (edit op nemá data_set →
  fallback default 'select' op) → data_set.sql_text → parse FROM schema.table →
  db_type (PG / MSSQL) → introspekce sloupců → INSERT form/panel/inputs.

Doctrine (Marti):
  - „git je truth, DB je cache" (file → DB auto-sync v sandbox endpointu)
  - „ID je svatý" (PK stabilní, code mutable)
  - Žádný tichý ok=True na chybě — každý fail = sys.exit(1) (ok=False, viditelné).

Hardening 1.6.2026 (Marti „ošetřit po všech stránkách"):
  - _fail() na všech chybových cestách → exit 1 (dřív tichý return → ok=True).
  - Robustní FROM parse: strip komentáře, [brackets] (MSSQL), "quoted", aliasy.
  - MSSQL introspekce: explicitní chyba když MCP None / prázdno (dřív tiché []).
  - Type→comp_type mapping: date/datetime→date, bool/bit→checkbox, else→edit
    (s fallbackem na edit, když daný comp_type neexistuje).
  - Idempotence: root existuje → skip (exit 0), nebo force=true → smazat + re-gen.
  - Prominentní finální status do stdout (backend ho loguje jako stdout_tail).
"""
import os
import re
import json
import sys
import psycopg2

# ============================================================================
# Konfigurace
# ============================================================================
MARTI_AI_USER_ID = 2
MARTI_AI_USER_TEXT = 'Marti-AI'
DEFAULT_FIELD_WIDTH = 400

# Sloupce přeskočené při generování inputů (auto-managed DB / audit).
# PG (lowercase) + Centrála 1 / MSSQL (PascalCase, match přes .lower()).
SKIP_COLUMNS = frozenset({
    'id', 'created_at', 'updated_at',
    'created_by_id', 'created_by_text',
    'updated_by_id', 'updated_by_text',
    'version',
    'datporizeni', 'datzmeny', 'autor', 'zmenil',
})


# ============================================================================
# Helpers — fail/skip (žádný tichý ok=True)
# ============================================================================
def _fail(msg):
    """Vytiskni důvod + exit 1 → sandbox vrátí ok=False (viditelný error)."""
    print()
    print("=" * 70)
    print(f"✗ FAIL: {msg}")
    print("=" * 70)
    sys.exit(1)


def _skip(msg):
    """Legitimní skip (ne chyba) → exit 0, ok=True."""
    print()
    print("=" * 70)
    print(f"○ SKIP: {msg}")
    print("=" * 70)
    sys.exit(0)


def _parse_from_table(sql):
    """Robustní parse prvního 'FROM schema.table'.

    Zvládá: -- line komentáře, /* block */ komentáře, [brackets] (MSSQL),
    "quoted" identifikátory, whitespace kolem tečky, table aliasy (ignoruje).
    Vrací (schema, table) nebo (None, None).
    """
    if not sql:
        return (None, None)
    s = re.sub(r'--[^\n]*', ' ', sql)            # line komentáře
    s = re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)  # block komentáře
    m = re.search(
        r'\bFROM\s+'
        r'[\[\"]?([A-Za-z_][A-Za-z0-9_]*)[\]\"]?'  # schema
        r'\s*\.\s*'
        r'[\[\"]?([A-Za-z_][A-Za-z0-9_]*)[\]\"]?',  # table
        s, re.IGNORECASE,
    )
    if m:
        return (m.group(1), m.group(2))
    return (None, None)


def _introspect_mssql_via_mcp(schema_name, table_name, db_name='DB_EC'):
    """MSSQL introspekce přes MCP eurosoft_strategie_describe_table.

    Vrací list tuples (column_name, data_type, is_nullable, max_length) — stejný
    shape jako PG information_schema.columns. Při chybě vrací (None, error_msg);
    při úspěchu (list, None). Caller dělá _fail při error.
    """
    try:
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    except Exception as e:
        return (None, f"import get_eurosoft_mcp_client selhal: {e}")

    mcp_client = get_eurosoft_mcp_client()
    if mcp_client is None:
        return (None, "MCP client je None (settings.eurosoft_mcp_enabled=False? MCP server down?)")

    try:
        result_json = mcp_client.call_tool_sync(
            "eurosoft_strategie_describe_table",
            {"schema": schema_name, "table": table_name, "db_name": db_name},
            conversation_id=None,
        )
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
    except Exception as e:
        return (None, f"MCP describe_table call failed: {e}")

    if not isinstance(result, dict) or result.get("ok", True) is not True:
        err = result.get("error") if isinstance(result, dict) else str(result)
        return (None, f"MCP describe_table vrátil error: {err}")

    cols = result.get("columns", []) or []
    normalized = []
    for c in cols:
        if not isinstance(c, dict):
            continue
        col_name = c.get("name") or c.get("column_name") or ""
        data_type = c.get("data_type") or c.get("type") or "varchar"
        is_nullable_raw = c.get("is_nullable")
        if isinstance(is_nullable_raw, bool):
            is_nullable = "YES" if is_nullable_raw else "NO"
        else:
            is_nullable = str(is_nullable_raw or "YES").upper()
        max_length = c.get("max_length") or c.get("character_maximum_length")
        if isinstance(max_length, int) and max_length < 0:
            max_length = None
        normalized.append((col_name, data_type, is_nullable, max_length))
    return (normalized, None)


def _comp_type_for_column(data_type, ct_map, default_input_id):
    """Map SQL data_type → comp_type id. date/time→date, bool/bit→checkbox,
    else→edit/input. Fallback na default_input_id když daný comp_type chybí."""
    dt = (data_type or '').lower()
    if ('date' in dt) or ('time' in dt):
        return ct_map.get('date') or default_input_id
    if ('bool' in dt) or (dt == 'bit'):
        return ct_map.get('checkbox') or default_input_id
    return default_input_id


# ============================================================================
# Main
# ============================================================================
def main():
    print("=" * 70)
    print("🪄 vytvorit_edit_jadro_2 — auto-gen comp_def hierarchy (edit core)")
    print("=" * 70)
    print()

    # ── Step 1: Parse context ───────────────────────────────────────────────
    ctx_raw = os.environ.get('SANDBOX_CONTEXT', '{}')
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        _fail(f"SANDBOX_CONTEXT JSON parse selhal: {e} (raw={ctx_raw!r})")

    if not isinstance(ctx, dict):
        _fail(f"SANDBOX_CONTEXT není dict: {ctx_raw!r}")

    core_id = ctx.get('coreId')
    force = bool(ctx.get('force'))
    print(f"Context: coreId={core_id}, force={force}")
    print()

    if core_id is None:
        _fail("coreId chybí v SANDBOX_CONTEXT — orchestrator nedostal kontext "
              "(frontend musí poslat {coreId} v POST body).")

    # ── Step 2: Connect ──────────────────────────────────────────────────────
    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        _fail("STRATEGIE_DATA_DB_URL není v sandbox env nastaveno.")

    conn = psycopg2.connect(db_url)
    try:
        # ── Step 3: Validate core + drafted/force ───────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.code, c.label,
                   (SELECT COUNT(*) FROM fw.comp_def cd
                     WHERE cd.core_id = c.id
                       AND cd.parent_comp_def_id IS NULL) AS root_count
            FROM fw.core c
            WHERE c.id = %s
        """, (core_id,))
        core_row = cur.fetchone()
        cur.close()

        if not core_row:
            _fail(f"fw.core #{core_id} neexistuje v DB.")

        c_id, c_code, c_label, c_root_count = core_row
        print(f"Core #{c_id}: code={c_code or '(NULL drafted)'}, "
              f"label={c_label or '(NULL)'}, root_count={c_root_count}")

        if c_root_count > 0:
            if not force:
                _skip(f"Core #{c_id} už má {c_root_count} root komponent — není "
                      f"drafted. Pro re-generaci pošli {{\"force\": true}}.")
            # force=true → smaž celou comp_def hierarchii tohoto core
            print(f"  force=true → mažu existující hierarchii core #{c_id} …")
            cur = conn.cursor()
            cur.execute("""
                WITH RECURSIVE tree AS (
                    SELECT id FROM fw.comp_def WHERE core_id = %s
                    UNION ALL
                    SELECT ch.id FROM fw.comp_def ch
                    JOIN tree t ON ch.parent_comp_def_id = t.id
                )
                DELETE FROM fw.comp_def WHERE id IN (SELECT id FROM tree)
            """, (core_id,))
            deleted = cur.rowcount
            cur.close()
            print(f"  smazáno {deleted} comp_def (re-gen).")
        print()

        # ── Step 4: Linked data_source via data_source_op (edit/insert) ─────
        cur = conn.cursor()
        cur.execute("""
            SELECT op.id, op.operation_kind, op.data_source_id, op.data_set_id,
                   ds.name AS ds_name,
                   dset.sql_text,
                   dc.db_type
            FROM fw.data_source_op op
            JOIN fw.data_source ds ON ds.id = op.data_source_id
            LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
            LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
            WHERE op.core_id = %s
              AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """, (core_id,))
        op_row = cur.fetchone()
        cur.close()

        if not op_row:
            _fail(f"Žádný fw.data_source_op s core_id={core_id} (kind edit/insert). "
                  f"Edit core musí mít edit-op odkazující na sebe (op.core_id={core_id}).")

        op_id, op_kind, ds_id, ds_set_id, ds_name, sql_text, db_type = op_row
        print(f"Linked op #{op_id} (kind={op_kind}): data_source #{ds_id} "
              f"({ds_name}), data_set={ds_set_id or '(NULL)'}, "
              f"db_type={db_type or '(NULL → fallback)'}")
        print()

        # ── Step 5: Resolve target table (FROM parse) ───────────────────────
        target_schema, target_table = _parse_from_table(sql_text)
        if target_schema:
            print(f"Target table (z linked op data_set): {target_schema}.{target_table}")
        else:
            # Fallback — edit op typicky nemá data_set; vezmi default 'select'
            # op téhož data_source a parse jeho sql_text + adopt db_type.
            print("Linked op nemá parsovatelný sql_text → fallback na default "
                  "'select' op data_source.")
            cur = conn.cursor()
            cur.execute("""
                SELECT dset.sql_text, dc.db_type
                FROM fw.data_source_op op
                JOIN fw.data_set dset ON dset.id = op.data_set_id
                LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
                WHERE op.data_source_id = %s
                  AND op.operation_kind = 'select'
                ORDER BY op.is_default DESC NULLS LAST, op.id ASC
                LIMIT 1
            """, (ds_id,))
            select_row = cur.fetchone()
            cur.close()
            if select_row and select_row[0]:
                target_schema, target_table = _parse_from_table(select_row[0])
                if target_schema:
                    print(f"Target table (z 'select' op): {target_schema}.{target_table}")
                if not db_type:
                    db_type = select_row[1]
                    print(f"  db_type (z fallback select op): {db_type or '(NULL)'}")

        if not (target_schema and target_table):
            _fail(f"Nelze resolve target table pro core #{core_id}. "
                  f"data_set sql_text neobsahuje jasný 'FROM schema.table' "
                  f"(CTE/subquery/composite?). sql_text={ (sql_text or '')[:200]!r}")

        # ── Step 6: Introspekce sloupců (db_type dispatch) ──────────────────
        db_type_norm = (db_type or '').lower().strip()
        if db_type_norm == 'mssql':
            print(f"db_type=mssql → introspekce přes MCP describe_table "
                  f"({target_schema}.{target_table}).")
            columns, mcp_err = _introspect_mssql_via_mcp(target_schema, target_table)
            if mcp_err:
                _fail(f"MSSQL introspekce selhala: {mcp_err}. "
                      f"(MCP server EC-SERVER2 běží? eurosoft_mcp_enabled? "
                      f"existuje {target_schema}.{target_table} v DB_EC?)")
        else:
            print(f"db_type={db_type_norm or 'pg (default)'} → introspekce "
                  f"information_schema.columns.")
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (target_schema.lower(), target_table.lower()))
            columns = cur.fetchall()
            cur.close()

        if not columns:
            _fail(f"Target table {target_schema}.{target_table} nemá žádné sloupce "
                  f"(neexistuje? db_type={db_type_norm or 'pg'}).")

        user_columns = [c for c in columns if (c[0] or '').lower() not in SKIP_COLUMNS]
        print(f"Sloupce: {len(columns)} total, {len(user_columns)} user-facing "
              f"(po skip system).")
        for col_name, col_type, col_nullable, col_maxlen in user_columns:
            null_mark = 'NULL' if col_nullable == 'YES' else 'NOT NULL'
            len_mark = f' ({col_maxlen})' if col_maxlen else ''
            print(f"  - {col_name}: {col_type}{len_mark} {null_mark}")
        print()

        if not user_columns:
            _fail(f"Po skip system columns nezbyly žádné user sloupce "
                  f"({target_schema}.{target_table} má jen audit/PK sloupce). "
                  f"Form by neměl žádná editovatelná pole.")

        # ── Step 7: comp_type IDs + default_props ───────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, default_props
            FROM fw.comp_type
            WHERE code IN ('form', 'panel', 'edit', 'input', 'date', 'checkbox')
        """)
        ct_rows = cur.fetchall()
        cur.close()
        ct_map = {row[1]: row[0] for row in ct_rows}
        defaults_map = {row[1]: (row[2] or {}) for row in ct_rows}

        form_type_id = ct_map.get('form')
        panel_type_id = ct_map.get('panel')
        input_type_id = ct_map.get('edit') or ct_map.get('input')
        input_code = 'edit' if ct_map.get('edit') else 'input'

        if not form_type_id:
            _fail("comp_type 'form' nenalezen v fw.comp_type.")
        if not panel_type_id:
            _fail("comp_type 'panel' nenalezen v fw.comp_type.")
        if not input_type_id:
            _fail("comp_type 'edit' ani 'input' nenalezen v fw.comp_type.")

        print(f"comp_type IDs: form={form_type_id}, panel={panel_type_id}, "
              f"input={input_type_id} ({input_code}), "
              f"date={ct_map.get('date', '-')}, checkbox={ct_map.get('checkbox', '-')}")
        print()

        def _merge_layout(type_code, structural_overrides=None):
            base = dict((defaults_map.get(type_code) or {}).get('layout') or {})
            if structural_overrides:
                base.update(structural_overrides)
            return base

        def _resolved_caption(type_code, per_instance, hardcoded_fallback):
            if per_instance:
                return per_instance
            return (defaults_map.get(type_code) or {}).get('default_caption') \
                or hardcoded_fallback

        # ── Step 8: INSERT atomic hierarchy ─────────────────────────────────
        print("─" * 70)
        print(f"INSERT atomic — form root + main panel + {len(user_columns)} inputs")
        print("─" * 70)
        try:
            # 8a — form root (region_slot='main' + data_source_id → backend
            # _resolve_entity_config_from_db ho matchne pro load/save dat).
            form_layout = _merge_layout('form')
            form_caption = _resolved_caption('form', c_label, 'Editace záznamu')
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fw.comp_def (
                    type_id, core_id, parent_comp_def_id,
                    name, caption, layout, sort_order, region_slot, data_source_id,
                    is_active, created_by_id, created_by_text,
                    updated_by_id, updated_by_text
                ) VALUES (%s, %s, NULL, %s, %s, %s::jsonb, 0, %s, %s,
                          TRUE, %s, %s, %s, %s)
                RETURNING id
            """, (
                form_type_id, core_id, 'form_root', form_caption,
                json.dumps(form_layout), 'main', ds_id,
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            ))
            root_id = cur.fetchone()[0]
            cur.close()
            print(f"  ✓ form root #{root_id} (ds_id={ds_id}, caption='{form_caption}')")

            # 8b — main panel (align=client = strukturální override)
            panel_layout = _merge_layout('panel', {"align": "client"})
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fw.comp_def (
                    type_id, core_id, parent_comp_def_id,
                    name, caption, layout, sort_order, region_slot,
                    is_active, created_by_id, created_by_text,
                    updated_by_id, updated_by_text
                ) VALUES (%s, NULL, %s, %s, %s, %s::jsonb, 0, %s,
                          TRUE, %s, %s, %s, %s)
                RETURNING id
            """, (
                panel_type_id, root_id, 'main_panel', '',
                json.dumps(panel_layout), 'main',
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
            ))
            main_panel_id = cur.fetchone()[0]
            cur.close()
            print(f"  ✓ main panel #{main_panel_id} (align=client)")

            # 8c — per-column inputs (type dle data_type, name=col pro save binding)
            input_defaults_layout = (defaults_map.get(input_code) or {}).get('layout') or {}
            input_ids = []
            for idx, (col_name, col_type, col_nullable, col_maxlen) in enumerate(user_columns):
                caption = col_name.replace('_', ' ').capitalize()
                col_type_id = _comp_type_for_column(col_type, ct_map, input_type_id)
                input_layout = dict(input_defaults_layout)
                if 'width' not in input_layout and 'min_width' not in input_layout:
                    input_layout['min_width'] = DEFAULT_FIELD_WIDTH
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id,
                        name, caption, layout, sort_order, region_slot,
                        is_active, created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (%s, NULL, %s, %s, %s, %s::jsonb, %s, NULL,
                              TRUE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    col_type_id, main_panel_id, col_name, caption,
                    json.dumps(input_layout), (idx + 1) * 10,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                inp_id = cur.fetchone()[0]
                cur.close()
                input_ids.append((inp_id, col_name, col_type_id))

            print(f"  ✓ {len(input_ids)} inputů v main panelu:")
            for inp_id, col_name, col_type_id in input_ids:
                print(f"    - #{inp_id} {col_name} (type_id={col_type_id})")

            conn.commit()
            print()
            print("─" * 70)
            print(f"✓ HOTOVO — comp_def hierarchy pro core #{core_id} (COMMIT):")
            print(f"  form root #{root_id} → main panel #{main_panel_id} "
                  f"→ {len(input_ids)} inputů")
            print(f"  Hard reload + otevři form → plný editovatelný UI.")
            print("─" * 70)

        except Exception as e:
            conn.rollback()
            _fail(f"INSERT selhal (ROLLBACK): {type(e).__name__}: {e}")

    finally:
        conn.close()


try:
    main()
except SystemExit:
    raise  # _fail/_skip — propaguj exit code (1=fail, 0=skip)
except Exception as e:
    import traceback
    print("=" * 70)
    print(f"✗ ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 70)
    print(traceback.format_exc())
    sys.exit(1)
