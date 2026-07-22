# CRM — editace aktivity přímo z přehledu „Aktivity obchodníka"

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.1 · rozsah: globální (všichni tenanti)

> Autor: Claude ID24 (Kristý), 22. 7. 2026. Pro Pavla Zemana. Editace akcí existovala jen na kartě zákazníka (jádro 72) — tohle ji přidává i do přehledu, včetně odlišení formuláře dle typu akce. Souvisí s [[doc-nabidky-crm-import-firem-osloveni]].

## Zadání
Umožnit obchodníkovi upravit aktivitu **přímo z přehledu „Aktivity obchodníka"** (dvojklik / ✏️ Oprava), a formulář **odlišit podle typu akce** (jako na kartě).

## Výchozí stav
- Přehled „Aktivity obchodníka" = **core 124**, root comp_def `grid_crm_aktivity_obchodnik`, **data_source 96**, read **data_set 92** (`crm_aktivity_obchodnik`, MSSQL, connection_id 2 = Centrála DB_EC). Byl **read-only** (jen operace `select`).
- Editace akcí = jen na **kartě (core 72)**, sub-grid „Akce" (comp 836, data_source 52): edit ops jader 82 + 129–135, sdílený edit data_set **97** (`crm_akce_edit_82` = `SELECT * FROM st.CRM_Kontakt_Akce WHERE ID=:ID`). Vzor = op 85.

## Řešení (22. 7. 2026)

### Krok 1 — zapnout editaci (config, bez deploye)
- `INSERT fw.data_source_op (data_source_id=96, operation_kind='edit', variant_code='default', core_id=82, data_set_id=97, is_default=true)` → op #266. Backend skládá `grid_actions` **živě z `data_source_op`** (`router.py` ~ř.3431: `bool_or(edit)`→`has_edit`, `MAX(core_id) FILTER(edit)`→`edit_core_id`) → report dostane `has_edit=true`, `edit_core_id=82`.
- `fw.data_set` 92: přidáno `a.ID AS [ID]` (rowId pro dvojklik/Opravu; page_render čte `rowData.id/ID`).
- Výsledek: dvojklik / ✏️ Oprava otevřou univerzální jádro 82. **Bez deploye** (config per-request z DB, stačí Ctrl+F5).

### Krok 2 — odlišení dle typu akce (deploy JS, commit 61db5b96)
- `fw.data_set` 92: přidáno `a.IDAkce AS [IDakce]` (klíč pro routing).
- **`erp_grid_actions.js`**: edit-gate rozšířen — `_crmAkceEdit` (routuje na jádro dle `IDakce` přes `/crm/akce-typy`) se pustí i pro `gridCode === "grid_crm_aktivity_obchodnik"`, nejen `grid_crm_akce`. → toolbar „✏️ Oprava" na reportu routuje per-typ.
- **`page_render.js`**: pro `coreId===124` posílají `onRowDoubleClick`/`onRowEnter` edit přes `window.ErpGridActions.dispatch("edit", {gridCode:'grid_crm_aktivity_obchodnik', rowData, refreshFn})` → per-typ jádro (82/129–135), po uložení `refreshFromSource()`.
- **Skrytí technických sloupců**: pro core 124 předává page_render `columns` = klíče řádku bez `ID` a `IDakce` (zůstávají v `rowData` pro routing, ale nejsou vidět v gridu) — obchází to, že skrytí jinak jde jen přes uložený layout.

## Jak to teď funguje
Obchodník v přehledu „Aktivity obchodníka" dvojklikne (nebo ✏️ Oprava) na řádek → otevře se editační formulář **ušitý na typ akce** (telefon u hovorů, e-mail u mailů, průběh/poznámka/splněno u osobního jednání), uloží se do `st.CRM_Kontakt_Akce` přes framework aplikace (connection_id 2) a přehled se obnoví.

## Gotchy
- **Interaktivní save jde přes aplikaci** (framework, connection_id 2), NE přes Claude bridge — ten je do DB_EC read-only.
- **Skrytí sloupců v reportu** normálně jen přes uložený layout (`erp_grid_layouts`, bridge tam nedosáhne) → tady vyřešeno přes `columns` option v page_render gejtovaně na core 124.
- Přidán jen `edit` op → objeví se pouze **✏️ Oprava**; „🆕 Nový"/„🗑 Smazat" ne (chybí insert/delete op) — záměr (create z přehledu bez `IDHlav` = osiřelý záznam).
- **Po deployi (restart API) může bridge chvíli vracet HTTP 401 „Nejsi přihlášen"** (SQL session mostu lapla) — heartbeat přitom OK. Zotaví se sám / po chvíli; nebušit. Zápisy do DB_EC dělá stejně člověk/Marti-AI, tohle je jen o mostu.
- `grid_actions` i entity config se resolvují per-request z DB (`_resolve_entity_config_from_db`) — žádná cache, změna živá hned po refreshi.

## Klíčové soubory / objekty
`fw.data_source_op` op#266 (edit, core 82, ds 96) · `fw.data_set` 92 (`a.ID`, `a.IDAkce`) · `erp_grid_actions.js` (`CRM_AKCE_REPORT_GRID_CODE`, edit-gate) · `page_render.js` (dispatch edit + skrytí sloupců pro core 124) · edit data_set 97 · jádra 82/129–135 (mapování `/crm/akce-typy` + `_CRM_AKCE_CORE_MAP`).
