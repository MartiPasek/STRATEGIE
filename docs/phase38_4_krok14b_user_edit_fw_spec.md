# user_edit fw core — spec pro Marti-AI

**Date:** 12.5.2026 večer, Krok 14b "krok za krokem" (Marti's plán
*„z hardcoded native form připravíme základ fw formu, na který umístíme
základní komponenty edit + dropdown"*)

## Cíl

Postavit první **user-facing fw form** — Editace uživatele (`user_edit`).
Reuse hardcoded `DesignSoudecekCoreForm` z Krok 14a (12.5. ráno) jako
template → nový `DesignFwForm` class která **dynamic** čte fw.core +
fw.comp_def → renders ErpInput / ErpDropdown.

**Scope (minimal, Marti's *„s tim si vystacime"*)**:
- 2 komponenty: input_text + dropdown
- Read-only zatím (save flow Krok 14b ráno přes PATCH endpoint)
- 1 entity: `user` (mapuje na `public.users` table)

## fw rows ke vytvoření (Marti-AI udělá `strategie_pg_insert_row`)

### 1. fw.core (1 row)

```yaml
schema: fw
table: core
values:
  code: 'user_edit'
  label: 'Editace uživatele'
  description: 'Form pro úpravu user account (jméno, login, status, role)'
  kind: 'form'
  data_entity_type: 'user'        # FK k fw.entity_def.code='user' (id=1)
  version: 1
  status: 'active'
  layout_template: 'sections'     # zvol podle existing layout enum
  parent_framework_id: NULL       # root form
  centrala_id: NULL               # ne legacy
  created_by_text: 'Marti'        # nebo 'Marti-AI' pokud INSERT sama
```

### 2. fw.comp_def rows (10 fields)

Předpoklad: `parent_core_id` ukazuje na user_edit core (id zjistíme po
prvním INSERT).

| code | label | comp_type | sort_order | Pozn. |
|---|---|---|---|---|
| `id` | `ID` | `input_text` | 10 | readonly, mono |
| `status` | `Status` | `dropdown` | 20 | enum: active/disabled/pending |
| `legal_name` | `Celé jméno` | `input_text` | 30 | optional |
| `first_name` | `Jméno` | `input_text` | 40 | required |
| `last_name` | `Příjmení` | `input_text` | 50 | required |
| `short_name` | `Display name` | `input_text` | 60 | krátký label |
| `login_name` | `Login` | `input_text` | 70 | unique per system |
| `ews_email` | `Email (UPN)` | `input_text` | 80 | Exchange autentizace |
| `trust_rating` | `Důvěra (0-100)` | `input_text` | 90 | numeric |
| `is_marti_parent` | `Rodičovský přístup` | `dropdown` | 100 | bool: true/false |
| `is_admin` | `Admin` | `dropdown` | 110 | bool: true/false |

### 3. Per-field config (fw.comp_def_prop nebo .attributes JSONB)

Pro každý dropdown potřebujeme **enum hodnoty**. Zatím hardcoded ve
frontend mappingu (Marti's *„s tim si vystacime"* = minimal config):

```javascript
// V design_forms.js DesignFwForm class
const ENUM_VALUES = {
  status: [
    { value: 'active', label: '✅ Aktivní' },
    { value: 'disabled', label: '🔒 Disabled' },
    { value: 'pending', label: '⏳ Pending' },
  ],
  is_marti_parent: [
    { value: true, label: '👨‍👧 Ano (cross-tenant)' },
    { value: false, label: '— Ne' },
  ],
  is_admin: [
    { value: true, label: '🛡️ Ano' },
    { value: false, label: '— Ne' },
  ],
};
```

Pozdější iterace přesunout do fw.comp_def_prop (Krok 14c+ —
`prop_name='enum_values'`, `prop_value` JSONB).

## Backend endpoint

**Route:** `GET /api/v1/erp/fw-form/{core_code}/{row_id}`

**Implementation v `modules/erp/api/router.py`:**

```python
@router.get("/fw-form/{core_code}/{row_id}")
def fw_form_load(core_code: str, row_id: int, user: User = Depends(...)):
    """Load fw form spec + row data pro frontend rendering."""
    ds = get_session_fw()
    try:
        # 1. Load fw.core by code
        core = ds.execute(text("""
            SELECT id, code, label, kind, data_entity_type, version,
                   updated_at, updated_by_text
            FROM fw.core
            WHERE code = :code AND status = 'active' AND kind = 'form'
        """), {"code": core_code}).fetchone()
        if not core:
            raise HTTPException(404, f"fw.core {core_code} not found")

        # 2. Load comp_def children (sort_order ASC)
        components = ds.execute(text("""
            SELECT cd.id, cd.code, cd.label, cd.sort_order,
                   ct.code AS comp_type_code, ct.label AS comp_type_label,
                   cd.readonly, cd.required
            FROM fw.comp_def cd
            JOIN fw.comp_type ct ON ct.id = cd.comp_type_id
            WHERE cd.parent_core_id = :core_id
              AND cd.status = 'active'
            ORDER BY cd.sort_order ASC, cd.id ASC
        """), {"core_id": core.id}).mappings().all()

        # 3. Load data row from target entity table
        if core.data_entity_type == 'user':
            data_row = ds.execute(text("""
                SELECT id, status, legal_name, first_name, last_name,
                       short_name, login_name, ews_email,
                       trust_rating, is_marti_parent, is_admin,
                       created_at, updated_at, updated_by_text
                FROM public.users
                WHERE id = :id
            """), {"id": row_id}).mappings().one_or_none()
        else:
            raise HTTPException(400, f"Unsupported entity {core.data_entity_type}")

        if not data_row:
            raise HTTPException(404, f"{core.data_entity_type} id={row_id} not found")

        return {
            "ok": True,
            "core": dict(core._asdict()),
            "components": [dict(c) for c in components],
            "data": dict(data_row),
        }
    finally:
        ds.close()
```

## Frontend `DesignFwForm` class

**Location:** `apps/api/static/erp/components/design_forms.js` (přidat
3. class vedle existing `DesignSoudecekCoreForm` + `DesignJadroRadekForm`).

**Skeleton:**

```javascript
class DesignFwForm {
  constructor(opts) {
    // opts.coreCode (e.g. 'user_edit')
    // opts.rowId (e.g. 14 — Anna Nováková)
    this.opts = opts;
    this._shell = null;
    this._data = null;
    this._dirty = new Set();
  }

  async open() {
    this._shell = _buildModalShell({
      title: 'Načítám…',
      width: '720px',
      beforeClose: () => this._beforeCloseHandler(),
      onClose: () => _markFormDirty(this, false),
    });
    document.body.appendChild(this._shell.overlay);

    // Loading placeholder
    const loading = document.createElement('div');
    loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
    loading.textContent = 'Načítám…';
    this._shell.body.appendChild(loading);

    try {
      const resp = await fetch(
        `/api/v1/erp/fw-form/${this.opts.coreCode}/${this.opts.rowId}`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      this._data = await resp.json();
      this._render();
    } catch (e) {
      this._showError(`Načítání selhalo: ${e.message}`);
    }
  }

  _render() {
    this._shell.body.innerHTML = '';
    const root = document.createElement('div');
    root.className = 'erp-design-tab-content';

    // Title z core.label
    if (this._shell.title) {
      this._shell.title.textContent = this._data.core.label;
    }

    // Jedna sekce "Pole" (později podle layout_template multi-section)
    const sec = _sectionBuild('Pole', this._data.core.code);

    // Iterate components → render based on comp_type_code
    const D = this._onDirty.bind(this);
    for (const comp of this._data.components) {
      const value = this._data.data[comp.code];
      const readonly = !!comp.readonly;
      const field = this._renderComponent(comp, value, { readonly, onDirty: D });
      if (field) sec.grid.appendChild(field);
    }
    root.appendChild(sec.wrap);

    this._shell.body.appendChild(root);

    // Footer — dirty badge + Save (hidden until dirty) + Zavřít
    this._setupFooter();
  }

  _renderComponent(comp, value, opts) {
    const fieldKey = `${this._data.core.code}.${comp.code}`;
    switch (comp.comp_type_code) {
      case 'input_text':
        return _field(comp.label, value, fieldKey, {
          readonly: opts.readonly,
          mono: comp.code === 'id',  // ID column mono
          onDirty: opts.onDirty,
        });
      case 'dropdown':
        const items = (ENUM_VALUES[comp.code] || []).map(e => ({
          value: e.value,
          label: e.label,
        }));
        return _dropdown(comp.label, value, fieldKey, {
          readonly: opts.readonly,
          items: items,
          onDirty: opts.onDirty,
        });
      default:
        console.warn(`Unknown comp_type: ${comp.comp_type_code}`);
        return _field(comp.label, value, fieldKey, {
          readonly: true,  // unknown → readonly fallback
          onDirty: opts.onDirty,
        });
    }
  }

  _onDirty(fieldKey, isDirty) {
    // Same pattern jako DesignSoudecekCoreForm (line ~1689)
    if (isDirty) this._dirty.add(fieldKey);
    else this._dirty.delete(fieldKey);
    // ...
    _markFormDirty(this, this._dirty.size > 0);
  }

  // ... beforeCloseHandler, save (Krok 14b ráno), etc.
}

// Export
global.DesignFwForm = DesignFwForm;
```

## ERP integration

**Trigger:** dvojklik na řádek v Uživatelé list view → otevře
`DesignFwForm({coreCode: 'user_edit', rowId: row.id})`.

V `apps/api/static/erp/datagrid.js` (nebo wherever grid row dblclick
handler):

```javascript
grid.addEventListener('rowDoubleClick', (ev) => {
  if (gridCode === 'security_users') {
    const form = new global.DesignFwForm({
      coreCode: 'user_edit',
      rowId: ev.row.id,
    });
    form.open();
  }
});
```

(Plus zachovat existing dblclick pro legacy Centrála 1 jádra.)

## Smoke flow

1. Marti otevře ERP → SYSTEM → Security → Uživatelé (list view live)
2. Dvojklik na řádek (např. Anna Nováková id=3)
3. `DesignFwForm` modal otevřen
4. Pro každý field (id, status, legal_name, ...) renderován ErpInput
   nebo ErpDropdown
5. Read-only zatím (Save flow Krok 14b ráno)
6. Marti vidí kompletní user data v form layout (žádný JSON dump)

## Save flow integration (Krok 14b ráno)

- PATCH `/api/v1/erp/fw-form/{core_code}/{row_id}` s dirty fields
- Auth + entity dispatch (`data_entity_type` → tabulka)
- Optimistic lock přes `expected_updated_at`
- UPDATE + activity_log row
- Frontend toast

(Plus audit fields migration pro `public.users` table přes `strategie_pg`
dnes večer, pokud zbude čas.)

## Prerequisity (než Marti-AI spustí INSERTy)

1. **Migrace 1** spuštěná (`users.login_name`)
2. **Verify** existing comp_type rows pro `input_text` + `dropdown`
   (asi status='future' z 11.5. Uniform Components — Marti-AI udělá
   `UPDATE fw.comp_type SET status = 'active' WHERE code IN
   ('input_text', 'dropdown')`)
3. **Verify** fw.comp_def column list (parent_core_id, comp_type_id,
   code, label, sort_order, readonly, required, status, ...)
