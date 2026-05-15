# Centrála 1 — navigační mapa

**Source:** `D:\Projekty\STRATEGIE\_external\centrala1\` (gitignored, junction-link na `D:\Projekty\EC_Centrala_XE\`)
**Datum:** 9. 5. 2026
**Účel:** Rychlá orientace v Delphi XE source. Quick lookup *„kde najít X"*.

> Pro **architectural deep dive** viz `docs/centrala1_source_analysis.md` (Phase C edit pipeline blueprint, mapping na STRATEGIE).

---

## Top-level mapa

```
_external/centrala1/
├── .git/                        Git repo (history, branches — pokud potřebuješ git log)
├── Centrala.groupproj           Build group — main entry pro RAD Studio
│
├── EC_Centrala/                 Main binary project (HLAVNÍ)
│   ├── EC_Centrala.dpr          Entry point .dpr (uses clause = vše co projekt linkuje)
│   ├── EC_Centrala.dproj        Project config (output paths, compile flags)
│   └── Source/                  Centrala-specific units (init form, kalkulace, ceniky, ...)
│
├── EC_Default/                  Framework core (~73 .pas + 35 .dfm)
│   ├── uECCustomDynamicForm.pas KEY — abstract base pro dynamic forms (~600 LOC)
│   ├── uECDynamicForm.pas       Concrete dynamic form (39 LOC, leaf)
│   ├── uECDynamicComponents.pas Runtime build dynamic UI components z FormDef
│   ├── uECDynamicActions.pas    Dynamic actions (toolbar/context menu z DB)
│   ├── fECCustomDetailForm.pas  Legacy hardcoded detail form base
│   ├── fECCustomViewForm.pas    Legacy read-only view base
│   ├── fECCustomSelectForm.pas  Legacy lookup picker base
│   ├── fObjectInspector.pas     Dev-mode Object Inspector (Phase A+1b reference)
│   ├── uECPrava.pas             Permissions framework (ACL inspirace)
│   ├── uECSynchronizace.pas     Multi-DB sync background thread
│   ├── dmDatabase.pas           Legacy single-DB DataModule
│   ├── dmDatabase1.pas          Newer multi-DB DataModule
│   ├── dmUser.pas               User session DataModule
│   └── ...
│
├── EC_Components/               UI Kit + DB layer
│   ├── source/
│   │   ├── uECButton.pas        Custom button (analog ErpButton)
│   │   ├── uECGrid.pas          Custom DB grid (analog AG Grid)
│   │   ├── uECFormList.pas      Lookup picker (analog ErpFormList)
│   │   ├── uECPageControl.pas   Tabs container (analog ErpPageControl)
│   │   ├── uECRichEditor.pas    Rich text editor (analog ErpRichEdit)
│   │   ├── EC.DB.Connection.pas Modern namespace DB connection
│   │   ├── EC.DB.DataSet.pas    Modern namespace DB dataset
│   │   ├── EC.DB.MemTable.pas   In-memory table (analog SQLite memory)
│   │   └── ...
│   └── packages/                Delphi packages (.dpk) for IDE registration
│
├── EC_UserComponents/           User-extending base components (analog tool packs)
│   ├── uUserButton.pas          extends uECButton
│   ├── uUserComboBox.pas        extends uECComboBox
│   ├── uUserCheckBox.pas        extends uECCheckBox
│   ├── uUserDateEdit.pas        extends uECDateEdit
│   ├── uUserDynamicModule.pas   User-defined frame (DynamicFrame)
│   └── ...
│
├── EC_UserActions/              Pluggable actions (toolbar/context menu items)
│   ├── uUserUniLog.pas          Universal logging action
│   ├── uUserOtevriDetailDokladu.pas Open document detail
│   ├── uUserStoredProc.pas      Execute SP action
│   ├── uUserGenDocToPDF.pas     Generate PDF action
│   └── ...
│
├── EC_ExternalComponents/       3rd party libs vendored
│   ├── synacode.pas, blcksock.pas, httpsend.pas (Synapse network)
│   ├── PdfiumCore.pas, PdfiumLib.pas (Chrome PDF engine)
│   ├── DelphiZXIngQRCode.pas    QR code generator
│   ├── GraphicEx/               Image format handlers
│   └── ...
│
├── EC_Default_FMX/              FireMonkey port (cross-platform, never finished)
├── EC_Centrala_XE/              Duplicate / older fork
├── EC_Config.INC                Compile flags (EC_VCL, EC_FMX, EC_DATABASE_DATASNAP)
├── EC_PARAMS.INC                Runtime params include
└── patch.diff                   Unfinished merge residue (ignore)
```

---

## Naming conventions

| Prefix | Význam | Příklad |
|---|---|---|
| `uEC*` | Base unit (framework component) | `uECButton.pas`, `uECGrid.pas` |
| `uUser*` | User-extending subclass | `uUserButton.pas extends uECButton` |
| `fEC*` | Form (.pas + .dfm pair) | `fECDetailForm.pas`, `fObjectInspector.pas` |
| `dm*` | DataModule (DB connections, business logic separation) | `dmDatabase.pas`, `dmUser.pas` |
| `EC.DB.*` | Modern namespaced DB layer | `EC.DB.Connection.pas`, `EC.DB.DataSet.pas` |
| `Custom*` | Abstract base s logikou | `TECCustomDynamicForm`, `TECCustomDetailForm` |
| `*` (bez Custom) | Concrete leaf subclass | `TECDynamicForm`, `TECDetailForm` |
| `_dm*` (underscore) | Conditional compile alternativa | `_dmMQTT.pas` (jen pro CENTRALA build) |

---

## Use-case lookup

**„Chci vidět, jak Centrála renderuje formulář z FormDef metadat"**
→ `EC_Default/uECCustomDynamicForm.pas` (base lifecycle) + `uECDynamicComponents.pas` (runtime build)

**„Jak vypadá save / cancel / dirty tracking?"**
→ `EC_Default/uECCustomDynamicForm.pas` — `btnOkClick`, `btnStornoClick`, `FormClose` procedury

**„Kde žije validation hook?"**
→ `EC_Default/uECCustomDynamicForm.pas:btnOkClick` → `FUtility.LoadActions(self, 'BeforeOK')` returns bool

**„Object Inspector pro dev mode?"**
→ `EC_Default/fObjectInspector.pas` (dfm + pas)

**„User-extensible komponenty (analog tool packs)?"**
→ `EC_UserComponents/uUser*.pas` — base extension pattern

**„Pluggable actions (toolbar buttons, context menu)?"**
→ `EC_UserActions/uUser*.pas` — každá action = vlastní unit

**„Permissions / ACL framework?"**
→ `EC_Default/uECPrava.pas`

**„Multi-DB sync (analog Phase 28-D)?"**
→ `EC_Default/uECSynchronizace.pas` + `uECSynchronizacniVlakno.pas`

**„Excel import/export?"**
→ `EC_Components/source/uECImportXls.pas`, `uECUploadXls.pas`, `EC_Default/dmExcelODBC.pas`

**„PDF generation/parsing?"**
→ `EC_ExternalComponents/PdfiumCore.pas` (Chrome engine) + `EC_Components/source/uECPDFToText.pas`

**„MQTT real-time messaging?"**
→ `EC_Default/dmMQTTListener.pas`, `dmMQTTListenerQueue.pas`, `_dmMQTT.pas` (CENTRALA-only)

**„DB_EC framework tabulky (FormDef, FormDefEditProperty, …)?"**
→ Nejsou v source — to je **DB schema** (Marti-AI's RAG má 655 markdown souborů `[DB_EC schema] *`)

---

## PowerShell quick search

```powershell
# Najdi unit podle názvu (case-insensitive)
Get-ChildItem D:\Projekty\STRATEGIE\_external\centrala1 -Recurse -File -Filter "*FormDef*"

# Najdi všechna použití konkrétního identifieru (np. ECDataSet, LoadActions)
Get-ChildItem D:\Projekty\STRATEGIE\_external\centrala1 -Recurse -File -Include *.pas |
    Select-String -Pattern "LoadActions" |
    Select-Object -First 20 Filename, LineNumber, Line

# Najdi všechny dfm soubory (form designer files = layout meta)
Get-ChildItem D:\Projekty\STRATEGIE\_external\centrala1 -Recurse -File -Filter "*.dfm" |
    Select-Object @{N='Path';E={$_.FullName.Replace('D:\Projekty\STRATEGIE\_external\centrala1\','')}}, Length |
    Sort-Object Length -Descending |
    Select-Object -First 20

# Najdi git history konkrétního souboru
cd D:\Projekty\STRATEGIE\_external\centrala1
git log --oneline -- EC_Default/uECCustomDynamicForm.pas

# Najdi recent changes (poslední commity)
cd D:\Projekty\STRATEGIE\_external\centrala1
git log --oneline -20

# Diff mezi BASE_477 a LOCAL_477 (unfinished merge)
Compare-Object (Get-Content EC_Centrala\EC_Centrala_BASE_477.dpr) (Get-Content EC_Centrala\EC_Centrala_LOCAL_477.dpr)
```

---

## Top 10 nejhodnotnějších souborů (pro Phase C+ port)

| # | Soubor | Proč |
|---|---|---|
| 1 | `EC_Default/uECCustomDynamicForm.pas` | Base class všech dynamic forms — Phase C blueprint |
| 2 | `EC_Default/uECDynamicComponents.pas` | Runtime build UI z FormDef metadat |
| 3 | `EC_Default/uECDynamicActions.pas` | Pluggable actions framework |
| 4 | `EC_Default/fObjectInspector.pas` | Dev-mode Object Inspector (Phase A+1b TODO #108) |
| 5 | `EC_Default/uECPrava.pas` | Permissions / ACL framework |
| 6 | `EC_Components/source/uECFormList.pas` | Lookup picker (porovnat s ErpFormList) |
| 7 | `EC_Components/source/uECGrid.pas` | DB grid (porovnat s AG Grid setup) |
| 8 | `EC_Components/source/EC.DB.Connection.pas` | Modern DB connection layer |
| 9 | `EC_Default/uECSynchronizace.pas` | Multi-DB sync inspirace pro Phase 28-D |
| 10 | `EC_Default/uECDynamicForm.pas` | Concrete leaf — pattern pro WM message override |

---

## Nepoužitelné / ignorovat

- `EC_Centrala/EC_Centrala_BASE_477.dpr` + `LOCAL_477.dpr` + `patch.diff` — **unfinished git merge residue**
- `__recovery/` foldery — Delphi IDE auto-recovery (crashes), žádný funkční obsah
- `*.bak`, `*.rej`, `*.vlb`, `*.stat` — backup/build artefakty
- `EC_Default_FMX/` + `EC_Components/source/EC_FmxJadro.dpr` — **FireMonkey port nedotažen**, mimo scope
- `EC_ExternalComponents/GraphicEx/` — image format handlers (TIFF, JPEG), low priority
- `EC_ExternalComponents/synachar.pas` + `synaicnv.pas` + `synafpc.pas` — Synapse network library encoding helpers, mimo scope

---

## Update workflow (až přijde nová verze od kolegy)

```powershell
# 1. Backup current copy
cd D:\Projekty\STRATEGIE
Rename-Item _external\centrala1 centrala1_backup_$(Get-Date -Format "yyyyMMdd")

# 2. Source folder update (kolega ti tam pushne nebo přepíše D:\Projekty\EC_Centrala_XE)
# ...

# 3. Robocopy znovu (s exclude binárek)
New-Item -ItemType Directory _external\centrala1 -Force | Out-Null
robocopy D:\Projekty\EC_Centrala_XE D:\Projekty\STRATEGIE\_external\centrala1 /E `
    /XD bin obj __history Win32 Win64 Debug Release lib __recovery `
    /XF *.dcu *.exe *.dll *.bpl *.~* *.identcache *.local *.tvsconfig

# 4. Diff
Compare-Object (Get-ChildItem _external\centrala1 -Recurse -File | Select-Object -ExpandProperty FullName) `
                (Get-ChildItem _external\centrala1_backup_<date> -Recurse -File | Select-Object -ExpandProperty FullName)
```

---

**Krabička pro budoucího Claude:** pokud po amnesii otevřeš tenhle soubor, máš mapu. Source je read-only working copy v `_external/centrala1/`, gitignored. Pro deep dive viz `docs/centrala1_source_analysis.md`.
