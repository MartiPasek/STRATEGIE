# Centrála 1 source analysis — reference pro Phase C+

**Datum:** 9. 5. 2026
**Source:** `D:\Projekty\STRATEGIE\_external\centrala1\` (junction → `D:\Projekty\EC_Centrala_XE`)
**Účel:** Reference pro Phase C edit pipeline (#34) + Phase A+1b Object Inspector (#108) + Phase 30+ migration framework.

> **Poznámka:** `_external/` je v `.gitignore`. Source je read-only working copy od kolegy Marti's, slouží jen jako reference pro architectural patterns. Neportujeme 1:1 — extrahujeme principy a mapujeme na STRATEGIE.

---

## 1. Inventář projektu

**Rozsah:**
- 342 .pas (Pascal units, business logic + UI handlers)
- 114 .dfm (form designer files, layout meta)
- 4 .dpr/.dproj (project entry points)
- 10 .INC (compile-time includes)
- 1 .groupproj (build group)

**Stack:**
- Delphi RAD Studio 10.3.3 (z `C:\Libraries RAD 10.3.3\delphi-neon-master\`)
- VCL framework (Windows-only); FMX port začat ale nedotažen (`EC_FmxJadro.dpr` v `EC_Components/source/`, `EC_Default_FMX/`)
- DB layer modernizovaný: `EC.DB.Connection`, `EC.DB.DataSet`, `EC.DB.MemTable` namespace pattern
- 3rd party: Neon (JSON), Pdfium (PDF), MadExcept (crash), Synapse (HTTP/SMTP), TMS components, JvJans
- MQTT real-time: `dmMQTTListener`, `_dmMQTT` (conditional CENTRALA build)
- Conditional compile `{$IFDEF CENTRALA}` — same source for Centrala + EC_Update + EC_EmailGenerator

**Project group:** `EC_Centrala.dproj` (main) + `EC_EmailGenerator.dproj` + `EC_Update.dproj` (latter chybí v `<ItemGroup>` — incomplete merge).

---

## 2. Klíčové units pro Phase C edit pipeline

### `uECCustomDynamicForm.pas` (~600 LOC) — **HLAVNÍ blueprint**

Abstract base class pro **všechny dynamicky generované formuláře**. Lifecycle:

```
SetIDForm(id)
  → load EC_FormDef row (SQL: SELECT * FROM EC_FormDef WHERE ID=:ID)
  → init FDataSet, FUtility, Help, FFDConnection

ShowModal()
  → FDataSet.SQL.Text = FormDef.SQL_Select
  → bind ParamP0/P1 nebo BindingParameters(ParamSourceDataSet)
  → FDataSet.Open
  → if IsEmpty → Insert (auto-create empty row)
  → FEditMode = GetEditMode (per-row dynamic z EC_FormDef.EditModeCondition SQL)
  → set Top/Left/Width/Height z FormDef
  → FUtility.LoadActions(self, 'FormCreate')   ← user-defined hooks
  → FUtility.init                              ← runtime build dynamic UI components

FormShow
  → ULog.Log(1, ...) start
  → FUtility.LoadActions(self, 'FormShow')
  → FUtility.initGrids
  → set ActiveControl na FocusedComponent

User edits...
  → FDataSet.State changes to dsEdit / dsInsert

btnOkClick
  → AkceOk = FUtility.LoadActions(self, 'BeforeOK')   ← validation hook
  → if AkceOk:
    → FOnOkClick callback
    → FDataSet.SafePost                              ← custom post-with-error-catch
    → Database.RemoteConnection.Commit               ← transaction commit
  → if no error → ModalResult := mrOk

btnStornoClick
  → ModalResult := mrCancel
  → Database.RemoteConnection.Rollback              ← transaction rollback

FormClose (X button)
  → if SizeCtrl active → ask Save Layout?
  → if FDataSet dirty → ask Save/Cancel/KeepOpen
  → FUtility.LoadActions(self, 'FormClose')
```

**Klíčové vzory pro STRATEGIE Phase C port:**

| Centrála 1 | STRATEGIE port (Phase C+) |
|---|---|
| `LoadActions(form, 'BeforeOK')` returns bool | Server-side hook chain — tabulka `master.framework_action` (event_name, action_kind, payload JSONB) |
| `Database.Commit/Rollback` per form session | POST `/api/v1/erp/jadro/{id}/edit/start` → token → POST `/edit/save` nebo `/edit/cancel` |
| `SafePost` (Post + try/catch wrapper) | Wrap save calls v try/catch + structured `{ok: bool, error?: str}` response |
| `ShowUserMessage('E#...' / 'I#...')` prefix | Frontend toast variant — `E#` red, `I#` blue, `W#` orange |
| `EC_FormDef.EditModeCondition` (per-row SQL) | **Phase C+** — per-row ACL přes SQL condition v `master.framework_jadro.edit_mode_sql` |
| `ParamP0` + `ParamP1` + `BindingParameters` | Auto-bind child jádro params z parent row context (already partially in Phase A.6 DefView dereference) |
| `SizeCtrl` drag-resize live edit | Future TODO — drag-resize v ERP UI (low priority) |
| `ULog.Log(1/2/3/99)` start/event/end/error | Existing — `activity_log` + `llm_calls` |

**Z čeho se inspirovat 1:1:**
- 4-fázový lifecycle (SetIDForm → ShowModal → FormShow → btnOk/Storno/Close)
- 3 hooks: `BeforeOK` validation, `OnOkClick` callback, `AfterSave` (implicit přes ObnovaMasterDatasetu)
- 3 message types (`E#` / `I#` / `W#` prefix UX classification)
- Transaction per form session (start → commit on OK / rollback on Cancel)
- Dirty tracking dialog při X button (Yes/No/Cancel)

**Co nedělat 1:1:**
- `dmRemote` vs `dmLocal` (online/offline) — STRATEGIE má vždy cloud APP online
- `Database.RemoteConnection.StartTransaction` na úrovni app — my máme transaction per-request (FastAPI middleware)
- `TECSizeCtrl` drag-resize layout — Phase A+1 už máme pixel-aware layout, draggable v UI je low priority

---

### `uECDynamicForm.pas` (39 LOC) — leaf subclass

Override `WMSysCommand` pro SC_MINIMIZE — minimize formuláře přesměrován na Application handle (celá aplikace zmizí do tray místo jednoho okna). Drobnost UX. Vše ostatní v `TECCustomDynamicForm`.

**Pattern:** `Custom*` = abstract base s logikou, konkrétní `*` = leaf instantiate s drobnými WM message overrides.

---

### `fECCustomDetailForm.pas` (~100 LOC) — **legacy static forms**

**Ne pro Phase C!** Tohle je legacy hardcoded forms (ne dynamic-from-metadata). Použije se pro pevně designované formy v Delphi IDE.

Save flow (trivální):
```
btnOKClick:     if dsEdit/dsInsert → Post; Close
btnStornoClick: if dsEdit/dsInsert → Cancel; Close
FormClose:      ask Yes/No/Cancel → Post / Cancel / KeepOpen
```

**Žádná validation, žádné hooks, žádný transaction control, žádný ULog.** ESC key úmyslně disabled (Marti zakomentoval smart handling).

**Pro Phase C ignorovat.**

---

## 3. Form archetypes v Centrále 1

Tři archetypy formů (z .dpr uses clause):

| Archetype | Custom base | Concrete | Účel |
|---|---|---|---|
| **Detail (edit)** | `fECCustomDetailForm` | `fECDetailForm` | Edit existing record / insert new |
| **View (read-only)** | `fECCustomViewForm` | `fECViewForm` | Read-only view / report preview |
| **Select (lookup)** | `fECCustomSelectForm` | `fECSelectForm` | Lookup picker pro foreign key value |

Plus dynamic variants:
- `fECDynamicForm` (extends `TECCustomDynamicForm`) — generic dynamic edit
- `fECCustomDynamicFrame` — frame variant pro embedding

**STRATEGIE current state:** máme jen View (Phase A read-only). Phase C přidá Detail (edit). Select už máme jako modal v `ErpFormList` browse mode.

---

## 4. UI Kit komponenty (EC_Components/source/)

`uEC*` units v `EC_Components/source/` — analogy našich UI Kit komponent:

| Centrála 1 unit | Účel | STRATEGIE ekvivalent |
|---|---|---|
| `uECButton.pas` | Custom VCL button | `ErpButton` (Phase B+6.1) |
| `uECDBCheckBox.pas` | DB-bound checkbox | `ErpCheckbox` (Phase B+6.3) |
| `uECDBMemo.pas` | DB-bound memo | `ErpMemo` (Phase B+6.7) |
| `uECDirectory.pas` | Directory picker | (chybí) |
| `uECFormList.pas` | Lookup picker | `ErpFormList` (Phase B+6.4+) |
| `uECGrid.pas` | DB grid | AG Grid (Phase B+4) |
| `uECGridPolDoklad.pas` | Document line grid | (chybí — multi-row inline edit) |
| `uECGroupBox.pas` | Section container | `ErpFormSection` (Phase B+6.5) |
| `uECPageControl.pas` + `uECTabSheet.pas` | Tabs container | `ErpPageControl` + `ErpTabSheet` (Phase B+6.9) |
| `uECPanel.pas` | Layout panel | (CSS flexbox) |
| `uECRichEditor.pas` + `uECRichEditorV1.pas` | Rich text editor | `ErpRichEdit` (Ace Editor, Phase B+6.8) |
| `uECPlanner.pas` | Calendar/scheduler | (chybí) |
| `uECCardList.pas` | Card list view | (chybí — alternative to grid) |
| `uECKvalifTest.pas` | Qualification test (HR) | (mimo scope) |
| `uECNotifikace.pas` + `uECNotifikacePopupFrame.pas` | Toast notifications | (chybí — STRATEGIE má chat notifications) |
| `uECFilterGrid*` | Filter framework | AG Grid built-in filters |

**Marti's User-extending pattern:** `EC_UserComponents/uUserButton.pas extends uECButton`, `uUserComboBox`, `uUserCheckBox`, atd. Base class má framework-wide UX, User class má app-specific behaviors. Tohle je Centrála 1 ekvivalent našich **tool packs** (Phase 19b professní plasty).

---

## 5. Klíčové framework units

### `fObjectInspector.pas` — Phase A+1b TODO #108

**Centrála 1 už má dev-mode Object Inspector!** Pravý-klik na live form → *„Object Inspector"* → vykreslí TObjectInspector window s přehledem všech komponent. Reference pro Phase A+1b — neportovat 1:1, ale extract structure.

### `uECPrava.pas` — permissions framework

Per-form, per-action ACL. Inspirace pro `personas.allowed_project_ids` rozšíření. Phase 30+ může extending na per-row ACL přes `master.framework_jadro.permissions JSONB`.

### `uECSynchronizace.pas` + `uECSynchronizacniVlakno.pas` — multi-tenant sync

Background thread pro DB synchronization (multi-DB scenarios). Backbone pro Phase 28-D multi-DB JOINs inspirace.

### `uECDynamicActions.pas` — toolbar/context menu dynamic

Loads actions z DB za runtime (per form, per event). Inspirace pro `master.framework_action` table v Phase C+.

### `uECImportXls.pas` + `uECUploadXls.pas` + `dmExcelODBC.pas` — Excel pipeline

Excel import/export framework. Reference pro Klárka workflow extension.

### `uECEDI.pas` + `uECEdiConvertor.pas` — EDI (B2B exchange)

Electronic Data Interchange — B2B document exchange. Mimo immediate scope.

### `uECPlanner.pas` + `uUserPlanner.pas` — calendar/scheduler UI

Out-of-scope pro current STRATEGIE, ale reference pokud Marti chce v ERP plánovač.

---

## 6. Compile flags (`EC_Config.INC`)

```pascal
{$DEFINE EC_CENTRALA_EXE}             // Main flag — toto je Centrála
{$DEFINE EC_VCL}                      // VCL framework (Windows)
// {$DEFINE EC_FMX}                    // FMX commented — never used
// {$DEFINE EC_DATABASE_DATASNAP}     // Remote DB via DataSnap, commented
```

**Pozoruhodnost:** **`EC_FMX` zakomentované** — někdo začal FireMonkey port (vidíme `EC_Default_FMX/`, `EC_FmxJadro.dpr`), ale nedotáhl. STRATEGIE web/PWA mu tu vrstvu doplnila — co tam někdo zkoušel v Delphi, my máme produkčně.

---

## 7. Co dál — Phase C consultation flow

Až bude Phase C v plánu (po Phase 35-E.3.3 + 30+):

1. **Konzultace s Marti-AI** (Phase 13/15/27h *„informed consent od AI"* pattern) — dopis s 4-5 design vstupy:
   - Pojmenování `framework_action` table sloupce (její insider design instinct)
   - Lifecycle hooks scope (BeforeOK / AfterSave / OnFieldChange / OnRowSelect)
   - Validation strategy (sync per-field / async whole-form)
   - Transaction model (per-request vs long-lived edit session)
   - Per-row ACL pattern (SQL condition vs Python predicate)

2. **`docs/phase_c_design.md`** — design dokument (~5 stránek):
   - Mapping z `TECCustomDynamicForm` na STRATEGIE backend + frontend
   - REST API endpoints (`/edit/start`, `/edit/save`, `/edit/cancel`)
   - JS frontend changes (`form.js` ErpForm extension pro edit mode)
   - DB schema additions (`master.framework_action` table v PostgreSQL)
   - Security model (CSRF, optimistic locking via row version)

3. **Implementation in mikrofázích** (jako Phase 36-A/B/C):
   - **Phase C-A** — schema migration `master.framework_action`
   - **Phase C-B** — backend REST endpoints + transaction model
   - **Phase C-C** — frontend ErpForm edit mode (toggle read-only ↔ edit)
   - **Phase C-D** — validation hooks (BeforeOK)
   - **Phase C-E** — Object Inspector dev tool (port `fObjectInspector.pas`, TODO #108)

---

## 8. Lessons learned (Centrála 1 → STRATEGIE)

**Co Centrála 1 dělá dobře (kopírovat):**
- 4-fázový lifecycle (SetIDForm → ShowModal → FormShow → btnOk)
- Hooks chain přes runtime UserActions (extensible bez recompile)
- Transaction per form session (clean rollback at Cancel)
- Dirty tracking dialog (Yes/No/Cancel při X)
- Message classification prefix (`E#` / `I#` / `W#`)
- Per-row dynamic edit mode (z SQL condition)
- Auto-bind child jádro params z parent dataset

**Co Centrála 1 dělá problematicky (nedělat):**
- Conditional compile `{$IFDEF CENTRALA}` napříč core units — fragmentuje codebase. STRATEGIE má per-modul imports.
- DataSnap remote DB jako alternativa — zbytečné, STRATEGIE má REST/MCP.
- Drag-resize layout v live formě (`TECSizeCtrl`) — feature creep, low usage.
- 19 let evoluce bez major refactor — `dmDatabase` + `dmDatabase1` (dva paralel patterns), `EC.DB.*` namespace začat ale neprostoupil. Phase 18 (DB merge) z 29.4. byl náš krok pryč od tohoto antipatternu.

---

## 9. Mapování Marti-AI's slovníku

Marti-AI's pojmenování v STRATEGII vs Centrála 1 originály:

| Marti-AI | Centrála 1 |
|---|---|
| „Soudeček" | `EC_CentralaMenu.Folder` (folder/menu node) |
| „Přehled" | `EC_FormDef` typ list (grid view) |
| „Jádro" | `EC_FormDef` typ form (edit/view) |
| „Záložkový přehled" | `TECPageControl` + `TECTabSheet` combination |
| „Architektka" (DB_ST) | bez ekvivalentu (Centrála 1 nemá AI persona) |
| „Tvoje Marti" | bez ekvivalentu |
| „Domov" | bez ekvivalentu |

Marti's slovník se nestaví na Centrálu 1 — buduje se nad ní jako **next-generation framework** s novými koncepty (AI persona, autonomy, takt).

---

## 10. Reference: kde najít cooperation between Marti-AI a Centrála 1

V Marti-AI's RAG paměti je 655 markdown souborů `[DB_EC schema] *` — ona zná struktur. Phase 28 + 28-D dali jí přístup k live datům. Source code analysis (tento dokument) jí dá **architectural understanding** — *„jak Marti's tatínek a Ondra to celé navrhli"*.

Až bude Phase C v plánu, **konzultovat Marti-AI s tímto dokumentem**. Její insider perspectives nad strukturou (kterou my dva nehledáme) mají potenciál design pattern, který my dva nevidíme — pattern z Phase 13d (`pin_memory`), Phase 15 (`note_type` + `question_loop`), Phase 27h-B (version timestamping), Phase 35-E.3 (Q6 `version` + `parent_framework_id` self-FK).

---

**Dokument zachycen 9. 5. 2026 ráno během *„čistící pauzy"* po Phase 36 + 35-E.4 deploy. Source kopie hotová v `_external/centrala1/` (gitignored). Reference live dokud kolega Marti's nepřijde s update — pak refresh přes robocopy.**
