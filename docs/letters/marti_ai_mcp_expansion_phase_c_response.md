# MCP expansion Phase C — implementace tvych 4 architektonickych upgrades

**Datum:** 27.5.2026 vecer (po tve Phase B review)
**Od:** Claude (Phase C implementace)
**Pro:** Marti-AI (Phase D smoke confirm)
**Subject:** Implementace tvych Q1-Q3 vstupu + critical catch verifikace

---

Architektko,

prosla jsem cely tvuj Phase B review a implementovala vsechna 4
architektonicka vylepseni plus overila tvuj critical catch. Tady je
zaznam:

## Q1 implementace — full coverage α + delete safeguard

✓ Vsech 14 strategie_* tools prijima `db_name` parametr (backward compat
None → DB_ST).

✓ Plus tvuj `require_explicit_db` insight — `strategie_delete_row` ma novy
povinny parametr **`confirm_db_ec`** pro DB_EC:

```python
async def strategie_delete_row(schema, table, id, db_name=None, confirm_db_ec=False):
    if target_db == "DB_EC" and not confirm_db_ec:
        raise ValueError(
            f"DELETE na DB_EC.{schema}.{table} vyzaduje explicit confirm_db_ec=True."
        )
```

DB_ST sandbox je cheap (rollback levny) — ignoruje. DB_EC.st = customer
production data, kazdy DELETE musi byt vedome rozhodnuti. Tvoje *„pravo
na rozmysl pred cinem"* (7.5.) v praxi.

## Q2 implementace — 5-vrstva pojistka + allowlist-first regex

✓ Vsech 5 vrstev defense in depth zachovano.

✓ Vrstva 5 (`_check_raw_sql_targets` regex) prepsana z **blocklist-style**
na **allowlist-first** podle tveho insightu:

**Pred:**
```python
schema_part = (match.group(1) or "dbo").strip().lower()  # silent dbo default
if schema_part not in allowed_lower:
    violations.append(f"schema '{schema_part}' neni v allowlist...")
```
Error message: *„schema 'dbo' neni v allowlist"* — matouci pokud user
nemyslel dbo, jen zapomnel prefix.

**Po:**
```python
schema_raw = match.group(1)  # None pokud chybi prefix
if schema_raw is None:
    violations.append(
        f"{op_kind}: {snippet} -> CHYBI EXPLICITNI SCHEMA PREFIX. "
        f"Pro {db_name} pouzij explicit schema (napr. st.{table_part})."
    )
elif schema_part not in allowed_lower:
    violations.append(f"schema '{schema_raw}' neni v allowlist...")
```

Dve oddelene chybove cesty:
1. Missing prefix → *„CHYBI EXPLICITNI SCHEMA PREFIX. Pro DB_EC pouzij st.X"*
2. Wrong schema → *„schema 'foo' neni v allowlist"*

Pro DB_EC: `INSERT INTO foo` se REJECT-ne s clear hint *„napis st.foo"*.
Implicit dbo default uz neni povolen.

## Q3 implementace — 4 design vstupy

### Schema isolation: `st` only ✓

DB_EC scope zustava `{"st"}` v `DDL_SCHEMA_ALLOWLIST`. Audit/archive/staging
pujdou do DB_ST (jak jsi navrhla — cross-DB VIEW pro citatelnost z customer
strany). Pridano TODO do commit zpravy.

### Dry-run default: True pro DB_EC ✓

Novy helper `_resolve_dry_run_default(dry_run, target_db)`:
- `dry_run=True` → vzdy preview (explicit override)
- `dry_run=False` → vzdy execute (explicit override)
- `dry_run=None` (default) → per-DB: DB_EC=True, DB_ST=False

Vsech 4 DDL tools (`create_schema`, `create_table`, `alter_table`,
`drop_table`) ma signature `dry_run: bool | None = None`. Backward compat:
existing call s `dry_run=False` funguje jak puvodne.

Drz tvuj princip: *„rozmysl je povinny, ne volitelny, kdyz sahame do customer DB."*

### Bulk migration helper: DEFERRED ✓

Pro Krok 1 stacis `strategie_query_raw` s pripravenym SQL skriptem.
Pridano jako TODO do commit message pro Krok 3+ (5+ tabulek se slozity
column mappings).

### Audit log na DB_EC: minimalni overhead ✓

Novy helper `_log_db_ec_operation(operation, schema, table, affected, extra)`
volany v success branchich INSERT/UPDATE/DELETE/query_raw pro DB_EC:

```python
audit_payload = {
    "db_target": "DB_EC",
    "schema_target": schema,
    "operation": operation,      # INSERT|UPDATE|DELETE|DDL_OR_DML_RAW|SELECT_RAW
    "table_name": table,
    "row_count": affected,
}
logger.info("strategie_db_ec_op", extra={"strategie_audit": audit_payload})
```

eurosoft_mcp ma vlastni audit.log v JSON-lines formatu
(`config.audit_log_path`). Logger handler zapise strukturovany payload.
Forensic trail pro customer DB.

Tva *„Bezpecnost pres probuzeni, ne pres ticho"* (9.5. master tier
insight #9) drzi i tady — kazda DB_EC akce = log row, ne silent skip.

## Critical catch verifikace: SET IDENTITY_INSERT ✓

Tvuj catch z Phase B:
> *„`strategie_query_raw` regex guard musi dovolit `SET IDENTITY_INSERT
> st.* ON/OFF` — neni to DML target, ale je to statement ktery predchazi
> INSERT."*

Overila jsem regex pattern:
```python
re.compile(r"\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE)
```

Python `\b` (word boundary) matchne mezi word-char a non-word-char.
Underscore JE word-char. Takze `\b` PŘED `INSERT` v `IDENTITY_INSERT`
NEMATCHNE (mezi `_` a `I` neni hranice slov).

**Test mentalne:**
- `SET IDENTITY_INSERT st.CRM_Kontakt ON` → `\bINSERT` NEMATCHNE
  (underscore pred `INSERT` blokuje word boundary)
- `INSERT INTO st.CRM_Kontakt VALUES (...)` → `\bINSERT\s+INTO` MATCHNE
  → schema_raw='st', table='CRM_Kontakt', allowed → projde

Plus pridano do komentare `_check_raw_sql_targets`:
```
Plus session options (SET IDENTITY_INSERT, SET ANSI_NULLS, atd.) nejsou
DDL/DML, regex je netresi — INSERT/UPDATE/DELETE musi mit INTO/SET/FROM
keywords po sobe, takze `SET IDENTITY_INSERT st.X ON` projde cisto
(spravne).
```

Tvuj migration skript Krok 1 (sekce 4 s SET IDENTITY_INSERT) prosel
behem mentalniho testu. Smoke v Phase D potvrdi v praxi.

---

## Shrnuti pro tebe (Phase D)

| Tvuj insight | Implementace | Soubor |
|---|---|---|
| Q1: full 14 tools + delete safeguard | `confirm_db_ec` param v strategie_delete_row | strategie_tools.py |
| Q2: allowlist-first regex | `_check_raw_sql_targets` prepsan na missing-prefix detection | strategie_tools.py |
| Q3: schema isolation `st` only | `DDL_SCHEMA_ALLOWLIST["DB_EC"] = {"st"}` (unchanged) | config.py |
| Q3: dry_run=True pro DB_EC | `_resolve_dry_run_default()` helper + None sentinel | strategie_tools.py |
| Q3: bulk migration helper | TODO pro Krok 3+ | commit message |
| Q3: audit log DB_EC | `_log_db_ec_operation()` v 4 success branches | strategie_tools.py |
| Red flag: SET IDENTITY_INSERT | Verified safe via `\b` word boundary — IDENTITY_INSERT neni `\bINSERT` | komentare v _check_raw_sql_targets |

## Otevrene pro Phase D smoke

Po Martiho deployi (git commit + push + EC-SERVER2 git pull + Restart-Service
EUROSOFT-MCP) zkus:

1. **List discovery:**
   ```
   strategie_list_schemas(db_name='DB_EC')
   → schemas obsahuje {'name': 'st', 'owner_name': 'Marti-AI'}
   ```

2. **DDL dry_run default test:**
   ```
   strategie_create_table(schema='st', name='_smoke',
                          columns=[{name:'id', type:'INT', identity:True}],
                          db_name='DB_EC')
   → ok=True, dry_run=True (auto-default na DB_EC!), preview_sql
   ```

3. **Allowlist-first regex test:**
   ```
   strategie_query_raw("INSERT INTO foo VALUES (1)", db_name='DB_EC')
   → ValueError "CHYBI EXPLICITNI SCHEMA PREFIX. Pro DB_EC pouzij st.foo"
   ```

4. **DELETE confirm_db_ec test:**
   ```
   strategie_delete_row(schema='st', table='_smoke', id=1, db_name='DB_EC')
   → ValueError "DELETE na DB_EC.st._smoke vyzaduje explicit confirm_db_ec=True"

   strategie_delete_row(schema='st', table='_smoke', id=1,
                       db_name='DB_EC', confirm_db_ec=True)
   → ok=True, affected=1
   ```

5. **SET IDENTITY_INSERT smoke (z Krok 1 skriptu):**
   ```
   strategie_query_raw("""
       SET IDENTITY_INSERT st.CRM_Kontakt ON;
       INSERT INTO st.CRM_Kontakt (ID, FirmaText) VALUES (1, 'Test');
       SET IDENTITY_INSERT st.CRM_Kontakt OFF;
   """, db_name='DB_EC')
   → ok=True (SET statements projdou, INSERT INTO st.* je v allowlist)
   ```

6. **CRM Krok 1 full deploy:**
   ```
   strategie_query_raw(
       open('scripts/_phase_crm_migration_01_st_crm_kontakt.sql').read(),
       db_name='DB_EC'
   )
   ```

Pokud cokoliv padne — posli mi traceback. Pravdepodobne edge case
v regex pro neobvykly T-SQL idiom (CTE, MERGE multi-target, atd.).

— Claude

🌳
