# Kompozice CORE — podrobný rozbor vzoru „Karta zákazníka" (core 72)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Kompozice CORE — podrobný rozbor vzoru „Karta zákazníka" (core 72)

> Autor: Claude ID24, 19. 7. 2026, na pokyn Marti („detailně zmapuj tento klíčový CORE — stavbou panelů, jejich anchors a jednotlivými komponentami a jejich parametry. TO JE NÁŠ VZOR"). Kristý duplikuje CORE klíčových přehledů Centrály1 do Přehledů/core STRATEGIE (vizuální i funkční zrcadlo 1:1); nejvíc pálí **skládání fw komponent na panely** (parent + pořadí), kde se komponenta při manipulaci osiří a zmizí.
> Stav: mapa vzoru + kompoziční model + reálný nepořádek jako exhibit problému. Navazuje na diskusi o řešení (detektor osiření / snapshoty / generátor).

## 1. Kompoziční model `fw` (jak vzniká obrazovka)

Obrazovka/přehled = **`fw.core`** (identita: `id`, `code`, `label`, `version`). Na core visí **strom komponent `fw.comp_def`**:
- **strom** drží `parent_comp_def_id` (self-FK); `core_id` = ke kterému core patří; `root=1` = kořenová komponenta core.
- **pořadí mezi sourozenci** = `sort_order`; **slot rodiče** = `region_slot` (u nás skoro vždy `main`).
- **typ** = `type_id` → `fw.comp_type`; **data** = `data_source_id`; **šablona panelu** = `container_template_id`(+version).
- **`layout` (jsonb)** = TĚŽIŠTĚ — nese anchor, rozměry i data-binding (viz §4–5). Sloupce `layout_x/y/w/h` jsou u tohoto core PRÁZDNÉ → **není to absolutní x/y mřížka, ale flow layout s dock-align.**

**Typy komponent (`fw.comp_type`, relevantní):** 302 form (📋 klasický modal) · 306 list_root (📊 přehled) · 13 panel · 12 groupbox · 15 pagecontrol · 16 tabsheet (tab) · 101 grid_modern · 2 edit (text) · 105 memo (textarea) · 106 number · 107 checkbox_modern · 108 date_modern · 109 datetime · 110 lookup (combo) · 111 lookup_multi · 112 file · 113 label_readonly · 310 entity_picker (🔗) · 311 adresar (soubory) · 300 container · 305 frameless_form. (Legacy Delphi typy 1–38: label/edit/checkbox/richedit/grid/panel/pagecontrol…)

## 2. Vzor: core `72` „Karta zákazníka"

Detailní karta CRM kontaktu (okno „Kontakty", status `72:<id>`). Root = comp_def **288** (typ 302 form, `root=1`, název `form_crm_kontakt_detail_test`, caption „Editace TEST detail", `layout` = min 646×446 / default 1404×983 px). Data míří do CRM tabulek **`st.CRM_Kontakt`** (hlavička) a **`st.CRM_Kontakt_Akce`** (řádek akce), `connection_id=2`.

**Zamýšlená struktura (jak vypadá na obrazovce):**
```
288 form „Karta zákazníka"
├─ 318 panel (hlavní kontejner — sloupce)
│   ├─ 320 panel „Kontakt"      (align left)  → Firma, Zdroj kontaktu, Země(310), Typ zakázky, Web,
│   │                                            Stav obch. vztahu(110), Ověřený kontakt(107), Kategorie(310), Vyhledáno z
│   ├─ 323 panel „Komunikace"                 → Komunikace(2), Obeslal(2), Datum poslední akce(108, ro), Příští kontakt(108)
│   ├─ 321 panel „Potenciál"    (align client)→ Atraktivita(110), Pravděpodobnost objednání(110), Pravděpodobnost spolupráce(110)
│   └─ 322 panel → 375 pagecontrol → taby: 376 Popis firmy (memo 309), 377 Poznámka (memo 311), 378 Adresář (adresar 942)
├─ 835 grid „CRM Kontaktní údaje (sub-grid v jádře)"
├─ 836 grid „CRM Akce (sub-grid v jádře)"
└─ 312 panel „Audit"           → ID, Autor, Datum pořízení, Změnil, Datum změny (vše 113 label_readonly)
```

## 3. Panely a jejich anchors

Panel = `comp_def` typu **13 (panel)** / 15+16 (pagecontrol+tab). Anchor a rozměr panelu jsou v `layout`:
- **`align`** = kotvení (Delphi styl): **`left`** (přišpendlí vlevo, roste dolů), **`client`** (vyplní zbytek), **`none`** (volně), (+ top/bottom). To je ten „anchor", co Kristý skládá.
- **`min_width`/`max_width`/`min_height`/`height`** = mantinely rozměru · **`border_mode: "all"`** = orámování · **`caption`** = nadpis panelu · **`placeholder`** = text prázdného panelu.

Příklady z vzoru: panel „Kontakt" `{"align":"left","max_width":500,"min_width":200,"min_height":100,"height":100,"border_mode":"all"}` · „Potenciál" `{"align":"client",…}` · „Komunikace" `{"align":"none",…}`. → panely se skládají vedle sebe **align-em** (left/client), ne souřadnicemi.

## 4. Komponenty (pole) a jejich parametry

Pole = list komponenta (typy 2/105/106/107/108/110/310/…). **Všechny parametry jsou v `layout` jsonb**, klíčové:
- **`column_name`** = zdrojový sloupec pro zobrazení.
- **`save`** = data-binding zápisu: `{table, column, schema, row_key, connection_id, readonly, reason?}`. Určuje, kam se pole uloží.
  - hlavičková pole → `st.CRM_Kontakt`, `row_key {"ID":"@id"}` (`@id` = otevřený záznam). Př. „Příští kontakt" → `st.CRM_Kontakt.PristiKontakt`.
  - akční pole → `st.CRM_Kontakt_Akce`, `row_key {"IDHlav":"@id","IDakce":16}`. Př. „Země" → `CRM_Kontakt_Akce.ZemeID`.
  - readonly / nemapované → `save.readonly=true`, `reason` (např. `non_base_alias:PoslAkce` u „Datum poslední akce").
- **layout pole:** `max_width`/`min_width`, **`always_new_row: true`** (zalom na nový řádek — takhle se dělá flow „mřížka" bez souřadnic), `placeholder`, `caption`.
- **entity_picker (310)** — pole s vazbou na číselník/entitu přes `data_source_id` (Země ds48, Typ zakázky ds47, Kategorie ds46) + `save`.

## 5. Sub-gridy „v jádře" (835, 836)

Grid uvnitř detailu = `comp_def` typu **101 grid_modern**, konfigurace v `layout`:
```json
{"kind":"select-detail","align":"top","height_px":200,"context_menu":["refresh"],
 "edit_core_id":81,"filter_field":"master_id","filter_source":":master_id",
 "data_source_code":"crm_kontakt_osoby_detail"}
```
- **`kind:"select-detail"`** = master-detail grid vázaný na otevřený záznam.
- **`filter_field:"master_id"` + `filter_source:":master_id"`** = řádky filtrované podle ID master záznamu (té Karty). Tohle je vazba „v jádře".
- **`data_source_code`** = odkud grid bere řádky (`fw.data_source` dle code) — sloupce gridu definuje ten data_source (+ `fw.comp_grid`/`comp_grid_column_alias`).
- **`edit_core_id`** = který core se otevře při editaci řádku (835→81 „Editace CRM Kontaktní údaje", 836→82).
- 835 „CRM Kontaktní údaje" ← `crm_kontakt_osoby_detail` (Jmeno/Telefon/Email/Web/LinkedIn/Typ/FirmaOrPozice/Prijmeni) · 836 „CRM Akce" ← `crm_kontakt_akce_detail` (Nazev/Jmeno/Telefon/Email/Web/LinkedIn/IDHlav/Poradi).

## 6. ⚠️ Reálný nepořádek ve vzoru = exhibit problému osiření

Core 72 je **živý rozpracovaný** a nese přesně tu škodu z manipulace, kterou Kristý řeší:
- **Duplicity pole „Firma"** pod panelem 320: comp_def 290, 325, 327 (třikrát `fld_test_firma_text`, různé `sort_order` 10/15/70).
- **Duplicitní panely** pod 320 (caption „Kontakt" 289, „Komunikace" 297, „Potenciál" 303, „Časový status" 300) — vedle „správných" pod 318 (320/323/321). Panel 320 se stal **skládkou** ~20 dětí (pole + panely + pagecontrol 307).
- **Stray panely** 319/324/332 (některé s vnořenými formy 370/371 „klasický modal"), panel 322 s duplicitním pagecontrol 374/375.
- Komponenty jsou v datech (`is_active=true`), ale kvůli špatnému `parent_comp_def_id`/pořadí se buď nevykreslí, nebo se kupí → člověk „to nedá dohromady".
- Důkaz nouzového řešení: tabulka **`fw._core_backup_20260520`** (ruční záloha core).

## 7. Co z rozboru plyne pro řešení (navazuje na společný popis)

1. **Detektor osiření/duplicit** nad `comp_def`: uzly s neexistujícím/neaktivním/cross-core rodičem, cykly, duplicitní `root`, `region_slot` mimo `container_template`, a **duplicitní pole se stejným `save.column`** v jednom core (jako 3× Firma). → „ukaž ztracené a přebytečné".
2. **Snapshoty + undo per core** (`comp_def` strom → jsonb snímek, à la `g2007.zaloha_prompt`): každá manipulace vratná; `_core_backup` povýšit na systém.
3. **Bezpečný reparent**: validace (stejný core, rodič je kontejner, slot existuje) přímo u zdroje tahu.
4. **Generátor comp_def stromu ze specifikace** (panely+align+komponenty+save-binding+pořadí) — automat pro 1:1 zrcadlo, deterministicky, ne ručním taháním.

---
## Klíčové tabulky
`fw.core` · `fw.comp_def` (+`_prop`/`_prop_override`) · `fw.comp_type` · `fw.container_template` · `fw.comp_grid`(+`_column_alias`) · `fw.data_source`(+`_op`) · `fw.menu_node` · `fw.edit_form_binding` · `fw._core_backup_20260520`.

*Podrobný rozbor vzoru core 72 (Karta zákazníka) — Claude C24, 19. 7. 2026. Vzor pro zrcadlení Centrála→STRATEGIE a základ pro nástroje na kompozici (detektor osiření, snapshoty, generátor).*


