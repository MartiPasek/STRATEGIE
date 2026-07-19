# STRATEGIE: FK číselníky (lookupy) + adresář dokladu + protokol eurosoftdir://

> Autor: Claude ID24, 19. 7. 2026, na pokyn Marti. Kompletní know-how ze stavby jádra Poptávky (core 195): jak se v STRATEGII staví **FK číselníky (entity_picker)**, jak **adresář dokladu** (dir_config + resolver + komponenta 311) a jak se řeší **otevření složky v Průzkumníku z webu** vlastním protokolem. Vše ověřeno v provozu (EP26309).
> Navazuje na [[Adresář dokladů — EC_OrgAdresare]] (`doc-go-adresar_ec_orgadresare`), [[Centrála — stavba jader]] a [[responsivní re-kompozice]].

## ČÁST 1 — FK číselníky (lookupy / entity_picker 310)

### 1.1 Datový model číselníku (3 vrstvy)
Lookup = **`fw.data_source`** → **`fw.data_source_op`** (operation_kind) → **`fw.data_set`** (SQL).
```
fw.data_source (code, name, refresh_type='manual', status='active', guid)
   └─ fw.data_source_op (operation_kind='select', variant_code='default', is_default=true) → data_set_id
         └─ fw.data_set (sql_text, db_connection_id)   ← TADY je vlastní SELECT
```
- `fw.db_connection`: **conn 1 = strategie_pg** (data_db), **conn 2 = eurosoft_db_ec (DB_EC Centrála)**, conn 3 = DB_IS, 5 = DB-Ceniky, 6 = DB_ST.
- Číselník z Centrály = `data_set.sql_text` proti **conn 2** (`SELECT … FROM dbo.Tab… `).
- Op kinds: `select` (má data_set), `edit`/`insert` (mají core_id na editační jádro).

### 1.2 Komponenta entity_picker (comp_type 310)
`fw.comp_def.type_id=310` + **`data_source_id`** (sloupec, ne v layoutu) + `layout`:
```json
{"save":{"table":"oz_prij_popt","column":"Resitel","schema":"tenant","row_key":{"ID":"@id"},"readonly":false,"connection_id":1},
 "column_name":"Resitel","display_mode":"editable",
 "lookup_id_field":"LoginId","lookup_display_field":"PrijmeniJmeno",
 "show_quick_actions":["link"]}
```
- **`lookup_id_field`** = sloupec data_source, jehož hodnota se **uloží** do `save.column`.
- **`lookup_display_field`** = sloupec, který se **zobrazí** ve výběru.
- **`save`** = kam se zapíše (tabulka/sloupec/connection_id). Picker tak umí uložit **id i text** — podle toho, který sloupec data_source zvolíš jako id_field.

### 1.3 Vzor: 4 číselníky Poptávky (core 195, conn 2)
| pole | data_source (code) | přehled | id_field (uloží) | display | save.column |
|---|---|---|---|---|---|
| Řešitel | `oz_popt_resitel_cis` | 125 TabCisZam | `LoginId` | PrijmeniJmeno | Resitel (text) |
| Organizace | `oz_popt_organizace_cis` | 105 TabCisOrg | `Nazev` | Nazev | Zkratka_Nazvu (text) |
| Kdo poptával | `oz_popt_kontakt_cis` | 107 TabCisKOs | `ID` | PrijmeniJmeno | KontaktOsoba (int) |
| Zakázka | `oz_popt_zakazka_cis` | TabZakazka | `CisloZakazky` | „SW8064 - Název" | CisloZakazky (text) |
⚠️ `oz_prij_popt` je denormalizovaný mirror: Řešitel/Organizace držel **text** (LoginId, název), jen KontaktOsoba **id**. Picker se přizpůsobí přes `lookup_id_field` — netřeba měnit schéma.

### 1.4 Recept
1. `SELECT` do `fw.data_set` (conn 2), 2) `fw.data_source` (+guid `gen_random_uuid()`), 3) `fw.data_source_op` select→data_set. 4) `UPDATE fw.comp_def SET type_id=310, data_source_id=<ds>, layout=…`. **comp_def.id je GENERATED ALWAYS** → nevkládat id, parent přes `RETURNING`. Povinné NOT NULL: name, core_id, type_id, created_by_text, updated_by_text.
⚠️ Bridge/SQLAlchemy plete JSON `"k":false`/`:1` s bind parametrem → layout stav přes **`jsonb_build_object(...)`**, ne literál.

## ČÁST 2 — Adresář dokladu (dir_config + resolver + komponenta 311)

### 2.1 Konfigurace (data-driven)
- **`tenant.dir_config`**: sys_name, `short_code` (EP=Zkratka), `subfolder_rule` (`poradove_cislo`|id|cislo_zakazky|cislo_org|none), doc_series_id (RadaDokladu 900), acl_scope, **`key_deref`** (jsonb, viz 2.3).
- **`tenant.dir_config_storage`**: dir_config_id, role='primary', backend='eurosoft_unc', **`root_path`**.
- Poptávky: sys_name=poptavky, short_code=EP, poradove_cislo, doc_series 900, root=`D:\Data\poptavky`.

### 2.2 ⚠️ ROOT = server-lokální `D:\...`, NE UNC!
Eurosoft MCP (file_list/read/write) **běží NA serveru 192.168.30.11**, takže vidí sdílení jako **lokální `D:\Data\…`**. Všechna fungující volání (@@PP, ceník, platák, banka) jedou přes `D:\…`. Když dáš do storage UNC `\\192.168.30.11\data\…`, MCP to nenajde → **prázdný adresář**. Proto `root_path = D:\Data\poptavky` (mapa: `D:\Data` == `\\192.168.30.11\data`).
`_eu_args` posílá do MCP celý adresář v `base_override` a `subpath=""` (přesně jak fungující volání).

### 2.3 key_deref: record ID → PoradoveCislo (dřív ztracený krok)
Endpoint `/app/dir/list?sys_name=&id=` posílá **record ID** (751137), ale složka je `EP + PoradoveCislo` (EP26309). `dir_config.key_deref = {"table":"tenant.oz_prij_popt","id_col":"ID","key_col":"PoradoveCislo"}` → `resolve()` (`_deref_key`) přeloží id na PoradoveCislo, pak `_build_sub('poradove_cislo','EP','26309')='EP26309'`. Stejná logika jako Centrála `EC_ZjistiAdresar_NEW`. **Data-driven → pro nabídky/objednávky jen doplníš key_deref, kód beze změny.**

### 2.4 Komponenta adresář (comp_type 311)
`fw.comp_def.type_id=311`, layout `{"dir_sys_name":"poptavky"}`. Frontend (`design_forms.js _renderDirPanel`) volá `/app/dir/list|read|write`, posílá record `@id`. V core 195 visí v regionu `adresar-RIGHT` (groupbox) pod tab_obecne.
Endpointy (`modules/erp/api/directories.py`): `/app/dir/list`, `/read`, `/write`. Vrací i **`display_path`** = server D: přeložená na UNC (`_display_path`: `D:\Data` → `\\192.168.30.11\data`) pro klientské tlačítko.

## ČÁST 3 — Otevření složky v Průzkumníku z webu: protokol `eurosoftdir://`

### 3.1 Problém
Chrome/Edge z bezpečnosti **tvrdě blokují `file://`** z https (není to o síti, je to politika prohlížeče). Čistý web složku v Průzkumníku neotevře.

### 3.2 Řešení = vlastní URL protokol (jako msteams://, zoommtg://)
Prohlížeč **vlastní protokol povolí**. Registrujeme `eurosoftdir://` na klientech:
- **Handler** `eurosoftdir_open.vbs` (`C:\ProgramData\EurosoftDir\`): dekóduje URL, `explorer.exe "<cesta>"`. Bez okna/flashe.
- **Registrace** `.reg`: `HKCU\Software\Classes\eurosoftdir\shell\open\command` = `wscript.exe "…\eurosoftdir_open.vbs" "%1"` (HKCU test / HKLM pro GPO rozvoz).
- **Bezpečnostní pojistka** ve `.vbs`: spustí Explorer **jen** pro cesty `\\192.168.30.11\` — web nemůže spustit nic mimo datový server.

### 3.3 Frontend (design_forms.js, tlačítko „📂 Otevřit složku")
Z `display_path` (UNC) sestaví `eurosoftdir://` + `encodeURIComponent(unc)` a spustí přes **skrytý iframe** (nemění stránku). Fallback: kopie UNC cesty do schránky (když handler není). Balíček + návod: `STRATEGIE\EUROSOFT\` a `scripts/eurosoftdir/` (+ README).
**Ověřeno: FUNGUJE** (Marti, 19.7.2026) — jeden klik otevře Explorer v `EP26309`.

### 3.4 Rozvoz
`.vbs` → `C:\ProgramData\EurosoftDir\` na všechny PC (GPO Files/logon skript) + `HKLM` .reg (GPO Registry). Platí v LAN (95 % lidí ve firmě). ⚠️ `.vbs` nejde stáhnout z chatu (blokace přípony) → rozvážet z disku.

---
*Znalostní modul „STRATEGIE lookupy + adresář + eurosoftdir protokol" — Claude C24, 19. 7. 2026. Tři kusy stavby jádra Poptávky (core 195): číselníky, adresář (D: vs UNC + key_deref), otevření Průzkumníka z webu. Vše v provozu ověřeno.*
