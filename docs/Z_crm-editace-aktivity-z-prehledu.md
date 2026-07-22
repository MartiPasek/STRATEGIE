# CRM — editace aktivity přímo z přehledu „Aktivity obchodníka"

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Autor: Claude ID24 (Kristý), 22. 7. 2026. Pro Pavla Zemana. Doplněk k editaci akcí, která už existovala jen na kartě zákazníka (jádro 72). Souvisí s [[doc-nabidky-crm-import-firem-osloveni]].

## Zadání
Umožnit obchodníkovi upravit aktivitu **přímo z přehledu „Aktivity obchodníka"** (dvojklik / ✏️ Oprava), ne jen z karty firmy.

## Jak to bylo (výchozí stav)
- Přehled „Aktivity obchodníka" = **core 124**, **data_source 96**, read **data_set 92** (`crm_aktivity_obchodnik`, MSSQL, connection_id 2 = Centrála DB_EC). Byl **read-only** — data_source 96 měl jen operaci `select`.
- Editace akcí existovala jen na **kartě zákazníka (core 72)** přes sub-grid „Akce" (comp 836, data_source 52): edit ops 82 + 129–135, všechny přes edit data_set **97** (`crm_akce_edit_82` = `SELECT * FROM st.CRM_Kontakt_Akce WHERE ID=:ID`). Vzor = op 85 (edit, core 82, def).

## Řešení (22. 7. 2026) — konfiguračně, bez zásahu do render-kódu
1. **Zapnout edit na reportu:** `INSERT fw.data_source_op (data_source_id=96, operation_kind='edit', variant_code='default', core_id=82, data_set_id=97, is_default=true)`.
2. **Vystavit rowId v reportu:** do `fw.data_set` 92 přidáno `a.ID AS [ID]` (page_render čte `rowData.id/ID`; bez toho je dvojklik no-op).

Jak to zafunguje: backend skládá `grid_actions` **živě z `data_source_op`** (`router.py` ~ř. 3431: `bool_or(edit)`→`has_edit`, `MAX(core_id) FILTER (edit)`→`edit_core_id`). → report 124 dostane `has_edit=true`, `edit_core_id=82`. `page_render.js` `onRowDoubleClick`/`onRowEnter` + toolbar „✏️ Oprava" otevřou pro vybraný řádek `ErpSpecForm`/`DesignFwForm` (jádro 82), po uložení `refreshFromSource()`.

**Žádný deploy** — config se čte per-request z DB, stačí refresh stránky (Ctrl+F5).

## Editační jádro 82
Default „osobní jednání": pole **Průběh / Poznámka / Informace / Splněno**. Ukládá do `st.CRM_Kontakt_Akce` (WHERE ID) přes **framework aplikace** (connection_id 2). Interaktivní save jde přes aplikaci — **Claude bridge je do DB_EC read-only**, DML tudy nejde.

## Gotchy
- **Skrytí technických sloupců v reportu jde jen přes uložený layout** (`erp_grid_layouts`) — bridge tam nedosáhne. Proto se `ID` v přehledu zobrazí (pinned vlevo); kdo chce, skryje v UI a uloží jako sdílený/výchozí layout.
- Přidání jen `edit` operace zapne pouze **✏️ Oprava**; „🆕 Nový" / „🗑 Smazat" se neobjeví (chybí insert/delete op) — **záměr**: create z přehledu bez `IDHlav` seedu = osiřelý záznam.
- `grid_actions` = per-request z DB (žádná cache) → změna je živá hned po refreshi.

## Follow-up (volitelné) — per-typ formuláře jako na kartě
Aby dvojklik v reportu otevřel formulář ušitý na typ akce (jádra 129–135, ne univerzální 82): přidat na ds 96 stejnou sadu edit ops jako na ds 52 + vystavit `a.IDAkce` v ds 92 + JS routing dle `IDakce` pro core 124 v `page_render` (zrcadlo embedded-grid routingu, `window.ErpGridActions.crmAkceCoreFor`). Zatím univerzální jádro 82 (edit Průběh/Poznámka/Splněno pro všechny typy).
