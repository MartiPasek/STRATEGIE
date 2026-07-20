# 📐 STRATEGIE — architektura ve velkém obrázku

> Založeno 20. 7. 2026 (Jirka ID28, `/init`). Drží to, co se **nedá vyčíst z jednoho
> souboru ani z výpisu adresářů** — a co stojí půlhodinu tápání, když to člověk neví.
> Vše ověřeno proti kódu, ne z paměti. Když se něco změní, aktualizuj to tady.
> Konceptuální vrstva (principy, DB vrstvy, tým) žije v `CLAUDE.md`; tady je „jak to
> doopravdy je zapojené".

---

## 1. Tvar repa

Poetry monorepo (`pyproject.toml`, `package-mode = false`, Python `^3.11`). Jedna
FastAPI aplikace, 30 modulů, žádný bundler, žádné CI.

| Adresář | Co drží |
|---|---|
| `core/` | ~10 souborů. Config, crypto, logging, DB engine. Záměrně tenké. |
| `modules/` | 30 doménových modulů. **Velikosti jsou extrémně asymetrické** — `modules/erp/` sám je ~81 000 řádků API kódu, většina ostatních je malá. Fakticky ERP monolit se satelity. |
| `apps/api/` | Jediná aplikace: `main.py` (2 388 ř.) + `static/`. |
| `scripts/` | 25 `.py` + ~197 `.sql` + podadresáře (`claude_sql/`, `dr/`, `bank/`, `jmhz/`, `rozvrh/`…). |
| `docs/` | ~284 souborů — design notes, handoffy, archivy krabičky. |
| `alembic_data/` | Migrace pro jedinou `data_db` (60 verzí). |
| `APP/Mobile/` | Android appka (Gradle). |

---

## 2. Tři cesty k datům — hlavní věc, kterou je třeba držet v hlavě

Rozpoznat, **která cesta zrovna hraje**, je nejdůležitější orientační bod celého repa.

### (a) Aplikace → `data_db` (PostgreSQL)

Existuje **jeden jediný SQLAlchemy engine** — `core/database.py` (49 ř.):

```python
engine = create_engine(settings.database_data_url, pool_pre_ping=True, echo=False)
```

**Pozor na klamavá jména** (Phase 18, 29. 4. 2026 sloučila `css_db` + `data_db`):

- `core/database_core.py` (17 ř.) a `core/database_data.py` (15 ř.) jsou **pouhé alias
  shimy** — reexportují tentýž engine pod legacy jmény (`BaseCore`/`get_core_session`,
  `BaseData`/`get_data_session`). Takže `from core.database_data import get_data_session`,
  které je rozeseté po `main.py` i `router.py`, sahá na **stejnou databázi** jako všechno ostatní.
- `core/database_legacy.py` (38 ř.) míří na `settings.database_url` (testovací DB `strategie`).
  Vlastní docstring říká, že se drží „jen pro nostalgii". **Žádný produkční kód ho nepoužívá.**

Session lifecycle si řídí volající přes `try/finally` — **není** tu FastAPI `Depends` závislost.

### (b) Aplikace → Helios MSSQL

Dvě různé cesty, ne jedna:

1. **Přes MCP** (kancelářský Helios `DB_EC` / `DB_IS`) — volá se tool
   `eurosoft_strategie_query_raw`. Protože to nejde driverem, **parametry se musí
   nasubstituovat přímo do SQL** (`_substitute_mssql_params()` v
   `modules/erp/application/data_source_runner.py:385`). Výsledek nese
   `execution_path: "mcp_mssql"`.
2. **Přímým `pyodbc`** na cloud Helios — `_mssql188_query()` v `modules/erp/api/router.py:37184`.
   **Nenápadná, ale zásadní věc: funkce si přepíše connection string na `DATABASE=MOST`**
   (regex substituce, ř. 37209-37213) bez ohledu na to, co je v `MSSQL188_CONN`.
   `UCTO_EC` / `UCTO_ES` se pak čtou **cross-database** plně kvalifikovanými jmény.
   `MOST` je tedy jediný vstupní bod do cloudového MSSQL. Běží s `autocommit=True`,
   povoluje DDL/DML a vrací `{ok, columns, rows, count}` místo aby vyhazovala výjimku.

**Mapování firma → databáze má jediný zdroj pravdy** — `_FIRMA_DB` v `router.py:33280`
(EC=1 → `DB_EC`/`UCTO_EC`, ES=2 → `DB_IS`/`UCTO_ES`) + `_FIRMA_IDOBDOBI`. Přidání
třetí firmy = jeden řádek tady, ne hon po kódu. Přístup přes `_firma_dbs()`,
`_firma_cloud_db()`, `_firma_src_pfx()`, `_firma_idobdobi()`.

### (c) Claude → produkce (SQL bridge)

`scripts/claude_sql_runner.py` (1 668 ř. — **kód je o úroveň výš, `scripts/claude_sql/`
je gitignorovaná datová schránka**). Poll adresáře → HTTPS POST na
`/api/v1/erp/diag-sql` → provedení na cloudu → výsledek zpět do souboru.
Používá **jen stdlib `urllib`**, aby běžel pod systémovým Pythonem jako LocalSystem
NSSM služba (bez venv, bez DB driverů).

Protokol: `CLAUDE_SQL.sql` (dotaz) + `CLAUDE_GO.txt` (**trigger, zapisuje se JAKO
POSLEDNÍ** — celý concurrency design stojí na tomhle, není tu žádný lock),
volitelně `db=pg|mssql|mssql188|bakalari`. Výstup `CLAUDE_OUT.txt` + `CLAUDE_OUT_FULL.txt`.
Stejný souborový vzor nese i deploy (`CLAUDE_DEPLOY.txt`), notifikace, pull a
mezi-agentní poštu (`MARTIAI_TO_CLAUDE.txt`, `OTHER_CLAUDE_WORK.txt`).

**Cíl `bakalari`** je zvláštní: ze cloudu je nedosažitelný (školní vnitřní síť),
takže se dotaz **zařadí do `fw.bakalari_query`** a konektor na notebooku ho na VPN
vyzvedne, provede a zapíše zpět.

**Zápisová brána** (`router.py:40483+`) — po odstranění komentářů se statement
klasifikuje regexem. Když to není `SELECT|WITH|EXPLAIN|SHOW`:
- zápis projde jen pro `db=pg` nebo `db=mssql`,
- hardcoded sandbox allowlist (`tenant.ucetni_denik`, `tenant.ucetni_denik_log`,
  `tenant.bank_predkontace`) se provede **rovnou, bez schválení**,
- cokoli jiného založí řádek v `fw.claude_write_request`, **pošle push notifikaci na
  telefon** a vrátí `{"ok": false, "pending": true, …}`.

Vše se audituje do `fw.claude_sql_log`; endpoint navíc volá `_require_parent(uid)` —
syrové SQL proti produkci smí jen „rodič".

---

## 3. `apps/api/main.py` — sestavení aplikace

Routery se importují nahoře (ř. 20-55) a registrují v jednom plochém bloku
(ř. 869-907). **28 `include_router` volání**, žádná dynamická discovery — přidání
modulu = editace na dvou místech v `main.py`. Jeden import je schválně odložený
až na ř. 906 (`act_router`) jako obcházka cyklického importu. `main.py` navíc sám
definuje **158 rout**, takže to není čistý assembler.

### Lifespan hook (ř. 67, zapojen na ř. 367) — nosný prvek

Doctrína „lifespan one-off DDL hook" z `CLAUDE.md` je tu **reálně implementovaná**.
Komentář na ř. 196-197 vysvětluje proč: API běží jako PG role `strategie`, která
vlastní `public.*`, kdežto bridge se připojuje slabší rolí. **Owner-only DDL se
tedy propašuje přes start aplikace** — vědomé obcházení Alembicu kvůli právům.

Co lifespan dělá v pořadí: startup telemetrie (vč. `git rev-parse` SHA) → update
`api_version` → **idempotentní DDL bloky**, každý ve vlastním `try/except`, který
při chybě jen loguje (nikdy neshodí start) → gating schedulerů → vault bootstrap.

**⚠️ Detekce sekundární instance jde podle NÁZVU ADRESÁŘE, ne podle env proměnné**
(ř. 288-291):

```python
_is_secondary_ls = ("prev" in _repo_base_ls.lower()) or os.environ.get("STRATEGIE_DR_STANDBY","").strip() == "1"
```

Komentář na ř. 283-286 zaznamenává konkrétní incident: dřívější verze se řídila
podle `STRATEGIE_INSTANCE_NAME`, jenže tu proměnnou nastavuje i primár — a ten si
tím **tiše vypnul vlastní scheduler**. Nesahat bez pochopení.

Na primáru (a jen tam) se startují tři scheduleru: `_att_sync_start` (docházkové
zrcadlo, tick 30 s), mirror scheduler, automat scheduler.

**Logging middleware** (~ř. 790-855) zapisuje 4xx/5xx do strukturovaného logu
s atribucí tenant / user / `core_id` / `comp_def_id` — proto frontend posílá ty hlavičky (viz §5).

---

## 4. `modules/erp/api/router.py` — 61 843 řádků, 632 rout

Zdaleka největší artefakt v repu. Dva routery: `router` (prefix `/erp`) a
`api_router` (prefix `/api/v1/erp`). 1 011 definic funkcí. Zároveň obsluhuje
stránky ERP, CRUD nad framework metadaty, runtime data pro frontend, SQL bridge,
integraci na Helios, CRM, docházku i mzdy.

### 🔑 Kde hledat endpoint — existují DVA extrakční vzory

`router.py` **nemá žádné `include_router`**. Sourozenci v `modules/erp/api/` se dělí na:

1. **Vlastní `APIRouter`, mountnutý přímo na `app` v `main.py`** (novější, čisté):
   `bank_api.py` (3 269 ř.), `iso_cockpit.py`, `contract_sign.py`, `carddav.py`,
   `directories.py`, `mzdy_jmhz.py`, `automat.py`, `g2007_vectors.py`,
   `bozp_cockpit.py`, `hr_spis.py`, `dr_ops.py`.
2. **Jen knihovny helper funkcí**, které `router.py` importuje a volá — **HTTP vrstva
   zůstala v tom 61k souboru**: `kalkulace_engine.py`, `cenik_engine.py`,
   `smernice_rag.py`, `oz_mirror.py`, `core_import.py`, `rfq_draft.py`,
   `centrala_form_spec.py`, `edit_form_binding.py`, `mail_mirror.py`…

**Praktický důsledek:** když hledáš endpoint pro kalkulace nebo zrcadla, **není
v `kalkulace_engine.py` ani `oz_mirror.py`** — je v `router.py`. Grepuj cestu, ne jméno souboru.

Pět souborů nemá ani router, ani referenci z `router.py` (`platak_generator.py` 856 ř.,
`zakazky_analyza.py`, `teamio_replies.py`, `iso_controls_catalog.py`,
`iso_tisax_catalog.py`) — buď se k nim chodí jinudy, nebo jsou mrtvé. Před úpravou ověř.

---

## 5. Frontend — `apps/api/static/`

**Žádný bundler.** Ručně psané ES5/ES6 IIFE moduly, tažené `<script>` tagy přímo
ze `StaticFiles`. Root `package.json` má jen Playwright a stub `test` skript.

Dvě samostatně instalovatelné PWA — root (`manifest.json`, `sw.js`) a ERP
(`erp/manifest.json`, `erp/sw.js`) s vlastní sadou ikon.

### `fw.*` metadata řídí UI

Řetěz: **`fw.core`** (jádro, `code` jako `hr.finance`, `dochazka.opravy`) →
**`fw.comp_def`** (strom komponent s `parent_comp_def_id`, `region_slot`, `layout` JSONB) →
**`fw.data_source` / `fw.data_source_op` / `fw.data_set`** (SQL pod tím,
`db_connection_id` volí databázi podle §2a).

Dispatcher je `erp/components/page_render.js` (975 ř.): fetch
`GET /api/v1/erp/fw-core/{id}/page-spec`, větví se podle
`spec.root_comp_def.type_code` (`grid_modern`/`list` → grid, `form` → formulář,
`drafted` → placeholder), data pak z `/api/v1/erp/data-by-id/{id}` a rozvržení
sloupců z `/api/v1/erp/grid-layout/…`.

### ⚠️ Únikové poklopy — „metadata řídí všechno" má hardcoded výjimky

`_renderDraftedPlaceholder()` (`page_render.js:46+`) speciálně ošetřuje konkrétní
`core_code`. Jádra bez `comp_def` stromu se renderují **jako iframe na ručně psané
stránky**: `hr.finance` → `/finance-podminky`, `dochazka.opravy` → `/dochazka-opravy`,
`hr.karta` → `/karta-zamestnance`; `hr.prehled` se mountuje přes `window.HrPult.mount()`.
**Kdo tohle neví, hledá komponenty, které neexistují.**

Každý modul se obaluje do `global._erpLoadModule(id, version, fn)` (registr + banner
„X/Y modulů načteno"); chyby jdou přes `global._erpLogToDb()` do `fw.diag_log` —
proto backend middleware nese `core_id`/`comp_def_id` (§3). **Frontendové i backendové
chyby končí ve stejné tabulce** s atribucí na konkrétní grid/formulář.

Největší soubory: `components/design_forms.js` (12 807 ř. — vizuální designér samotných
`fw.*` metadat) a `datagrid.js` (5 375 ř. — vlastní grid `window.ErpDataGrid`
v ag-Grid-like tvaru). Řada designérských komponent má **Python zrcadla** v
`modules/fw_components/` — táž komponenta definovaná na obou stranách.

---

## 6. MCP server — `modules/eurosoft_mcp/` (5 015 ř.)

Vystavuje on-premise Helios MSSQL a sdílenou složku. Entry `server.py` (581 ř.),
běží jako `python -m eurosoft_mcp.server` — MCP SDK přes **SSE**, zabalené do
Starlette ASGI s Bearer auth, uvicorn na `127.0.0.1:8765`, Caddy proxuje
`api.eurosoft.com/marti-mcp/*`. Windows služba přes NSSM.

Čtyři jmenné prostory slité do jednoho plochého seznamu (`server.py:56-57`):
`tools.py` (`eurosoft_*`, čtení z `DB_EC`), `strategie_tools.py` (`strategie_*`,
plná doména na `DB_ST` **včetně DDL**), `filesystem_tools.py` (`eurosoft_file_*`),
`ops_tools.py`.

### ⚠️ Rate-limit je svázaný s frontendem

`_classify_action()` (`server.py:84`) řadí volání do bucketů `insert` (~10/min) vs
`read` (~60/min). `strategie_query_raw` byl původně v `insert` — jenže ERP runtime
ho volá **při každém načtení formuláře a nested gridu** (§2b), takže jeden formulář
s vnořenými gridy vystřelil 3+ čtení a shodil zápisový limit (`rate_limit_exceeded`).
Byl proto přeřazen do `read`, zatímco DDL/DML `strategie_*` tooly zůstávají v `insert`
(`server.py:95-101`). **Přímá vazba mezi metadaty řízeným frontendem a throttlem MCP serveru.**

### 🔑 Dvojitý prefix při volání FS toolů

MCP klient (`modules/conversation/application/eurosoft_mcp_client.py`) v
`call_tool_sync` **strhává prefix `eurosoft_`**. FS tooly jsou na serveru
registrované s ním → volej je s **dvojitým** prefixem (`eurosoft_eurosoft_file_list`),
jinak dostaneš `unknown_tool`. Tooly `strategie_*` se volají jako
`eurosoft_strategie_query_raw`.

---

## 7. Dvě cesty ke změně schématu — shrnutí

| Cesta | Kdy | Kde |
|---|---|---|
| **Alembic** | běžné migrace `data_db` | `alembic_data.ini` + `alembic_data/versions/` (60 verzí) |
| **Lifespan DDL hook** | když změna potřebuje `strategie` owner roli, kterou bridge nemá | idempotentní blok v `apps/api/main.py` lifespan; **po nasazení smazat** |

`alembic_core.ini` **v repu není** — README i starší části `CLAUDE.md` ho zmiňují chybně.
