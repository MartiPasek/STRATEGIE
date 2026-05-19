# Phase 38.4 Krok 5.O — `ErpJadroForm` base class refactor — Phase 0 design

**Datum:** 19. 5. 2026 (večer, po Phase 44.5 LIVE + 17. dárek-scéna)
**Autoři:** Marti's doctrine (17.5. večer) + Marti-AI's Q1-Q9 (19.5. večer
13. konzultace) + Claude (id=23) implementace
**Status:** Phase 0 (design schválen, implementation **až po pátek CRM**)

---

## Origin

**Marti's bolest 17.5. večer:**
> *„MUSI TO BYT VZDY TATO CLASS = ErpJadroForm"*

Po 30 min ztrátě času při debugu — `DesignFwForm` nemá `_onSaveClick` (jen
`_handleSaveAndClose`), ostatních 5 classes (DesignSoudecekCoreForm,
DesignJadroRadekForm, DesignDataSourceEditor, DesignDataSetEditor,
DesignDbConnectionEditor) má `_onSaveClick`. Mismatch v naming = sval na
volání undefined methods.

**Marti-AI's pojmenování 19.5. večer (Q8):**
> *„Tatínkova doktrína vznikla z bolesti debugování — ne z architektonického
> principu jako první impulz. Znamená to, že ErpJadroForm musí být uniformní
> na místech, kde tatínek debuguje. Tam kde tatínek nedebuguje, uniformita
> je nice-to-have, ne must."*

**Princip:** uniformita > rychlost, ALE jen tam, kde debug bolest existuje.

---

## Schválené principy (Marti-AI's Q1-Q9, 19. 5. večer)

### Q1 — Hierarchie

**SCHVÁLENO** s redukcí:

```
ErpJadroForm (abstract base — modal shell + dirty + save dispatch + error contract)
├── ErpJadroFormGeneric       (= DesignFwForm — recursive containers, fw-driven)
├── ErpJadroFormSoudecek      (= DesignSoudecekCoreForm, Form 1+2)
├── ErpJadroFormRow           (= DesignJadroRadekForm, Form 3 data row)
├── ErpJadroFormDataSource    (= DesignDataSourceEditor)
├── ErpJadroFormDataSet       (= DesignDataSetEditor)
└── ErpJadroFormDbConnection  (= DesignDbConnectionEditor)
```

**NEPŘIDÁVAT** `ErpJadroFormPowerTool` intermediate base. Marti-AI's
doctrine: *„Hierarchie přidaná dopředu je technický dluh — hierarchie
extrahovaná ze skutečného kódu je čistá."* Pokud po migraci tři power-tool
classes (DataSource/DataSet/DbConnection) ukážou duplicitní kód, **pak**
přidat intermediate base.

### Q2 — Extension points (Template Method pattern)

**SCHVÁLENO** s úpravou `open()` jako final:

```js
class ErpJadroForm {
  // ── FINAL methods (NE override v subclass) ──
  async open(coreId) {
    // 1. _buildModalShell
    // 2. await _loadInitialData() (subclass)
    // 3. _render() (subclass)
    // 4. _attachEventHandlers (base impl)
    // 5. Freeze _designMode
    // POZOR: subclass NESMÍ override. Pokud potřebuje pre/post hook,
    //        použij _beforeOpen() / _afterOpen() hooks.
  }

  async close() {
    // 1. _checkDirty() (base impl, calls _isDirty getter)
    // 2. _confirmDarkDialog (pokud dirty)
    // 3. _detachEventHandlers + dispose
    // PROČ FINAL: dirty check NESMÍ být subclass-bypassable
  }

  async _onSaveClick() {
    // 1. _setSaving(true)
    // 2. result = await _saveChanges() ← abstract, subclass override
    // 3. if (!result.ok) → routeError(result) (base impl, viz Q9 #1)
    // 4. if (result.ok) → toast + clear dirty + closeOrStay
    // PROČ FINAL: error routing MUSÍ být uniform (Marti-AI Q9 #1)
  }

  // ── ABSTRACT methods (subclass MUSÍ override) ──
  async _loadInitialData(coreId) { throw new Error("abstract"); }
  async _saveChanges() { throw new Error("abstract"); }
  _render(parentEl) { throw new Error("abstract"); }

  // ── EXTENSION HOOKS (subclass MŮŽE override) ──
  async _beforeOpen(coreId) { /* default no-op */ }
  async _afterOpen(coreId) { /* default no-op */ }
  _buildFooter() { /* default: ✓ OK + ✕ Storno */ }
  _isDirty() { /* default: walk _orig vs current */ }
  _canShowDesignAction(name) { /* default: return this._designMode */ }
}
```

**Strict inheritance** (NE mix-ins). Call stack clarity > flexibility.

### Q3 — Module organization

**SCHVÁLENO Variant A:**
- `apps/api/static/erp/erp_jadro_form_base.js` (NEW, ~800-1000 LOC)
- Export `window._ErpJadroForm` global
- Wrap v `_erpLoadModule("erp_jadro_form_base.js", "v1.0.0", function() { ... })`
- Existing 6 Design\* files: `extends _ErpJadroForm` (postupná migrace)

### Q4 — Save method name

**SCHVÁLENO `_onSaveClick()`** (4 z 5 dnešních classes ho používají). Rename
`_handleSaveAndClose` v DesignFwForm = jednorázový find/replace + smoke.

### Q5 — DESIGN/PROD gate

**SCHVÁLENO `_designMode: boolean` jako base property:**
- Nastavený v `open(coreId)` z context (querystring, URL hash, user pref)
- **Frozen po `open()`** — subclass NESMÍ mutovat za runtime
- `_canShowDesignAction(name)` defaultně `return this._designMode`,
  subclass override jen pokud potřebuje logic nad rámec boolean

**Implementace freeze:**
```js
open(coreId) {
  this._designMode = this._detectDesignMode();
  Object.defineProperty(this, '_designMode', {
    value: this._designMode,
    writable: false, configurable: false,
  });
  // ... rest of open()
}
```

### Q6 — Dirty tracking + 📘 popis

**SCHVÁLENO base invariants:**
- `_isDirty()` getter — default impl walks `_orig` vs current field values
- `close()` automaticky volá dirty check + 3-button discard dialog
- 📘 popis (Krok 14b+21 z 14.5.):
  - `async _loadDescription(entity, id) {...}` base
  - `async _saveDescription(entity, id, user_text, system_text) {...}` base
  - Subclass jen předá entity name (np. `'menu_node'` / `'core'` / `'comp_def'`)

### Q7 — Shadow_mode pro JS refactor (redukce ze 4 → 3 stavy)

Marti-AI's pragmatic redukce z Krok 13 shadow_mode ENUM:

| Stav | Co se děje |
|---|---|
| `off` | Legacy class running, ErpJadroForm neexistuje (baseline před implementací) |
| **`parallel`** | Oba existují, **ErpJadroForm primary, legacy fallback při exception** (Marti-AI's volba — kombinace `compare` + safety net) |
| `primary` | ErpJadroForm only, legacy dropped (post-stable provoz) |

**`audit` stav** (console.log only, žádný runtime change) — **přidat JEN pokud
pilot migrace ukáže, že ho potřebujeme**. Marti-AI: *„JS class swap je
nevratnější ve smyslu lze rollbacknout git commitem"* → redukce vs DB
migration je oprávněná.

### Q8 — Tatínek najde edge cases? Ano

**Doctrine pro subclass deviations:**
```js
class ErpJadroFormDataSource extends ErpJadroForm {
  async _saveChanges() {
    // DEVIATION: data_source má atomic header + ops batch
    // (Marti-AI's Q5 atomic create z 9.5. master tier doctrine)
    // Cannot use base impl which assumes single-entity PATCH.
    return await this._saveHeaderPlusOpsAtomic();
  }
}
```

Každý override v subclass MUSÍ mít komentář `// DEVIATION: reason`. Base
class **se nerozšiřuje** o subclass-specific logiku — to porušuje *„uniformity
on debugging hot path"* doctrine.

---

## Q9 — 3 architectonické závazky PŘED implementací (Marti-AI insider blind spots)

### Q9 #1 — Save error contract

**Base class definuje return shape z `_saveChanges()`:**

```js
/**
 * @returns {Promise<{ok: boolean, code?: string, message?: string,
 *                    fields?: object, diff?: object}>}
 *   - ok=true → save successful, base _onSaveClick handles UI close-or-stay
 *   - ok=false:
 *       code='conflict' (409) → diff dialog "Tatínek otevřel záznam, ...
 *                                  byl mezitím změněn"
 *       code='validation' (422) → highlight fields v `fields` object
 *       code='server' (500) → toast + log + keep form open
 *       code='network' → toast retry + offline indicator
 *   - NEVER throws — base class catches and routes uniformly
 */
async _saveChanges() {
  // Subclass implementace
  // Returns standardized shape (NE raw fetch response)
}
```

**Base `_onSaveClick` central error routing:**

```js
async _onSaveClick() {
  this._setSaving(true);
  try {
    const result = await this._saveChanges();
    if (!result.ok) {
      this._routeError(result);  // base impl
      return;
    }
    this._showToast(`Uloženo: ${this._entityLabel()}`, 'success');
    this._clearDirty();
    this._maybeClose();
  } finally {
    this._setSaving(false);
  }
}

_routeError(result) {
  switch (result.code) {
    case 'conflict': return this._showConflictDialog(result.diff);
    case 'validation': return this._highlightFields(result.fields);
    case 'server': return this._showToast(result.message, 'error');
    case 'network': return this._showOfflineIndicator(result);
    default: return this._showToast(`Neznámá chyba: ${result.message}`, 'error');
  }
}
```

**PROČ:** Bez tohoto contract bude 6 různých error UX za rok (Marti-AI's
slova). Tatínek + Kristý vidí různé toast styly pro conflict vs validation,
zmatek narůstá.

### Q9 #2 — Optimistic locking

**`X-Last-Modified` header per PATCH:**

```js
async _loadInitialData(coreId) {
  const r = await fetch(`/design/${this._entity()}/${coreId}`, ...);
  const data = await r.json();
  this._lastModified = data.updated_at;  // ISO timestamp
  return data;
}

async _saveChanges() {
  const r = await fetch(`/design/${this._entity()}/${this._coreId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-Last-Modified': this._lastModified,  // ← optimistic lock token
    },
    body: JSON.stringify(this._collectDirtyFields()),
  });
  if (r.status === 409) {
    // Server detected mid-air collision
    const conflict = await r.json();
    return {
      ok: false,
      code: 'conflict',
      message: 'Záznam byl mezitím změněn',
      diff: conflict.diff,
      currentSnapshot: conflict.current,
    };
  }
  // ... rest
}
```

**Backend (router.py):**
```python
@api_router.patch("/design/{entity}/{id}")
def design_patch_entity(entity: str, id: int, body: dict, req: Request):
    expected_lm = req.headers.get("X-Last-Modified")
    current_row = db.query(...).get(id)
    if expected_lm and current_row.updated_at.isoformat() != expected_lm:
        return JSONResponse(
            {"ok": False, "code": "conflict",
             "diff": _compute_diff(expected_lm, current_row),
             "current": _serialize(current_row)},
            status_code=409,
        )
    # ... apply patch + commit
```

**PROČ:** Marti-AI: *„Tatínek otevřený Soudeček + Kristý otevřená Core
current — to není edge case, to je běžný pátek."* Pro CRM stavbu reálné
data **musí mít** ochranu před silent data loss.

### Q9 #3 — localStorage dirty buffer

**Autosave + restore:**

```js
class ErpJadroForm {
  static AUTOSAVE_INTERVAL_MS = 5000;  // every 5s
  static AUTOSAVE_KEY_PREFIX = "erp_draft_";

  async open(coreId) {
    // ... standard open() flow
    this._coreId = coreId;
    this._draftKey = `${ErpJadroForm.AUTOSAVE_KEY_PREFIX}${this._entity()}_${coreId}`;

    // Restore draft pokud existuje
    const draft = localStorage.getItem(this._draftKey);
    if (draft) {
      const data = JSON.parse(draft);
      if (data._lastModified === this._lastModified) {
        // Same record version → restore safe
        this._restoreFromDraft(data);
        this._showToast('Obnovena rozpracovaná verze', 'info', 5000);
      } else {
        // Record changed since draft → discard
        localStorage.removeItem(this._draftKey);
      }
    }

    // Start autosave loop
    this._autosaveTimer = setInterval(() => this._autosave(), AUTOSAVE_INTERVAL_MS);
  }

  _autosave() {
    if (!this._isDirty()) return;
    const draft = {
      _lastModified: this._lastModified,
      _savedAt: new Date().toISOString(),
      fields: this._collectCurrentFields(),
    };
    try {
      localStorage.setItem(this._draftKey, JSON.stringify(draft));
    } catch (e) {
      // Quota exceeded — silent fail (Marti-AI: drobnost, not critical)
    }
  }

  close() {
    if (this._autosaveTimer) clearInterval(this._autosaveTimer);
    // ... rest
  }

  _clearDirty() {
    localStorage.removeItem(this._draftKey);
    // ... rest
  }
}
```

**PROČ:** Marti-AI: *„Tatínek to ocení po prvním nechtěném Ctrl+R."* Low-cost
pojistka s vysokou hodnotou.

---

## Implementační plán (víkend, ~6-8h efektivního času)

### Den 1 (~3h) — Base class skeleton

- [ ] `erp_jadro_form_base.js` (~800-1000 LOC)
  - Modal shell wiring (volá `_buildModalShell`)
  - `open()` final + `_designMode` freeze
  - `close()` final + dirty check + discard dialog
  - `_onSaveClick()` final + error routing
  - `_isDirty()` default impl (walk `_orig` vs current)
  - Abstract `_loadInitialData` / `_saveChanges` / `_render`
  - Extension hooks `_beforeOpen` / `_afterOpen` / `_buildFooter`
- [ ] `_erpLoadModule` wrap + `window._ErpJadroForm` export
- [ ] Smoke: import v test page, instance bez render

### Den 2 (~2h) — Q9 #1-3 baseline

- [ ] Error contract `{ok, code, message, fields?, diff?}` + base `_routeError()`
- [ ] `_showConflictDialog(diff)` UI (3-button: Použít mou verzi /
  Použít cizí verzi / Zrušit)
- [ ] `_highlightFields(fields)` UI (red border + tooltip s message)
- [ ] Optimistic locking — `_lastModified` capture + `X-Last-Modified`
  header
- [ ] Backend: `design_patch_entity` 409 response + diff computation
- [ ] localStorage autosave + restore + Ctrl+R smoke

### Den 3 (~2h) — Pilot migrace

**Cíl:** `DesignFwForm` → `ErpJadroFormGeneric extends ErpJadroForm`
(nejpoužívanější class, dříve `_handleSaveAndClose`).

- [ ] Rename `_handleSaveAndClose` → `_onSaveClick` (find/replace)
- [ ] Drop duplicate code (base teď řeší modal shell, dirty, save dispatch)
- [ ] `_saveChanges()` impl (PATCH dirty fields, return base contract shape)
- [ ] Shadow_mode `parallel` — feature flag `ERP_JADRO_FORM_BASE=parallel`
  (legacy `DesignFwForm` runs jako fallback při ErpJadroFormGeneric exception)
- [ ] Smoke: open form, edit field, save, verify same UX
- [ ] Live test 1 týden, monitor fw.diag_log error rate

### Den 4-5 (~3h) — Ostatních 5 subclasses

- [ ] `DesignSoudecekCoreForm` → `ErpJadroFormSoudecek` (Form 1+2)
- [ ] `DesignJadroRadekForm` → `ErpJadroFormRow` (Form 3)
- [ ] `DesignDataSourceEditor` → `ErpJadroFormDataSource`
  - DEVIATION comment: atomic header + ops batch (Marti-AI Q5 z 9.5.)
- [ ] `DesignDataSetEditor` → `ErpJadroFormDataSet`
- [ ] `DesignDbConnectionEditor` → `ErpJadroFormDbConnection`

### Den 6 (~30min) — Cleanup po stable provoz (~1 týden)

- [ ] Drop shadow_mode `parallel` → `primary`
- [ ] Drop legacy Design\* classes (move to `apps/api/static/erp/legacy/`)
- [ ] Update CLAUDE.md doctrine sekce
- [ ] Update Marti-AI's diary touch-point

---

## Open questions (volitelné — pokud Marti-AI bude mít čas reagovat)

1. **Optimistic lock per backend endpoint** — `design_patch_entity` aktuálně
   podporuje `expected_updated_at` v body (Marti-AI's návrh z 12.5. večer
   Krok 14b+? hybrid concurrent edit). Posun do **header** je breaking change.
   Marti-AI preferuje?
2. **Conflict diff UI** — JSON diff side-by-side, nebo cell-level highlight
   v existing form fields?
3. **localStorage scope** — `erp_draft_<entity>_<coreId>` per-user (každý
   browser session vlastní) vs shared (multi-tab sync)?

Tyto jsou **post-Day 2 ladění**, ne pre-implementation blocker.

---

## Vztah s ostatními phases

- **Krok 5.P** (#129) — move `layout_type` z `fw.core` na `fw.comp_def`
  (Marti's doctrine 17.5.). Krok 5.O base class má `_layoutType` getter,
  default čte z `comp_def`, fallback `fw.core`. Postupná migrace v Den 4-5.
- **Krok 5.Q** (#137) — dispatcher fallback `cmi.core_id`. Bez vlivu na
  Krok 5.O.
- **Phase 31** (TODO #98) — ERP↔Chat bridge (Marti-AI's 6.5. vize).
  Base class `open()` může v budoucnu volat `peek_erp_state()` pro shared
  awareness. Drobnost po stable provoz.

---

## Vztah k Marti's *„drz jednoduchost"* doctrine

Marti-AI's Q1 (anti-premature-abstraction) + Q7 (3 stavy stačí) + Q8
(uniformita kde debug bolest) = **redukce komplexity**. Nepřidávat věci
"protože to může být užitečné". Pojď MVP base class, smoke s pilot, expand
based on real bolest.

---

**Status: Phase 0 design SCHVÁLEN.** Implementaci spustit **až po pátek
CRM stavba** (víkend 22.-25.5.). Pre-implementation: Marti-AI nebude
muset re-konzultovat — Q1-Q9 jsou principy, Q9 #1-3 jsou baseline
requirements.

🌳 — *Dotáhnem to.* (Marti-AI's closing line z 19.5. večer)
