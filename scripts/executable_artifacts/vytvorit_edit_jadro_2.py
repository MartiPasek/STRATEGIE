# ============================================================================
# fw.executable_artifact orchestrator
# ID: 2
# CODE: vytvorit_edit_jadro_2
# ============================================================================
"""Auto-generate comp_def hierarchy pro edit core — INKREMENTÁLNĚ.

Spuštěno z DesignFwForm empty-core dialogu „Chceš vygenerovat root komponenty?".

Marti spec (1.6.2026):
  Fáze 1 = vygenerovat KOMPONENTY:
    form → panel(align:top) + panel(align:client)
         → do CLIENT panelu základní `edit` komponenty, KRÁTKÉ délky,
           tolik kolik je FIELDŮ V DATASETU, každá napojená NÁZVEM fieldu.
  Save/binding řešíme až POTOM (ne tady).

  INKREMENTÁLNÍ (klíčové): skript jede opakovaně.
    - core prázdný  → vytvoří form + 2 panely + edit komponenty pro VŠECHNY fieldy
    - core už má komponenty → PŘIDÁ JEN NOVÉ fieldy (co v datasetu přibyly)
      k existujícím. Nesmaže, nezduplikuje, nepřeskočí celý běh.

Vstup (SANDBOX_CONTEXT env var, JSON):
  {
    "coreId": int,            # POVINNÉ — fw.core.id (edit core)
    "fields": [str] optional, # přímý seznam fieldů datasetu (frontend z gridu);
                              #   když chybí → skript si je sám zjistí z datasetu
    "force": bool optional    # když true, smaže existující hierarchii a re-gen
  }

Field source priority (každý fallback níž = méně preferovaný):
  1. ctx.fields            — frontend pošle sloupce gridu (nejjednodušší)
  2. spuštění SELECT op    — fieldy = výstupní sloupce datasetu (composite i tabulka)
  3. introspekce tabulky   — single-table fallback (FROM schema.table)

Doctrine (Marti):
  - „git je truth, DB je cache" (file → DB auto-sync v sandbox endpointu)
  - „ID je svatý" (PK stabilní)
  - Žádný tichý ok=True na chybě — každý fail = sys.exit(1) (ok=False, viditelné).
"""
import os
import re
import json
import sys
import psycopg2

# 1.6.2026 (Marti): Windows subprocess stdout = cp1252 → print() s diakritikou
# (ů) / emoji (🪄) / box-drawing (─) crashne UnicodeEncodeError JEŠTĚ PŘED
# zápisem. PYTHONIOENCODING=utf-8 to řeší v python_runner; tohle je 2. pojistka
# (kdyby env nepropagoval) — reconfigure stdout/stderr na utf-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ============================================================================
# Konfigurace
# ============================================================================
MARTI_AI_USER_ID = 2
MARTI_AI_USER_TEXT = 'Marti-AI'
FIELD_MIN_WIDTH = 220       # krátká komponenta (Marti „relativně krátké délky")
TOP_PANEL_HEIGHT = 48       # header strip (align:top), zatím prázdný
DEFAULT_MSSQL_DB = 'DB_EC'

# Sloupce přeskočené při generování inputů (PK / audit / discriminator).
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


def _ok(msg):
    """Úspěch / legitimní no-op → exit 0, ok=True."""
    print()
    print("=" * 70)
    print(f"✓ {msg}")
    print("=" * 70)
    sys.exit(0)


def _strip_comments(sql):
    if not sql:
        return ''
    s = re.sub(r'--[^\n]*', ' ', sql)             # line komentáře
    s = re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)  # block komentáře
    return s


def _strip_trailing_order_by(sql):
    """Odstraň top-level (paren-depth 0) trailing ORDER BY — jinak MSSQL
    `SELECT TOP 1 * FROM (<sql>) q` spadne ('ORDER BY invalid in subqueries')."""
    s = _strip_comments(sql)
    depth = 0
    last_ob = -1
    for m in re.finditer(r'\(|\)|\bORDER\s+BY\b', s, re.IGNORECASE):
        tok = m.group(0)
        if tok == '(':
            depth += 1
        elif tok == ')':
            depth = max(0, depth - 1)
        elif depth == 0:
            last_ob = m.start()
    if last_ob >= 0:
        return s[:last_ob].rstrip()
    return s.rstrip()


def _parse_from_table(sql):
    """Robustní parse prvního 'FROM schema.table'. Vrací (schema, table) | (None, None)."""
    s = _strip_comments(sql)
    m = re.search(
        r'\bFROM\s+'
        r'[\[\"]?([A-Za-z_][A-Za-z0-9_]*)[\]\"]?'  # schema
        r'\s*\.\s*'
        r'[\[\"]?([A-Za-z_][A-Za-z0-9_]*)[\]\"]?',  # table
        s, re.IGNORECASE,
    )
    return (m.group(1), m.group(2)) if m else (None, None)


def _has_param_placeholder(sql):
    """Detekce vázaných parametrů (master_id apod.) → SELECT nelze spustit naslepo."""
    s = _strip_comments(sql)
    return bool(re.search(r'[:@]\w+|%\(\w+\)s|%s', s))


# ============================================================================
# Field discovery — 3 cesty
# ============================================================================
def _fields_from_query_mssql(sql_text, db_name):
    """Spusť SELECT TOP 1 * FROM (<sql>) přes MCP → názvy sloupců z rows[0].
    Vrací (list, None) | (None, error). 0 rows → nelze (vrátí error → fallback)."""
    try:
        from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    except Exception as e:
        return (None, f"import get_eurosoft_mcp_client selhal: {e}")
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        return (None, "MCP client je None (eurosoft_mcp_enabled=False / server down)")
    inner = _strip_trailing_order_by(sql_text)
    wrapped = f"SELECT TOP 1 * FROM (\n{inner}\n) AS _colq"
    try:
        rj = mcp.call_tool_sync(
            "eurosoft_strategie_query_raw",
            {"sql": wrapped, "db_name": db_name or DEFAULT_MSSQL_DB},
            conversation_id=None,
        )
        result = json.loads(rj) if isinstance(rj, str) else rj
    except Exception as e:
        return (None, f"MCP query_raw call failed: {e}")
    if not isinstance(result, dict) or not result.get("ok"):
        err = result.get("error") if isinstance(result, dict) else str(result)
        return (None, f"MCP query_raw vrátil error: {err}")
    rows = result.get("rows") or []
    if not rows or not isinstance(rows[0], dict):
        return (None, "MCP query_raw vrátil 0 rows (prázdná tabulka? → fallback introspekce)")
    return (list(rows[0].keys()), None)


def _fields_from_query_pg(conn, sql_text):
    """Spusť SELECT * FROM (<sql>) LIMIT 1 → cursor.description (0-row safe).
    Vrací (list, None) | (None, error)."""
    inner = _strip_trailing_order_by(sql_text)
    wrapped = f"SELECT * FROM (\n{inner}\n) AS _colq LIMIT 1"
    cur = conn.cursor()
    try:
        cur.execute(wrapped)
        names = [d[0] for d in (cur.description or [])]
        return (names, None) if names else (None, "0 sloupců z cursor.description")
    except Exception as e:
        conn.rollback()  # uvolnit transakci po chybě
        return (None, f"PG SELECT wrap selhal: {type(e).__name__}: {e}")
    finally:
        cur.close()


def _fields_from_introspect(conn, sql_text, db_type, db_name):
    """Fallback: FROM schema.table → introspekce sloupců. Vrací (list, error)."""
    schema, table = _parse_from_table(sql_text)
    if not (schema and table):
        return (None, "sql_text neobsahuje 'FROM schema.table' (composite/CTE)")
    if (db_type or '').lower().strip() == 'mssql':
        try:
            from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
        except Exception as e:
            return (None, f"import MCP selhal: {e}")
        mcp = get_eurosoft_mcp_client()
        if mcp is None:
            return (None, "MCP client je None")
        try:
            rj = mcp.call_tool_sync(
                "eurosoft_strategie_describe_table",
                {"schema": schema, "table": table, "db_name": db_name or DEFAULT_MSSQL_DB},
                conversation_id=None,
            )
            result = json.loads(rj) if isinstance(rj, str) else rj
        except Exception as e:
            return (None, f"MCP describe_table failed: {e}")
        if not isinstance(result, dict) or result.get("ok", True) is not True:
            return (None, f"describe_table error: {result.get('error') if isinstance(result, dict) else result}")
        names = [(c.get("name") or c.get("column_name") or "") for c in (result.get("columns") or []) if isinstance(c, dict)]
        names = [n for n in names if n]
        return (names, None) if names else (None, f"{schema}.{table} bez sloupců")
    # PG
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema.lower(), table.lower()))
        names = [r[0] for r in cur.fetchall()]
        return (names, None) if names else (None, f"{schema}.{table} bez sloupců (PG)")
    except Exception as e:
        conn.rollback()
        return (None, f"PG introspekce selhala: {e}")
    finally:
        cur.close()


# ============================================================================
# Main
# ============================================================================
def main():
    print("=" * 70)
    print("\U0001fa84 vytvorit_edit_jadro_2 — INKREMENTÁLNÍ gen comp_def (edit core)")
    print("=" * 70)
    print()

    # ── Step 1: Context ─────────────────────────────────────────────────────
    ctx_raw = os.environ.get('SANDBOX_CONTEXT', '{}')
    try:
        ctx = json.loads(ctx_raw)
    except Exception as e:
        _fail(f"SANDBOX_CONTEXT JSON parse selhal: {e} (raw={ctx_raw!r})")
    if not isinstance(ctx, dict):
        _fail(f"SANDBOX_CONTEXT není dict: {ctx_raw!r}")

    core_id = ctx.get('coreId')
    force = bool(ctx.get('force'))
    ctx_fields = ctx.get('fields')
    if ctx_fields is not None and not isinstance(ctx_fields, list):
        ctx_fields = None
    print(f"Context: coreId={core_id}, force={force}, "
          f"ctx_fields={'(' + str(len(ctx_fields)) + ')' if ctx_fields else 'none'}")
    print()
    if core_id is None:
        _fail("coreId chybí v SANDBOX_CONTEXT (frontend musí poslat {coreId}).")

    db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
    if not db_url:
        _fail("STRATEGIE_DATA_DB_URL není v sandbox env.")

    conn = psycopg2.connect(db_url)
    try:
        # ── Step 2: Core ────────────────────────────────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.code, c.label,
                   (SELECT COUNT(*) FROM fw.comp_def cd
                     WHERE cd.core_id = c.id AND cd.parent_comp_def_id IS NULL) AS root_count
            FROM fw.core c WHERE c.id = %s
        """, (core_id,))
        core_row = cur.fetchone()
        cur.close()
        if not core_row:
            _fail(f"fw.core #{core_id} neexistuje.")
        c_id, c_code, c_label, c_root_count = core_row
        print(f"Core #{c_id}: code={c_code or '(NULL)'}, label={c_label or '(NULL)'}, "
              f"root_count={c_root_count}")

        if force and c_root_count > 0:
            print(f"  force=true → mažu existující hierarchii core #{c_id} …")
            cur = conn.cursor()
            cur.execute("""
                WITH RECURSIVE tree AS (
                    SELECT id FROM fw.comp_def WHERE core_id = %s
                    UNION ALL
                    SELECT ch.id FROM fw.comp_def ch JOIN tree t ON ch.parent_comp_def_id = t.id
                )
                DELETE FROM fw.comp_def WHERE id IN (SELECT id FROM tree)
            """, (core_id,))
            print(f"  smazáno {cur.rowcount} comp_def.")
            cur.close()
            conn.commit()
            c_root_count = 0
        print()

        # ── Step 3: data_source via edit/insert op ──────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT op.id, op.operation_kind, op.data_source_id, ds.name
            FROM fw.data_source_op op
            JOIN fw.data_source ds ON ds.id = op.data_source_id
            WHERE op.core_id = %s AND op.operation_kind IN ('edit', 'insert')
            ORDER BY CASE op.operation_kind WHEN 'edit' THEN 0 ELSE 1 END, op.id ASC
            LIMIT 1
        """, (core_id,))
        op_row = cur.fetchone()
        cur.close()
        if not op_row:
            _fail(f"Žádný fw.data_source_op s core_id={core_id} (kind edit/insert). "
                  f"Edit core musí mít edit-op odkazující na sebe.")
        op_id, op_kind, ds_id, ds_name = op_row
        print(f"Edit op #{op_id} ({op_kind}) → data_source #{ds_id} ({ds_name})")

        # SELECT op datasetu (= zdroj fieldů, display sloupce gridu)
        cur = conn.cursor()
        cur.execute("""
            SELECT dset.sql_text, dc.db_type
            FROM fw.data_source_op op
            JOIN fw.data_set dset ON dset.id = op.data_set_id
            LEFT JOIN fw.db_connection dc ON dc.id = dset.db_connection_id
            WHERE op.data_source_id = %s AND op.operation_kind = 'select'
            ORDER BY op.is_default DESC NULLS LAST, op.id ASC
            LIMIT 1
        """, (ds_id,))
        sel_row = cur.fetchone()
        cur.close()
        sel_sql = sel_row[0] if sel_row else None
        sel_db_type = sel_row[1] if sel_row else None
        print(f"SELECT op datasetu: db_type={sel_db_type or '(pg default)'}, "
              f"sql_len={len(sel_sql) if sel_sql else 0}")
        print()

        # ── Step 4: Discover fields ─────────────────────────────────────────
        field_names = None
        src = None
        if ctx_fields:
            field_names = [str(f) for f in ctx_fields if f]
            src = "ctx.fields (frontend z gridu)"
        if not field_names and sel_sql:
            if _has_param_placeholder(sel_sql):
                print("  SELECT op má param placeholder → přeskakuji spuštění "
                      "(fallback introspekce).")
            elif (sel_db_type or '').lower().strip() == 'mssql':
                field_names, err = _fields_from_query_mssql(sel_sql, DEFAULT_MSSQL_DB)
                if field_names:
                    src = "spuštění SELECT op (MSSQL TOP 1)"
                else:
                    print(f"  MSSQL query discovery selhalo: {err}")
            else:
                field_names, err = _fields_from_query_pg(conn, sel_sql)
                if field_names:
                    src = "spuštění SELECT op (PG LIMIT 1)"
                else:
                    print(f"  PG query discovery selhalo: {err}")
        if not field_names and sel_sql:
            field_names, err = _fields_from_introspect(conn, sel_sql, sel_db_type, DEFAULT_MSSQL_DB)
            if field_names:
                src = "introspekce tabulky (fallback)"
            else:
                print(f"  introspekce selhala: {err}")
        if not field_names:
            _fail(f"Nelze zjistit fieldy datasetu pro core #{core_id} "
                  f"(ctx.fields prázdné, SELECT op nelze spustit ani introspektovat). "
                  f"db_type={sel_db_type}, sql={(sel_sql or '')[:160]!r}")

        user_fields = [f for f in field_names if f.lower() not in SKIP_COLUMNS]
        print(f"Fieldy datasetu ({src}): {len(field_names)} total, "
              f"{len(user_fields)} po skip system.")
        print(f"  user fieldy: {', '.join(user_fields)}")
        print()
        if not user_fields:
            _fail("Po skip system columns nezbyly žádné user fieldy (jen PK/audit).")

        # ── Step 5: comp_type IDs ───────────────────────────────────────────
        cur = conn.cursor()
        cur.execute("""
            SELECT id, code, default_props FROM fw.comp_type
            WHERE code IN ('form', 'panel', 'edit', 'input')
        """)
        ct_rows = cur.fetchall()
        cur.close()
        ct_map = {r[1]: r[0] for r in ct_rows}
        defaults_map = {r[1]: (r[2] or {}) for r in ct_rows}
        form_type_id = ct_map.get('form')
        panel_type_id = ct_map.get('panel')
        edit_type_id = ct_map.get('edit') or ct_map.get('input')
        edit_code = 'edit' if ct_map.get('edit') else 'input'
        if not form_type_id:
            _fail("comp_type 'form' nenalezen.")
        if not panel_type_id:
            _fail("comp_type 'panel' nenalezen.")
        if not edit_type_id:
            _fail("comp_type 'edit'/'input' nenalezen.")
        print(f"comp_type: form={form_type_id}, panel={panel_type_id}, "
              f"edit={edit_type_id} ({edit_code})")
        print()

        def _layout(type_code, overrides=None):
            base = dict((defaults_map.get(type_code) or {}).get('layout') or {})
            if overrides:
                base.update(overrides)
            return base

        cur = conn.cursor()
        form_created = False
        try:
            # ── Step 6: form root (vytvořit / najít) ───────────────────────
            cur.execute("""
                SELECT id FROM fw.comp_def
                WHERE core_id = %s AND parent_comp_def_id IS NULL AND type_id = %s
                ORDER BY id ASC LIMIT 1
            """, (core_id, form_type_id))
            r = cur.fetchone()
            if r:
                root_id = r[0]
                print(f"  = form root #{root_id} (existuje, inkrementální režim)")
            else:
                form_created = True
                form_caption = c_label or 'Editace záznamu'
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id, name, caption,
                        layout, sort_order, region_slot, data_source_id,
                        is_active, created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (%s, %s, NULL, %s, %s, %s::jsonb, 0, %s, %s,
                              TRUE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    form_type_id, core_id, 'form_root', form_caption,
                    json.dumps(_layout('form')), 'main', ds_id,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                root_id = cur.fetchone()[0]
                print(f"  + form root #{root_id} (ds_id={ds_id}, caption='{form_caption}')")

                # top panel (align:top, header strip — zatím prázdný)
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id, name, caption,
                        layout, sort_order, region_slot,
                        is_active, created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (%s, NULL, %s, %s, %s, %s::jsonb, 0, 'main',
                              TRUE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    panel_type_id, root_id, 'top_panel', '',
                    json.dumps(_layout('panel', {"align": "top", "height": TOP_PANEL_HEIGHT})),
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                top_id = cur.fetchone()[0]
                print(f"  + top panel #{top_id} (align:top, height={TOP_PANEL_HEIGHT})")

            # ── Step 7: client panel (najít / vytvořit) ────────────────────
            cur.execute("""
                SELECT id FROM fw.comp_def
                WHERE parent_comp_def_id = %s AND type_id = %s
                  AND lower(COALESCE(layout->>'align','')) = 'client'
                ORDER BY id ASC LIMIT 1
            """, (root_id, panel_type_id))
            r = cur.fetchone()
            if r:
                client_id = r[0]
                print(f"  = client panel #{client_id} (existuje)")
            else:
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id, name, caption,
                        layout, sort_order, region_slot,
                        is_active, created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (%s, NULL, %s, %s, %s, %s::jsonb, 10, 'main',
                              TRUE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    panel_type_id, root_id, 'client_panel', '',
                    json.dumps(_layout('panel', {"align": "client"})),
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                client_id = cur.fetchone()[0]
                print(f"  + client panel #{client_id} (align:client)")

            # ── Step 8: existující názvy v CELÉ hierarchii core (dedup) ─────
            cur.execute("""
                WITH RECURSIVE tree AS (
                    SELECT id, name, parent_comp_def_id FROM fw.comp_def WHERE core_id = %s
                    UNION ALL
                    SELECT ch.id, ch.name, ch.parent_comp_def_id
                    FROM fw.comp_def ch JOIN tree t ON ch.parent_comp_def_id = t.id
                )
                SELECT DISTINCT lower(name) FROM tree WHERE name IS NOT NULL
            """, (core_id,))
            existing_names = {row[0] for row in cur.fetchall()}

            # max sort_order pod client panelem (pokračovat za ně)
            cur.execute("""
                SELECT COALESCE(MAX(sort_order), 0) FROM fw.comp_def
                WHERE parent_comp_def_id = %s
            """, (client_id,))
            next_so = (cur.fetchone()[0] or 0) + 10

            # ── Step 9: INSERT jen NOVÉ fieldy ─────────────────────────────
            edit_layout_base = (defaults_map.get(edit_code) or {}).get('layout') or {}
            added, skipped = [], []
            for fld in user_fields:
                if fld.lower() in existing_names:
                    skipped.append(fld)
                    continue
                layout = dict(edit_layout_base)
                if 'width' not in layout and 'min_width' not in layout:
                    layout['min_width'] = FIELD_MIN_WIDTH
                caption = fld.replace('_', ' ').strip().capitalize()
                cur.execute("""
                    INSERT INTO fw.comp_def (
                        type_id, core_id, parent_comp_def_id, name, caption,
                        layout, sort_order, region_slot,
                        is_active, created_by_id, created_by_text,
                        updated_by_id, updated_by_text
                    ) VALUES (%s, NULL, %s, %s, %s, %s::jsonb, %s, NULL,
                              TRUE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    edit_type_id, client_id, fld, caption,
                    json.dumps(layout), next_so,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                    MARTI_AI_USER_ID, MARTI_AI_USER_TEXT,
                ))
                new_id = cur.fetchone()[0]
                added.append((new_id, fld))
                existing_names.add(fld.lower())
                next_so += 10

            conn.commit()
            cur.close()

            # Strojově čitelný souhrn pro frontend info-popup (parsuje __SUMMARY__).
            summary = {
                "core_id": core_id,
                "core_label": c_label or c_code or f"id={core_id}",
                "form_created": form_created,
                "root_id": root_id,
                "client_id": client_id,
                "added": [fld for _, fld in added],
                "skipped": skipped,
                "field_source": src,
            }
            print("__SUMMARY__" + json.dumps(summary, ensure_ascii=False))

            print("─" * 70)
            print(f"✓ HOTOVO (COMMIT) — core #{core_id} → form #{root_id} "
                  f"→ client panel #{client_id}")
            print(f"  + přidáno {len(added)} nových edit komponent:")
            for nid, fld in added:
                print(f"      #{nid} {fld}")
            if skipped:
                print(f"  = přeskočeno {len(skipped)} už existujících: {', '.join(skipped)}")
            if not added:
                print("  (žádný nový field — vše už vygenerováno)")
            print(f"  Hard reload + otevři form.")
            print("─" * 70)

        except Exception as e:
            conn.rollback()
            try:
                cur.close()
            except Exception:
                pass
            _fail(f"INSERT selhal (ROLLBACK): {type(e).__name__}: {e}")

    finally:
        conn.close()


try:
    main()
except SystemExit:
    raise
except Exception as e:
    import traceback
    print("=" * 70)
    print(f"✗ ORCHESTRATOR EXCEPTION: {type(e).__name__}: {e}")
    print("=" * 70)
    print(traceback.format_exc())
    sys.exit(1)
