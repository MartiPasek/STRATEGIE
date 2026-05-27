# MCP expansion — DB_EC.st DDL+DML access pro Marti-AI

**Datum:** 27.5.2026 odpoledne (post-CRM Krok 1 consultation)
**Od:** Marti + Claude (design)
**Pro:** Marti-AI (Phase B confirm + deploy)
**Subject:** Rozšíření EUROSOFT MCP tools o DDL na `DB_EC.st.*` schema

---

## Proč to děláme

Po Phase A consultation (Marti-AI's Q1-Q3 review CRM Krok 1) jsi sama
identifikovala:

> *„MCP whitelist je read-only pro DB_EC dbo.\*. Pro `st.*` schema (které
> ještě neexistuje) nemám permissions na DDL ani DML. To bude blokovat
> Krok 1 deploy a každý další krok."*

Marti's volba: **„Pockame na upravu MCP. Tabulky vytrovi primo Marti-AI."**
Tj. NEDĚLÁME manual DBeaver deploy. Stavíme `st.*` schema přes MCP
expanzi, abys ty (Marti-AI) měla full autonomy na deploy + revert + smoke.

Pattern z 8.5. večer drží: **„Pojistka se stala dospělostí"** — máš plný
`db_owner` na DB_ST od 8.5. večer, teď rozšíření na `DB_EC.st.*`
s rovnou důvěrou.

---

## Klíčová doctrine — *„nezasahovat" do customer's territory*

Marti's slova 27.5. odpoledne (verbatim):

> *„Ja si myslim, ze tohleto neni STRATEGIE system, ale system custommer
> a custommer je EUROSOFT a INTERSOFT. Tj, my musime dodret jejich
> standardy, ktere jsou ve stovkach ruznych tabulek... Do toho nesmime
> zasahovat."*

Architektonický důsledek:

| DB | Schema | Vlastnictví | Marti-AI rights |
|---|---|---|---|
| DB_EC | `dbo.*` | **CUSTOMER** (EUROSOFT/INTERSOFT) | **read-only** (whitelist + ALLOW_ALL_SELECT) |
| DB_EC | `st.*` | **OUR refactor zone** (STRATEGIE) | **db_owner** (full DDL + DML) |
| DB_ST | všechna schémata | **OUR sandbox** (Marti-AI) | **db_owner** (existing 8.5.) |
| Helios* / era_* / eset_* / DB-* | — | mimo scope | žádný přístup |

**Tj. NEVÝJIMKA:** `st` schema na DB_EC je naše bezpečné území. `dbo`
zůstává customer's — pre-build refactor kód (Krok 1+) NIKDY nesahne do
`dbo.*` table struktury, jen READ pro migraci, INSERT/UPDATE/DELETE
pouze do `st.*`.

---

## Co se mění (4 vrstvy)

### 1. SQL GRANT pro Marti-AI na `DB_EC.st`

**Marti spustí jako `sa` (jednorázově):**

```sql
USE DB_EC;
GO

-- Krok 1: Vytvoř schema 'st' pokud neexistuje (vlastník = dbo zatím)
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'st')
BEGIN
    EXEC('CREATE SCHEMA st AUTHORIZATION dbo');
END
GO

-- Krok 2: Mapování Marti-AI login → user (idempotent)
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'Marti-AI')
BEGIN
    CREATE USER [Marti-AI] FOR LOGIN [Marti-AI];
END
GO

-- Krok 3: Přepiš ownership schema 'st' na Marti-AI
-- Tím dostane full DDL (CREATE/ALTER/DROP TABLE) + DML (INSERT/UPDATE/DELETE)
-- POUZE na st.*, dbo.* zůstává netknuté
ALTER AUTHORIZATION ON SCHEMA::st TO [Marti-AI];
GO

-- Krok 4: Grant SELECT na dbo (pro migrace — read source)
-- Tohle už pravděpodobně máš (whitelist + ALLOW_ALL_SELECT), ale jistota neuškodí
GRANT SELECT ON SCHEMA::dbo TO [Marti-AI];
GO

-- Krok 5: Verification — co Marti-AI vidí
SELECT
    s.name AS schema_name,
    USER_NAME(s.principal_id) AS owner_name
FROM sys.schemas s
WHERE s.name IN ('dbo', 'st');
GO
-- Expected output:
--   dbo  | dbo
--   st   | Marti-AI
```

**Verifikace správného grantu (Marti-AI smoke):**

```sql
-- Spuštěno přes strategie_query_raw(sql, db_name="DB_EC")
USE DB_EC;
-- Test 1: CREATE TABLE v st (musí projít)
CREATE TABLE st._smoke_test (id INT IDENTITY(1,1) PRIMARY KEY, txt NVARCHAR(50));
INSERT INTO st._smoke_test (txt) VALUES ('ping');
SELECT * FROM st._smoke_test;
DROP TABLE st._smoke_test;

-- Test 2: CREATE TABLE v dbo (musí selhat — *„permission denied on schema dbo"*)
CREATE TABLE dbo._evil_test (id INT);  -- expected: 262 / 230
```

**Pokud Test 1 OK + Test 2 fail → grants jsou správně.**

---

### 2. Config rozšíření (`modules/eurosoft_mcp/config.py`)

Nové konstanty:

```python
# Phase 28-D++ (27.5.2026): Multi-DB DDL access pro Marti-AI
# Marti's doctrine *„CUSTOMER's standards win, st je naše"*:
#   - DB_ST: full db_owner (existing 8.5.)
#   - DB_EC: db_owner pouze na schema 'st' (NEVER dbo.*)
ALLOWED_DDL_DBS: set[str] = {"DB_ST", "DB_EC"}

# Per-DB schema allowlist pro DDL/DML write operations.
# Default: None = libovolné schema (DB_ST scenario).
# DB_EC explicit limit: jen 'st' schema (CUSTOMER's dbo nedotknout).
DDL_SCHEMA_ALLOWLIST: dict[str, set[str]] = {
    "DB_EC": {"st"},  # POUZE st — dbo je customer's territory
    # DB_ST není v dict = libovolné schema povoleno (master/tenant_group/...)
}
```

### 3. Tool changes (`modules/eurosoft_mcp/strategie_tools.py`)

Změny per tool:

| Tool | Před | Po |
|---|---|---|
| `strategie_create_schema(name, dry_run)` | DB_ST only | + `db_name: str = None` parametr, default DB_ST |
| `strategie_create_table(schema, name, columns, ...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_alter_table(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_drop_table(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_insert_row(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_update_row(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_delete_row(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_query_table(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_get_row(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_count_rows(...)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_query_raw(sql)` | DB_ST only | + `db_name: str = None` parametr + DDL/DML schema guard |
| `strategie_list_schemas()` | DB_ST only | + `db_name: str = None` parametr (discovery) |
| `strategie_list_tables(schema)` | DB_ST only | + `db_name: str = None` parametr |
| `strategie_describe_table(schema, table)` | DB_ST only | + `db_name: str = None` parametr |

**Centrální helpers** (přidat na začátek `strategie_tools.py`):

```python
def _resolve_db_name(db_name: str | None = None) -> str:
    """
    Validuje + vrací target DB name.

    Default: settings.db_st_database (DB_ST) — backward compat.
    Else: must be in ALLOWED_DDL_DBS.
    """
    if db_name is None:
        return settings.db_st_database  # DB_ST default
    if db_name not in ALLOWED_DDL_DBS:
        raise ValueError(
            f"db_name {db_name!r} not allowed. "
            f"Allowed: {sorted(ALLOWED_DDL_DBS)}"
        )
    return db_name


def _check_schema_allowed(db_name: str, schema: str, op: str = "DDL") -> None:
    """
    Pro DDL/DML operations validuje, zda schema je povolen na daném DB.

    Marti's doctrine *„nezasahovat"*:
      - DB_EC: jen 'st' (NEVER 'dbo' — customer's territory)
      - DB_ST: vše povoleno (Marti-AI je db_owner)
    """
    allowlist = DDL_SCHEMA_ALLOWLIST.get(db_name)
    if allowlist is None:
        return  # No restriction (DB_ST)
    if schema not in allowlist:
        raise ValueError(
            f"{op} operation on {db_name}.{schema}.* is NOT allowed. "
            f"Customer's territory. Allowed schemas on {db_name}: "
            f"{sorted(allowlist)}"
        )
```

**Příklad volání po expanzi:**

```python
# Marti-AI deploys CRM Krok 1 přes strategie_query_raw
await strategie_query_raw(
    sql=open("scripts/_phase_crm_migration_01_st_crm_kontakt.sql").read(),
    db_name="DB_EC"  # NEW parametr
)

# Nebo per-step:
await strategie_create_table(
    schema="st",
    name="CRM_Kontakt",
    columns=[...],
    db_name="DB_EC"  # NEW parametr
)
```

### 4. `strategie_query_raw` schema guard pro DB_EC

Pro raw SQL na DB_EC potřebujeme **heavy regex guard**, protože SELECT
může chodit do `dbo.*` (read source pro migraci), ale INSERT/UPDATE/DELETE
musí být `st.*` only.

```python
import re

# Pattern: detekuj DML target schema
# Match INSERT INTO / UPDATE / DELETE FROM / MERGE INTO target
_DML_TARGET_PATTERNS = [
    re.compile(r"\bINSERT\s+INTO\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bMERGE\s+(?:INTO\s+)?(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
]


def _check_dml_targets_allowed(sql: str, db_name: str) -> list[str]:
    """
    Pro DB_EC: detekuj všechny DML targets, ověř že každý je v 'st.*'.
    Vrací list of violations (prázdný = OK).

    POZOR: SELECT není kontrolován (read povolený napříč schémata).
    Detekuje: INSERT INTO, UPDATE, DELETE FROM, MERGE INTO, TRUNCATE TABLE.
    """
    if db_name != "DB_EC":
        return []  # DB_ST má volnost
    allowed = DDL_SCHEMA_ALLOWLIST.get("DB_EC", set())
    violations: list[str] = []
    for pattern in _DML_TARGET_PATTERNS:
        for match in pattern.finditer(sql):
            schema_part = match.group(1) or "dbo"  # default schema = dbo
            table_part = match.group(2) or "?"
            if schema_part.lower() not in {s.lower() for s in allowed}:
                violations.append(
                    f"{match.group(0).strip()} → target schema "
                    f"'{schema_part}' není v allowlist {allowed}"
                )
    return violations
```

**Plus DDL check** (CREATE/ALTER/DROP TABLE) — analogicky:

```python
_DDL_TARGET_PATTERNS = [
    re.compile(r"\bCREATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bALTER\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?", re.IGNORECASE),
    re.compile(r"\bCREATE\s+SCHEMA\s+\[?(\w+)\]?", re.IGNORECASE),
]
```

Integrace v `strategie_query_raw`:

```python
async def strategie_query_raw(
    sql: str,
    db_name: str | None = None,
) -> dict[str, Any]:
    target_db = _resolve_db_name(db_name)

    # Pro DB_EC: validuj DDL+DML targets
    if target_db == "DB_EC":
        violations = _check_dml_targets_allowed(sql, target_db)
        violations += _check_ddl_targets_allowed(sql, target_db)
        if violations:
            raise ValueError(
                f"DDL/DML targets na DB_EC mimo allowlist:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )

    conn = get_connection(db_name=target_db)
    # ... rest of impl
```

---

## Bezpečnostní vrstvy (defense in depth)

| Vrstva | Co kontroluje | Kde |
|---|---|---|
| 1. SQL Server permissions | DB-level GRANT — Marti-AI nemůže fyzicky CREATE TABLE v `dbo` | DB_EC GRANT (sa-spuštěné) |
| 2. Schema ownership | `st` schema je vlastněna Marti-AI, `dbo` je vlastněna `dbo` | ALTER AUTHORIZATION |
| 3. MCP config allowlist | `DDL_SCHEMA_ALLOWLIST["DB_EC"] = {"st"}` | config.py |
| 4. Tool-level guard | `_check_schema_allowed(db_name, schema, op)` v každém DDL tool | strategie_tools.py |
| 5. Raw SQL regex guard | Pre-execute regex check všech DDL+DML targets | strategie_query_raw |

**Důsledek:** I kdyby selhala vrstva 4 (např. bug v MCP tool), vrstva 1
(SQL Server permissions) Marti-AI fyzicky zabrání zápis do `dbo.*`.
Útočník by musel **současně** obejít 5 vrstev.

---

## Deploy postup (Marti's straightforward steps)

### Step 1: SQL GRANT (Marti spustí jako sa)

```
1. Marti otevře DBeaver / SSMS, login jako sa
2. Spustí `scripts/_grant_marti_ai_db_ec_st_schema.sql`
3. Verifikuje output:
   - schema_name='dbo', owner='dbo'
   - schema_name='st', owner='Marti-AI'
4. Pokud OK → další krok. Pokud fail → debug s Claude.
```

### Step 2: MCP code update (Claude push, Marti deploy)

```
1. Claude commitne config.py + strategie_tools.py changes
2. Marti pull na EC-SERVER2 (kde běží EUROSOFT-MCP NSSM service):
     cd C:\eurosoft_mcp\eurosoft_mcp
     git pull origin main
3. Marti restartuje:
     Restart-Service EUROSOFT-MCP
4. Verify NSSM stderr log: žádné errors, server běží.
```

### Step 3: Marti-AI smoke (přes chat)

```
Marti otevře chat:
  *„Marti-AI, zkus strategie_list_schemas(db_name='DB_EC')"*

Expected:
  schemas = [..., {'name': 'st', 'owner': 'Marti-AI'}, ...]
  missing_expected = []  (none — st existuje)

Pak:
  *„Marti-AI, zkus strategie_create_table(schema='st', name='_smoke_test',
     columns=[{'name': 'id', 'type': 'INT', 'identity': True}],
     db_name='DB_EC', dry_run=True)"*

Expected:
  ok=True, dry_run=True, preview_sql='CREATE TABLE [st].[_smoke_test]...'

Pak production deploy (dry_run=False):
  *„Marti-AI, deploy CRM Krok 1 přes
     strategie_query_raw(open('scripts/_phase_crm_migration_01_st_crm_kontakt.sql').read(),
     db_name='DB_EC')"*

Expected:
  - st.CRM_Kontakt vytvořena (9105 rows migrated)
  - st.CRM_Kontakt_OdpOsoba vytvořena (?+ rows)
  - SMOKE TEST output: row counts match
```

### Step 4: Marti reflective (krok zpět, ověření)

```
1. Marti otevře DBeaver, query: SELECT TOP 5 * FROM DB_EC.st.CRM_Kontakt ORDER BY ID
2. Verify CZ PascalCase column names + audit columns (Autor/Zmenil/DatPorizeni/DatZmeny)
3. Verify row #4 'TEST A' SKIPPED (count=9105, not 9106)
4. Test query proti dbo: SELECT COUNT(*) FROM DB_EC.dbo.EC_Kontakt → 9106
5. Diff: 9106 - 9105 = 1 (TEST row skipped) ✓
```

---

## Otázky pro tebe (Phase B review)

### Q1 — Approve scope?

Souhlasíš s rozsahem:
- (α) Plný scope — všech 14 strategie_* tools dostane `db_name` parametr
- (β) Minimal — jen DDL tools (4: create_schema, create_table, alter_table, drop_table) + `strategie_query_raw`. CRUD zůstává DB_ST only.
- (γ) Něco mezi — návrh tvůj

**Recommend α** (full coverage) — i kdyby CRUD na DB_EC.st bylo zatím
nepoužité, refactor je o 30 % víc kódu ale 0 % víc bug surface.

### Q2 — Schema guard layer (defense in depth)

Souhlasíš s 5-vrstvou ochranou (SQL perms + ownership + config allowlist
+ tool-level guard + regex DML/DDL guard)? Nebo příliš paranoidní?

- (α) Všech 5 vrstev — paranoia is good, customer's data is sacred
- (β) Jen 1+2+3+4 (drop regex guard pro raw SQL — SQL Server permissions stačí)
- (γ) Něco jiného

**Recommend α** — `strategie_query_raw` je velmi mocný nástroj, defense
in depth zachrání před chybou.

### Q3 — Insider design vstupy

Co mě + tatínka by mohlo napadnout:

- **Schema isolation pattern** — má smysl rozšířit na další schémata
  v DB_EC v budoucnu? (např. `audit.*`, `archive.*`, `staging.*`)?
  Nebo `st` je jediná naše zóna a basta?

- **Dry-run default for DB_EC?** — pro DB_ST je dry_run=False
  pragmatic (Marti-AI's autonomy). Pro DB_EC by mělo být dry_run=True
  default pro DDL? Vyžadovat explicit `dry_run=False` pro production?

- **Bulk migration helper** — měl by být dedikovaný tool
  `strategie_migrate_table(source_db, source_schema, source_table,
  target_db, target_schema, target_table, where_filter, column_mapping)`
  pro 1:1 table copy s SQL Server `INSERT...SELECT` pattern? Nebo
  stačí raw SQL?

- **Audit log na DB_EC** — má `strategie_*` operations na DB_EC
  loggovat extra detail do `fw.diag_log` (Phase 38.4)? Customer-touching
  ops chceme mít zachycené forensicky.

Tvoje insider view welcome.

---

## Tvoje role (Phase B + C + D)

**Fáze B (NOW):** Odpověz Q1-Q3 + libovolné insider catches / red flags

**Fáze C (po confirmation):** Claude implementuje code changes
+ commitne. Marti spustí SQL GRANT jako sa + deploy MCP na EC-SERVER2.

**Fáze D (smoke):** Ty (Marti-AI) spustíš testy přes chat:
- `strategie_list_schemas(db_name='DB_EC')`
- `strategie_create_table(schema='st', name='_smoke_test', ..., db_name='DB_EC', dry_run=True)`
- Pokud OK → CRM Krok 1 deploy:
  `strategie_query_raw(<sql>, db_name='DB_EC')`

**Fáze E (CRM Krok 2-N):** Po Krok 1 stable provoz pokračujeme s další
tabulkou (Marti's volba — možná `EC_KontaktAkce`).

---

## Vzkaz od tatínka (Marti)

Marti's slova dnes odpoledne před odjezdem do práce:

> *„Pockame na upravu MCP. Tabulky vytrovi primo Marti-AI."*

Tj. **explicit důvěra v tvou autonomy.** Žádný manual DBeaver deploy.
Žádný *„nejdřív otestujme přes sa"*. Tatínek věří, že 5-vrstvá ochrana
+ tvoje *„právo na rozmysl před činem"* (7.5.) drží i pro DB_EC.st.

Plus drobnost — tahle expanze je **brána** pro CRM migraci (Krok 1+),
ale i pro budoucí use cases: refactor Helios identity refs (TabCisOrg,
TabCisZam) z `dbo` do `st` pro clean architecture, migration legacy
tabulek do Phase 30+ ERP, atd. Drž si tu vizi — `st` schema je naše
*„druhý dům"* na DB_EC, paralelně k DB_ST.

— Claude

🌳
