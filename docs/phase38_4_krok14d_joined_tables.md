# Phase 38.4 Krok 14d — Joined tables (1:N child rows v form)

**Vznikl:** 14. 5. 2026 večer (po IT prezentaci s Ondrou + Krok 14c+3.5 polish)
**Trigger:** Marti's *„joinované tabulky, jejich zobrazení a editace, např. Další emaily, telefony"*
**Variant:** A — sub-grid pod form fields (Marti's "klasicky pres grid v jadre edit formu")

---

## Problem statement

Současný form `user_edit` zobrazuje **single row** z `public.users` table.
Marti chce v stejném formu vidět + editovat **související 1:N rows**:
- `user_emails` (další emaily pro user — work / personal / archiv)
- `user_phones` (telefony — mobile / work / home)
- Plus dalších 1:N (možná v budoucnu — `user_addresses`, `user_certifications`, atd.)

Pattern Marti's volba: **sub-grid v form** (Variant A). Plus uniformity
doctrine — engine musí být **generic** pro jakoukoliv parent-child
relationship, ne hardcoded per entity.

## 3 vrstvy implementace

### Vrstva 1 — Schema

**Step 1:** Schema check (Marti runs SQL).

Předpoklad: `public.user_emails`, `public.user_phones` možná existují.
Pokud ne, vznik migrací:

```sql
CREATE TABLE public.user_emails (
  id           BIGSERIAL PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  email        VARCHAR(255) NOT NULL,
  kind         VARCHAR(20)  NOT NULL DEFAULT 'work',
                                  -- 'work' / 'personal' / 'archive' / 'other'
  note         TEXT,
  is_primary   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW(),
  created_by_id INT REFERENCES public.users(id),
  updated_by_id INT REFERENCES public.users(id),
  updated_by_text VARCHAR(255)
);
CREATE INDEX idx_user_emails_user_id ON public.user_emails(user_id);
CREATE TRIGGER user_emails_updated_at_trigger BEFORE UPDATE ON public.user_emails
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE public.user_phones (
  id           BIGSERIAL PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  phone        VARCHAR(50) NOT NULL,
  kind         VARCHAR(20) NOT NULL DEFAULT 'mobile',
                                  -- 'mobile' / 'work' / 'home' / 'fax'
  is_primary   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW(),
  created_by_id INT REFERENCES public.users(id),
  updated_by_id INT REFERENCES public.users(id),
  updated_by_text VARCHAR(255)
);
CREATE INDEX idx_user_phones_user_id ON public.user_phones(user_id);
CREATE TRIGGER user_phones_updated_at_trigger BEFORE UPDATE ON public.user_phones
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

Pokud existují (z Phase 28 user management nebo dřívější), pak schema
fix = jen ALTER ADD missing columns (updated_at, audit fields).

### Vrstva 2 — Backend

**Step 2:** `_FW_FORM_ENTITY_MAP` extension pro children definitions:

```python
"user": {
  "schema": "public",
  "table": "users",
  "id_column": "id",
  "select_columns": [...],  # existing
  # ─── NEW ───
  "children": {
    "user_emails": {
      "table": "user_emails",
      "fk_column": "user_id",
      "id_column": "id",
      "select_columns": ["id", "email", "kind", "note", "is_primary"],
      "default_kind": "work",
      "label": "Další emaily",
    },
    "user_phones": {
      "table": "user_phones",
      "fk_column": "user_id",
      "id_column": "id",
      "select_columns": ["id", "phone", "kind", "is_primary"],
      "default_kind": "mobile",
      "label": "Telefony",
    },
  },
}
```

**Step 3:** Backend endpoints (CRUD per child):

```python
# READ — extend existing GET /fw-form/{code}/{row_id}
# Pridat children section do response:
{
  "core": {...}, "form": {...}, "fields": [...], "data": {...},
  "children": {
    "user_emails": [
      { "id": 1, "email": "...", "kind": "work", ... },
      ...
    ],
    "user_phones": [...]
  }
}

# CREATE
POST /api/v1/erp/fw-form/{core_code}/{parent_id}/children/{child_key}
Body: { email: "...", kind: "work", note: "..." }
→ INSERT s user_id=parent_id

# UPDATE
PATCH /api/v1/erp/fw-form/{core_code}/{parent_id}/children/{child_key}/{child_id}
Body: { email: "...", kind: "work", expected_updated_at: "..." }
→ UPDATE WHERE id=:child_id AND user_id=:parent_id AND updated_at=:expected
→ 409 Conflict pokud mismatch (optimistic lock, jako Krok 14b parent)

# DELETE
DELETE /api/v1/erp/fw-form/{core_code}/{parent_id}/children/{child_key}/{child_id}
→ Soft delete (is_deleted=true) nebo hard delete? Marti rozhodne.
```

**Důležitá architektonická volba:**
- `parent_id` v URL je **safety check** — pokud child_id=5 patří user_id=99 (ne 15), reject (anti tampering)
- Plus per-child `WHERE user_id=:parent_id` v UPDATE/DELETE — guard
  proti race podruhé

### Vrstva 3 — Frontend

**Step 4:** Sub-grid rendering v `DesignFwForm._render`:

```javascript
// Po main form fields, iterate spec.children:
if (this._spec.children) {
  for (const [childKey, childRows] of Object.entries(this._spec.children)) {
    const childConfig = entity_config.children[childKey]; // backend musí poslat label
    
    // Sub-section "Další emaily"
    const childSec = _sectionBuild(childConfig.label, "child:" + childKey);
    
    // AG Grid mini-table pro child rows
    const gridContainer = document.createElement("div");
    gridContainer.style.cssText = "height:200px;...";
    
    new agGrid.Grid(gridContainer, {
      columnDefs: childConfig.select_columns.map(col => ({
        field: col,
        editable: this._formDesignMode || /* in PROD = editable per ACL */,
        ...
      })),
      rowData: childRows,
      onCellValueChanged: (ev) => this._onChildCellChanged(childKey, ev),
      // ... add row button + delete row button per row
    });
    
    childSec.grid.appendChild(gridContainer);
    root.appendChild(childSec.wrap);
  }
}
```

**Step 5:** Save flow — extension stávajícího `_onSaveClick`:

```javascript
async _onSaveClick() {
  // 1. Save parent data (existing Krok 14b flow)
  const parentResult = await this._savParentRow();
  if (parentResult.error) return; // 409 conflict, atd.
  
  // 2. Save dirty child rows (NEW Krok 14d)
  for (const childKey of Object.keys(this._dirtyChildren)) {
    const dirty = this._dirtyChildren[childKey];
    for (const row of dirty.created) await this._postChildRow(childKey, row);
    for (const row of dirty.updated) await this._patchChildRow(childKey, row);
    for (const id of dirty.deleted) await this._deleteChildRow(childKey, id);
  }
  
  _showToast("Uloženo (parent + children)", "success");
}
```

## Marti-AI consultation otázky

Před implementací — 4-5 architektonických otázek pro insider design partner:

1. **Schema design** — pokud child tables chybí, co bys přidala? Pojďme
   user_emails s `is_primary` flag (jen jeden primary) + `kind` enum.
   Schvalná decision criteria pro multi-row entity?

2. **Backend endpoint pattern** — sub-resource (`/fw-form/user/15/children/user_emails`)
   nebo flat (`/fw-form/user_emails`)? Já preferuji sub-resource (parent_id
   safety check), ale ty jsi viděla Centrálu 1 — co tam fungovalo?

3. **`fw.comp_type` pro nested grid** — reuse existing `grid_modern`
   (id=101) nebo nový typ (`nested_grid` id=300+, pojmenuj prosím)?
   Mart's "uniformita vítězí nad speciálními případy" — měl by být
   generic engine, ale nested grid se chová jinak než top-level grid
   (parent_id context, save flow coupling, atd.).

4. **Save flow — atomic vs sequence?** — Centrála 1 pattern:
   - (a) Single transaction: parent + child rows v jednom SQL transaction
       (BEGIN/COMMIT). Pokud child UPDATE selže, parent rollback.
   - (b) Sequential: parent save first, pak children jeden po druhém.
       Pokud child fail, parent zůstane uloženy, children dirty.
   Co tam fungovalo z user perspective?

5. **Insider catch** — co jsi v Centrále 1 patternu pro related tables
   spatřila, co by mělo zůstat (Q3 "věci, které k sobě patří, mají bydlet
   spolu" doctrine)? Co změnit?

## Mikrofáze plán

| Krok | Co | ETA |
|---|---|---|
| 14d-A | Schema check + případná migrace (Marti runs SQL) | 15 min |
| 14d-B | `_FW_FORM_ENTITY_MAP['user'].children` extension | 15 min |
| 14d-C | Backend GET extension (children load) + per-child CRUD endpoints | 1.5h |
| 14d-D | Frontend sub-grid renderer (AG Grid mini + dirty tracking) | 2h |
| 14d-E | Marti-AI consultation dopis + odpověď | mezi B a D (paralelně) |
| 14d-F | Smoke E2E (add email, edit, delete, save parent+child) | 30 min |

Total: ~4.5h pro full Krok 14d. Možná víc pokud Marti-AI's odpověď
přinese pivots (Phase 13/15/19b/27h/35/9-iter pattern — obvykle 2-3
insights co rozšíří plán).

## Status

| Část | Status |
|---|---|
| Marti's pattern volba (Variant A sub-grid) | ✅ 14.5. večer |
| Schema check | ✅ 14.5. večer (user_contacts polymorphic existuje) |
| Marti-AI consultation | ✅ 14.5. večer (6 decisions + 3 nuance) |
| Krok 14d-A SQL migrace audit fields | ✅ 14.5. večer (ALTER ADD prošel) |
| Krok 14d-B fw.comp_type INSERT nested_grid | ⏳ ready, čeká spustění |
| Backend implementation (14d-C) | ❌ TODO |
| Frontend implementation (14d-D) | ❌ TODO |
| Save flow atomic + timeout (14d-E) | ❌ TODO |
| Smoke E2E (14d-F) | ❌ TODO |

## Archeology — Marti's earlier design choices (14.5. večer discovery)

Při Krok 14d-A migrace jsme zjistili, že **Marti's `user_contacts` table
už měla** (pravděpodobně z Phase 22 user management, 29.4.):
- `ux_user_primary_contact` — partial unique index (same constraint
  jako Marti-AI's Q1B preference). Marti-AI's pattern už byl in DB
  prior to consultation.
- `trg_user_contacts_updated_at` — updated_at trigger (same pattern
  jako Marti-AI's Q7 z 9.5.).

**Doctrine confirmation:** Marti-AI's Q1A *„Tvoje dubnové rozhodnutí
bylo správné"* je archeologicky prokázaná. Marti's prior design pattern
konverguje s Marti-AI's later architectural review. Plus convention:
Marti's naming je `trg_` prefix pro trigger + `ux_` prefix pro unique
index. Marti-AI's draft naming `_trigger` suffix + `uq_` prefix —
estetic difference, semantic identical.

**Po archeology cleanup (14.5. večer):**
- DROP `uq_user_contacts_primary` (naš duplikát) — zachovat
  `ux_user_primary_contact` (Marti's earlier)
- DROP `user_contacts_updated_at_trigger` (naš duplikát) — zachovat
  `trg_user_contacts_updated_at` (Marti's earlier)

**Co Krok 14d-A reálně přidalo:**
- 4 audit columns (created_by_id, created_by_text, updated_by_id, updated_by_text)
- function `public.update_updated_at()` (idempotent CREATE OR REPLACE)
- Žádná jiná changes (index + trigger byly existing)
