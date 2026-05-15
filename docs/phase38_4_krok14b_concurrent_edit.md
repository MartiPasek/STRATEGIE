# Phase 38.4 Krok 14b+? — Hybrid Concurrent Edit Protection

**Vznikl:** 14. 5. 2026 odpoledne (~40 min před Marti's IT prezentaci s Ondrou)
**Trigger:** Marti's pojmenování distributed systems risk *„dva users na stejnou tabulku → vzajemne si prepisou"*
**Marti's reakce:** *„Zní až moc ideálně... Zapiš to do todo."*

---

## Problem

**Lost update** — klasický distributed systems anti-pattern:

```
T0 (08:00):  Marti i Kristý otevřou form users.id=15 (oba SELECT)
T1 (08:30):  Marti změní legal_name="Pavel Zeman"
T2 (08:35):  Kristý změní status="disabled"
T3 (08:36):  Kristý SAVE → UPDATE users SET status='disabled' WHERE id=15
T4 (08:40):  Marti SAVE → UPDATE users SET legal_name='Pavel Zeman' WHERE id=15
             ↑ Marti VŠECHNY ostatní fields přepíše ze SVÉ 08:00 verze.
             ↑ Kristýino status='disabled' přepíše zpět na 'active'.
             ↑ TICHÝ data loss. Žádný warning. Žádná stopa.
```

**Centrála 1 anti-pattern:** last-write-wins bez detection. EUROSOFT to *„toleruje"*
protože paralelní edits jsou vzácné, ale s 60 lidmi + Marti-AI v týmu **risk roste**.

## Dvě možnosti řešení (a hybrid)

### Možnost A — Marti-AI's optimistic lock (12.5. večer Save flow konzultace)

```
PATCH /fw-form/user_edit/15
Body: {
  expected_updated_at: "2026-05-14T08:00:00Z",   ← timestamp z původního SELECT
  legal_name: "Pavel Zeman"
}

Backend SQL:
  UPDATE public.users
  SET legal_name='Pavel Zeman', updated_at=NOW()
  WHERE id=15
    AND updated_at='2026-05-14T08:00:00Z'   ← ATOMIC GUARD
  RETURNING id;

Pokud 0 rows → 409 Conflict (someone changed it).
```

**Pro:** Atomic — single SQL statement, žádný race window. DB engine garantuje.
**Proti:** Generic conflict message *„někdo to změnil"*. Per-row, ne per-field.

### Možnost B — Marti's compare-data (14.5. odpoledne, *„nejdrive vyvolat novy select te vety"*)

```
1. Marti SAVE click
2. Backend: SELECT row z DB
3. Backend: Diff vs original (frontend posílá original v body)
4. Pokud diff → 409 + detail per-field
5. Pokud match → UPDATE
```

**Pro:** Friendly UX *„Kristý změnila status z 'active' na 'disabled'"*.
**Proti:** **Race window mezi krok 2 a 5.** Kristý může save mezi SELECT a UPDATE.
Není atomic bez SERIALIZABLE transaction.

### Recommended — Hybrid (kombinuje obojí)

```
STEP 1 — Atomic guard přes updated_at:
  UPDATE public.users
  SET legal_name='Pavel Zeman', updated_at=NOW()
  WHERE id=15
    AND updated_at='2026-05-14T08:00:00Z'
  RETURNING id;

STEP 2 — Pokud 0 rows (409 Conflict):
  SELECT current row z DB (teď je bezpečné — UPDATE neproběhl)
  Diff vs frontendu posílaný `original` snapshot

STEP 3 — Vrátit 409 s payload:
  {
    error: "concurrent_edit",
    conflicts: [
      { field: "status", was: "active", now: "disabled" }
    ],
    by_user: { id: 11, short_name: "Kristý" },
    changed_at: "2026-05-14T08:35:00Z",
    current_updated_at: "2026-05-14T08:35:00Z"   ← pro retry
  }

STEP 4 — Frontend reakce:
  Dialog: "Kristý změnila pole 'status' (active → disabled) v 08:35.
           Co chceš?"
  [Reload] — discard moje změny, reload from current
  [Přepsat] — POST znovu s `expected_updated_at=current_updated_at`
              (= force overwrite, vědomě)
  [Merge]   — (future polish) auto-merge non-overlap fields
```

**Atomic guard z A + friendly diff z B = best of both worlds.**

## Edge cases (Marti's *„zní moc ideálně"* intuition)

1. **Auto-merge non-overlap fields**
   - Marti změnil `legal_name`, Kristý změnila `status`. Žádný overlap.
   - Auto-merge = zapis Marti's `legal_name` + zachovat Kristý's `status`.
   - Risk: pokud Marti's `legal_name` change byl motivován starým `status='active'`
     view, mohlo to být *„semanticky"* nepřesné.
   - **Konzervativně:** ne auto-merge MVP. Marti vidí dialog, rozhodne sám.

2. **JSONB / nested field diff**
   - `fw.comp_def.layout` JSONB drží mnoho sub-fields (width, height, panels).
   - Two users edit different sub-keys → diff musí být per-JSONB-path.
   - **MVP:** treat JSONB jako opaque blob (jakákoli změna = conflict).
   - **Future polish:** JSON Patch diff per path.

3. **User identity v diff response**
   - Backend musí znát *„kdo změnil"*. To je `updated_by_id` (Krok 14b ADD COLUMN).
   - Pre-Krok 14b: jen `updated_at` (žádný *„kdo"*). MVP: prostě *„někdo"*.
   - Post-Krok 14b: dohledat user.short_name přes JOIN.

4. **Marti-AI jako updater**
   - Marti-AI's PATCH calls jdou přes stejný endpoint.
   - Conflict dialog musí zobrazit *„Marti-AI změnila..."* místo human user name.
   - `change_source='marti_ai'` (Marti-AI's 12.5. večer návrh) → frontend
     rozliší ikony / kontext.

5. **Force overwrite (rebase pattern)**
   - User klikne *„Přepsat"* po conflict dialog → frontend pošle PATCH znovu s
     `expected_updated_at=current_updated_at` (= timestamp z conflict response).
   - **Race podruhé:** mezi conflict response a force overwrite ANOTHER user
     může edit. Druhý conflict → další dialog. Konvergence nutná.
   - **Limit:** 3× conflict in row → backend zaloguje + frontend zobrazí
     *„Vícenásobné konflikty, otevři row znovu"* (force reload).

6. **Activity log per conflict**
   - Každý 409 Conflict → INSERT do activity_log
     (`category='concurrent_edit_blocked'`, `summary='by={user} field={field}'`).
   - Marti-AI's ranní digest (Phase 16-A oversight) může nakopit konflikty
     → *„dnes 3 lidé měli konflikty na users.id=15, něco systémově?"*.
   - Pattern Marti-AI's *„bezpečnost přes probuzení, ne přes ticho"* (10.5.).

## Implementační plán

**Backend (`modules/erp/api/router.py`):**
1. Nový endpoint `PATCH /fw-form/{core_code}/{row_id}`:
   - Body: `{ expected_updated_at: ISO8601, ...field updates }`
   - Validate fields against `_FW_FORM_ENTITY_MAP[entity]["select_columns"]` whitelist
   - SQL `UPDATE WHERE id AND updated_at=:expected RETURNING id`
   - Pokud 0 rows → re-SELECT + diff + 409 payload
2. Helper `_compare_rows(original: dict, current: dict) -> list[ConflictField]`:
   - Per-key compare. JSONB jako opaque blob (MVP).
   - Returns `[{ field, was, now }]`.
3. Audit log per UPDATE + per 409 Conflict.

**Frontend (`apps/api/static/erp/components/design_forms.js`):**
1. `DesignFwForm.open()` ukládá `this._spec.data.updated_at` jako `_originalUpdatedAt`
2. `_onSaveClick()` → PATCH s body `{ expected_updated_at: _originalUpdatedAt, ...dirty fields }`
3. 409 handler:
   - Parse `conflicts` array + `by_user` + `current_updated_at`
   - Custom `_confirmDarkDialog` 3-button: Reload / Přepsat / Zrušit
   - Reload → re-fetch GET /fw-form/.../15 → refresh form
   - Přepsat → PATCH znovu s `expected_updated_at=current_updated_at`

**Dependencies:**
- `users.updated_at` column existuje (legacy schema OK)
- `users.updated_by_id` + `updated_by_text` — Krok 14b backend migrace
- `update_updated_at()` trigger — Krok 14b backend per-table
- `change_source` column v activity_log — Krok 14b backend
- Marti-AI consultation pre-implementation (Phase 13/15/19b/27h/35/9-iter pattern)

## Centrála 1 distinkce — *„NA ÚROVNI ARCHITEKTURY"*

**Centrála 1:** Form **nemá** detection. Last-write-wins. Marti's *„riziko, že se o data poperou"*.

**STRATEGIE:** Pattern je v **schema layer** (`updated_at` + trigger), **endpoint layer**
(`UPDATE WHERE updated_at`), a **UI layer** (frontend 409 handler). **Single architecture
pattern, applied per-entity automaticky.** Žádný ad-hoc concurrency check per form.

Když přidáš novou entity do `_FW_FORM_ENTITY_MAP`, concurrent edit protection je
**free** — stačí mít `updated_at` column a auto trigger. Generic engine v praxi.

## Marti's *„zní moc ideálně"* — proč

Tři důvody, proč to není zase tak ideal:

1. **Implementační komplexita** — backend potřebuje 2 SQL calls (UPDATE + post-409 SELECT)
   + per-field diff helper + custom JSONB handling. Není to jedno-line fix.
2. **UX rozhodnutí** — Reload vs Přepsat vs Merge: každý má edge cases. User confusion
   risk pokud dialog není self-explanatory.
3. **Performance** — 409 path = 2x DB roundtrip + diff computation. Pokud konflikty
   jsou časté (= bad UX), backend nervously busy. Měření v produkci nutné.

Plus future polish (JSONB merge, auto-merge non-overlap, Marti-AI's special-case
display) — každý sám malý project. **MVP = atomic guard + simple diff dialog.**

## Otevřené otázky pro Marti-AI consultation (po Krok 14b backend)

1. **Auto-merge non-overlap?** Default off (konzervativní), nebo on s explicit confirm?
2. **JSONB diff strategy?** Opaque blob MVP, nebo JSON Path per-key diff?
3. **Marti-AI's vlastní concurrent edits?** `change_source='marti_ai'` v audit + dialog
   zobrazení (*„Marti-AI změnila..."* místo user name)?
4. **Rate-limit conflict dialogs?** 3 conflicts in row → force reload (anti-loop)?
5. **Cross-tenant concurrency?** Kristý v EUROSOFT vs Marti-AI v STRATEGII edituje
   stejnou users row přes různé tenant context — možné? Pokud ano, jak řešit?

## Status

| Část | Status |
|---|---|
| Marti-AI's návrh optimistic lock | ✅ 12.5. večer (Save flow konzultace) |
| Marti's návrh compare-data | ✅ 14.5. odpoledne |
| Hybrid pattern pojmenovaný | ✅ 14.5. odpoledne (tento doc) |
| TODO #62 v workspace | ✅ 14.5. |
| Krok 14b backend implementation | ❌ TODO po IT prezentaci |
| Marti-AI consultation pre-impl | ❌ TODO (5 otázek výše) |
| Smoke test E2E | ❌ TODO |

---

**Marti's pivot vision:** *„Centrála 1 neresi, my to resit budeme — protože máme
Marti-AI v týmu, riziko paralelních edits poroste. Architektonicky, ne ad-hoc."*

---

## Produkční flow (14.5. ~15:50, Marti's *„VYJADRI SE"*)

### Backend 409 payload contract

```json
HTTP 409 Conflict
{
  "ok": false,
  "error": "concurrent_edit",
  "conflicts": [
    { "field": "status", "was": "active", "now": "disabled", "label": "Stav účtu" }
  ],
  "by_user": { "id": 11, "short_name": "Kristýna", "change_source": "ui" },
  "changed_at": "2026-05-14T08:30:00Z",
  "current_data": { /* celý row whitelist */ },
  "current_updated_at": "2026-05-14T08:30:00Z"
}
```

### Frontend dialog (4 volby)

| Tlačítko | Akce |
|---|---|
| **⟳ Načíst znovu** | Drop Marti's uncommitted edits, render `current_data` v formě (žádný re-fetch — z 409 payload) |
| **⚠ Přepsat přesto** | Resend PATCH s `expected_updated_at = current_updated_at`. Force overwrite, Marti's data přepíší Kristýiny. Vědomé rozhodnutí. |
| **📋 Porovnat detail** | Side-by-side modal *„Tvoje vs Kristýiny vs DB current"* (Krok 14b+?+, future polish) |
| **✗ Zpět** | Zavřít dialog, form zůstane otevřený s Marti's edits (defer decision) |

### Safeguards produkce

1. **Audit log per 409** — `activity_log` INSERT s `category='concurrent_edit_blocked'`
2. **Anti-loop** — 3× 409 in row během 10 min → *„Přepsat"* disabled, force *„Načíst znovu"*
3. **Marti-AI special case** — `change_source='marti_ai'` → dialog ukáže Marti-AI's reasoning z `marti_ai_thought_id` v audit
4. **Smart field formatting** — enum lookup (status: active→disabled, ne raw IDs), text truncate, JSONB per-key summary

### End-to-end pattern

```
PATCH /fw-form/user_edit/15 + expected_updated_at
       ↓
Backend UPDATE WHERE id AND updated_at=:expected
       ↓
   match (1 row)    miss (0 rows)
       ↓                 ↓
   200 OK            SELECT current + diff + WHO/WHEN
                         ↓
                    409 + payload
                         ↓
                    Frontend 4-button dialog
                         ↓
                    ┌─Reload─→ render current_data
                    ├─Přepsat→ resend PATCH s current_updated_at
                    ├─Detail─→ side-by-side modal (future)
                    └─Zpět──→ defer (edits preserved)
```

**Marti's hodnota pro produkci:** *„Žádný silent loss — uživatel vždy ví, co se stane."*
