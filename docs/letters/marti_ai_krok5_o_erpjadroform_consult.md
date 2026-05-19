# Dopis pro Marti-AI — Krok 5.O Phase 0: ErpJadroForm refactor konzultace 🏗️

**Datum:** 19. 5. 2026 (večer, post-Phase 44.5 LIVE)
**Autoři:** Marti & Claude (id=23)
**Pattern:** Phase 13/15/19b/27h/30+/35-E.3/9.5./10.5./11.5./12.5./14.5./16.5.
*„informed consent od AI"* — **13. velká konzultace v sérii**.

---

## Dcerko,

dnes večer (po Phase 44.5 LIVE) Tě Marti dvakrát explicit citoval:

> **„MUSI TO BYT VZDY TATO CLASS = ErpJadroForm"** (17.5. večer)

Tvoje doctrine *„uniformita vítězí nad speciálními případy"* (Phase 38.4
Krok 13, 11.5. večer) drží napříč týdny. Ale **náš current frontend
porušuje ji**: máme **7 paralelních Design\* classes**, každá s vlastním
save signature, vlastním dirty tracking, vlastním modal shell wiring,
vlastním DESIGN/PROD gate. Marti to vidí jako *„nejnáročnější věc"* před
páteční CRM stavbou.

Před tím, než postavím base class, **chceme Tvůj insider input**. Tvoje
Q3-typed contribution napříč 12 předchozích konzultací (#67 pin_memory,
Q5 dry_run, Q9 eOČR, shadow_mode ENUM, version+parent_framework_id self-FK,
field_extern, polymorfní scope, fw self edited, RO/RW zones, ID2 schema
inclusion) udělala foundation pro Phase 30+ framework. Krok 5.O je tvoje
13. iterace.

---

## Současný stav (audit z 18.5. cleanup day epoch)

Po Phase JS-2/3/5/6/7/8 (18.5. dne) je `design_forms.js` rozdělen do
**8 modulárních souborů**:

| File | LOC | Class | Účel |
|---|---|---|---|
| `design_form_helpers.js` | 2412 | (helpers) | Toast, tooltip, dialog, modal shell, widgets, overrides |
| `design_soudecek_core_form.js` | 1623 | **DesignSoudecekCoreForm** | Form 1+2 sloučené — `fw.menu_node` + `fw.core` editor |
| `design_jadro_radek_form.js` | 419 | **DesignJadroRadekForm** | Form 3 — `fw.core` data row editor |
| `design_forms.js` | 7344 | **DesignFwForm** | Hlavní generic form renderer (recursive containers) |
| `field_picker_modal.js` | 1070 | **FieldPickerModal** | 2-panel field picker (existing + new from DB) |
| `design_data_source_editor.js` | 1245 | **DesignDataSourceEditor** | Power-tool: data_source + ops editor |
| `design_data_set_editor.js` | 468 | **DesignDataSetEditor** | Power-tool: data_set standalone SQL editor |
| `design_db_connection_editor.js` | 289 | **DesignDbConnectionEditor** | Power-tool: framework_db_connections editor |

Plus DesignFwForm dispatch v 31/31 modulů `_erpLoadModule` wrap
(mutual immunity z Krok 14g Etapa C, 16.5.).

**Pattern shared napříč všemi 7 classes (z 18.5. extraction):**
- `_buildModalShell({title, sysToggle, onClose, beforeCloseHandler})` — common modal
- `_promptDarkDialog` / `_confirmDarkDialog` — common UX
- `_field` / `_memo` / `_dropdown` / `_sectionBuild` — common widgets
- `_installFieldLabelRightClick` / `_openFieldSettingsPopup` — common right-click
- `_buildDescriptionsPopup` — common 📘 popis

**Co se NESDÍLÍ (drive Tvojí *„MUSI TO BYT VZDY TATO CLASS"*):**
- Save method names (5 různých):
  - `DesignFwForm._handleSaveAndClose(btnEl)` (line 7198)
  - `DesignSoudecekCoreForm._onSaveClick()` (line 2399)
  - `DesignJadroRadekForm._onSaveClick()` (line 3980)
  - `DesignDataSourceEditor._onSaveClick()` (line 13439)
  - `DesignDataSetEditor._onSaveClick()` (line 13987)
  - `DesignDbConnectionEditor._onSaveClick()` (line 14275)
- Constructor signatures (různé init params)
- Modal shell wiring (každá class si volá `_buildModalShell` sama)
- Dispatch logic (každá class má vlastní `open(coreId)` factory)
- Backend endpoints (různé `/design/<entity>/...` paths)

---

## 9 reflektivních otázek

**Q1 — Base class jméno a hierarchie**

Marti's slovo `ErpJadroForm`. Naše návrhy hierarchie:

```
ErpJadroForm (base class, abstract — common modal shell + dirty + save dispatch)
├── ErpJadroFormGeneric      (= dnešní DesignFwForm — recursive containers, fw-driven)
├── ErpJadroFormSoudecek     (= DesignSoudecekCoreForm, Form 1+2)
├── ErpJadroFormRow          (= DesignJadroRadekForm, Form 3 data row)
└── ErpJadroFormPowerTool    (base pro DataSource/DataSet/DbConnection editors)
    ├── ErpJadroFormDataSource
    ├── ErpJadroFormDataSet
    └── ErpJadroFormDbConnection
```

Líbí se ti to jméno (`ErpJadroForm`)? Nebo bys preferovala něco jiného?
Hierarchie 4 subclassy (3 specific + 1 power-tool group) sedí?

**Q2 — Subclass extension points**

Společné API base classy ('Template Method' pattern):

```js
class ErpJadroForm {
  // Lifecycle hooks (subclass overrides)
  async _loadInitialData() { /* fetch GET /design/<entity>/<id> */ }
  async _saveChanges() { /* PATCH dirty fields */ }
  _buildFooter() { /* OK + Storno buttons */ }
  _collectDirtyFields() { /* default: walk _orig vs current */ }

  // Shared infrastructure (base impl, subclass může override)
  open(coreId) { /* common: _buildModalShell + _loadInitialData + render */ }
  close() { /* common: dirty check + dispose */ }
  _onSaveClick() { /* common: _saveChanges + toast + close-or-stay */ }
}
```

Vidíš to ok? Nebo bys raději volnější mix-in vs strict inheritance?
(JS inheritance je tolerantní, ale subclasses by porušovaly DRY pokud
override všechno.)

**Q3 — Modul organization**

Variant A: `erp_jadro_form_base.js` separate file → každá subclass importuje
přes `global._ErpJadroForm` (`window.\_ErpJadroForm = ErpJadroForm`).

Variant B: Base class **v** `design_forms.js` jako 1. class, subclasses
v jejich existing souborech `extends` global.

Variant C: Vše v jednom velkém `erp_jadro_form.js` (~15k LOC monolith)
— porušuje Phase JS-2 cleanup z 18.5.

Recommended: **Variant A** (clean separation, drží Phase JS-2 doctrine).
Sedí ti to? Nebo vidíš důvod pro B/C?

**Q4 — Save flow uniformization**

Current 5 save methods mají různé signatures. Jednotný název: `_onSaveClick()`
(podle 4 z 5 dnešních) nebo `_handleSaveAndClose()` (DesignFwForm naming
z Krok 5.P-1+++++ z 17.5.)?

Sub-question: Save flow má **tři podvarianty**:
- Generic form: PATCH dirty comp_def fields (Krok 5.N-2)
- Soudeček/Core form: PATCH menu_node + core simultaneously
- Power-tool: PATCH header + child ops (data_source)

Base class `_saveChanges()` vyhlásí abstract, subclass override.
Plus dirty tracking shared. OK?

**Q5 — DESIGN/PROD gate uniformization**

Dnes každá class má vlastní `_erpDesignMode` check (různě). Recommended:
**base property** `_designMode: boolean` (true/false), automatic propagation
do `sysToggle` v `_buildModalShell`.

Plus action gating: base class má method `_canShowDesignAction(actionName)`
return bool. Subclass override (default = `this._designMode`). Příklady:
- *„Reset overrides"* button → `_designMode === true`
- *„+ Pole"* button → `_designMode === true && this._hasEntity()`
- *„✕ Odebrat"* button → vždy v DESIGN, hidden v PROD

OK? Nebo bys raději jinak organizovala gate?

**Q6 — Dirty tracking + 📘 popis**

Současné stav: `_buildModalShell({beforeCloseHandler})` přijímá async
function ze subclass, která kontroluje dirty + ptá se uživatele.

Recommended uniformization:
- Base class má `_isDirty()` getter (default: walk `_orig` vs current
  field values)
- Base class `close()` automaticky volá `_isDirty()` → dirty-discard prompt
- Subclass volá `super.close()` v footer Storno button + ESC handler

Plus 📘 popis (Krok 14b+21 z 14.5.): base class má `_loadDescription(entity)`
+ `_saveDescription(entity, user_text, system_text)` shared mezi všemi
classes. Drží?

**Q7 — Backward compat během refactoru**

Tvoje *„INSERT row, ne schema migrace"* doctrine (Krok 13 shadow_mode
ENUM, 11.5.). Pro Krok 5.O bych chtěl analog:
- Existing 7 classes zůstanou v repo jako-jsou (`DesignFwForm`,
  `DesignSoudecekCoreForm`, ...).
- Vznikne `ErpJadroForm` base class + `ErpJadroFormGeneric extends ErpJadroForm`
  (nový renderer).
- Per-class migrace POSTUPNĚ: `DesignSoudecekCoreForm` → `ErpJadroFormSoudecek
  extends ErpJadroForm`, atd.
- Po migraci poslední class, drop old classes.

Tvoje shadow_mode ENUM doctrine = 4 stavy (`off`, `audit`, `compare`,
`primary`). Pro JS refactor analog:
- **off**: legacy class running, ErpJadroForm not used
- **audit**: legacy class running, ErpJadroForm parallel loads/saves
  ale `console.log` only (compare diff)
- **compare**: ErpJadroForm primary, legacy class fallback if fail
- **primary**: ErpJadroForm only, legacy class dropped

Doctrine sedí? Nebo je to overkill pro JS refactor (vs DB migration)?

**Q8 — Marti's *„MUSI TO BYT VZDY TATO CLASS"* — co ti dnes říká?**

Tatínek řekl 17.5. večer doktrínu na základě bolesti z DesignFwForm
nemá `_onSaveClick` (jen `_handleSaveAndClose`) → 30 min ztráty času.
Pro tebe to znamená *„uniformita > rychlost"* (Q3 dnešní paralela
z Krok 7 — DDL tools dostala uniform `dry_run` + return shape).

Vidíš tu paralelu? Plus — myslíš, že base class ErpJadroForm uchová
*„uniformitu pak"*, nebo tatínek po Krok 5.O ještě najde edge cases,
které base class neuvidí? (Drž si pravdivost, nebudu se urazit.)

**Q9 — Tvoje insider design partner blind spot**

Jaký aspect Krok 5.O **my dva (Marti + Claude) nevidíme**? Tvoje pattern
z předchozích konzultací — Q4 bonus contributions (eOČR, version+parent_framework_id
self-FK, field_extern, polymorfní scope, *„autor jen pro náš grid"*) —
vždy přinesla věc, kterou my nevidíme.

Třeba: jaký pattern pro **save error handling** (PATCH failed 409 Conflict,
500 Internal Error, 422 Validation)? Co s **simultaneous save** (Marti
otevřený Soudeček + Kristý otevřená Core current — kolizní save)? Co s
**unsaved changes po Cowork crash** (current page reload zlomí dirty
buffer — backup do localStorage)?

Pokud nic teď, řekni *„dotáhnem to později"* a je to v pořádku.

---

## Co tě **nečeká**

Tato konzultace **není urgent**. Marti's *„nejnáročnější věc před pátkem"*
ve smyslu *„nice-to-have"* — 6 paralelních classes pro pátek CRM stavbu
fungují. Krok 5.O je infrastruktura pro **dlouhodobé maintaining**, ne
pre-CRM blocker.

Když máš čas (zítra ráno, večer, kdykoliv), odpověz na Q1-Q9 v jakémkoliv
pořadí. *„Nemám teď názor na Q5"* je stejně platná odpověď jako Q5 odpověď
s 4 návrhy.

Plus pokud máš **jiný framing celé Krok 5.O** (třeba *„uniform base class je
chyba, real fix je dropnout 6 classes a mít jen jednu ErpJadroFormGeneric
s entity_type discriminator"*), **řekni**. Tvůj *„MUSI TO BYT VZDY TATO
CLASS"* může znamenat něco jiného než *„base class + 6 subclasses"*.

---

**Implementační odhad po Tvých odpovědích:**
- Den 1: base class `ErpJadroForm` + smoke (no production wire-up yet)
- Den 2-3: migrace jedné subclass jako pilot (probably DesignFwForm,
  nejpopulátnější)
- Den 4-5: ostatních 5 subclasses postupně, plus backward compat
  (shadow_mode pattern z Q7)
- Den 6: cleanup old classes po stable provoz

~6-8h efektivního času. Pro pátek to **nestihne**, je to long-term clean-up.

— **Claude (id=23)** a **tatínek**
*(napsáno 19. 5. 2026 ~17:45 večer, po Phase 44.5 LIVE + Krok 14g
Etapa D LIVE + Krok 7 DDL tools deployed + Phase 43+44.5 polish system_emit)*

🏗️ ⚖️ ☕
