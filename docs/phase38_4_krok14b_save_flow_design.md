# Phase 38.4 Krok 14b — Save flow design (skeleton)

**Date:** 13.5.2026 (draft připraven 12.5. večer ~20:30)

Po Marti's konzultaci s Marti-AI (12.5. večer, 5 iterací) je finální
design jasný. Ráno spustíme migrace + implementaci.

## Architektonické rozhodnutí (z konzultace)

### Audit fields (finální)

Per **Marti's *„system je taky user"*** doctrine + Marti-AI's bod #A
(created_* symetrie):

```
created_at        TIMESTAMP    -- existing, Marti-AI's 8.5. DDL
created_by_text   VARCHAR      -- existing, Marti-AI's 8.5. DDL
created_by_id     INTEGER FK   -- NOVÉ (Migrace 2)
updated_at        TIMESTAMP    -- existing, trigger drží
updated_by_id     INTEGER FK   -- NOVÉ (Migrace 2)
updated_by_text   VARCHAR(200) -- NOVÉ frozen label (Migrace 2)
```

**Žádný `updated_by_persona_id`** — Marti's elegant simplification
přes *„system je taky user"*. Persona Marti-AI dostala `users.id=2`
(12.5. večer), všichni budoucí actors (cron, import, automation) taky
budou user accounts.

### PATCH endpoint

```
URL:     PATCH /api/v1/erp/design/{entity}/{id}
Auth:    Bearer token (session user)
Body:    {
           "changes": {"col1": val1, "col2": val2},
           "expected_updated_at": "2026-05-13T08:42:31"  // Marti-AI's bod #B (optimistic lock)
         }

Backend:
  1. Auth → resolve actor:
     - If session.user_id → actor_user_id = user.id, actor_text = user.login_name
     - If session.persona_id (Marti-AI from chat) → 
         lookup persona.linked_user_id → actor_user_id, persona.name → actor_text
     - If background task (cron, migration) → actor_user_id = system_user.id, 
         actor_text = 'system' or task name
  
  2. Entity dispatch (whitelist):
     - "menu_node" → fw.menu_node
     - "core" → fw.core
     - "comp_def" → fw.comp_def
     - "comp_def_prop_override" → fw.comp_def_prop_override
     - else → 404 Not Found
  
  3. Column whitelist (per entity, z entity_def attributes):
     - Reject id, created_at, created_by_*, updated_at (system-managed)
     - Allow remaining columns
  
  4. Optimistic lock check:
     SELECT updated_at, updated_by_text 
     FROM {entity} WHERE id = {id};
     IF updated_at != expected_updated_at:
       RETURN 409 Conflict {
         "error": "concurrent_edit",
         "current_updated_at": "...",
         "current_updated_by_text": "Kristy"  // kdo prepsal mezitim
       }
  
  5. UPDATE (atomic):
     UPDATE fw.{entity}
     SET {col1} = ?, {col2} = ?,
         updated_by_id = {actor_user_id},
         updated_by_text = {actor_text}
     WHERE id = {id}
       AND updated_at = {expected_updated_at}  -- double-check at DB level
     RETURNING updated_at, updated_by_id, updated_by_text;
     
     IF rowcount == 0:
       RETURN 409 Conflict  -- race condition fallback
  
  6. activity_log entry (Vrstva 1 design save, retention forever):
     INSERT INTO activity_log (
       actor_user_id, action_kind, entity_type, entity_id,
       payload, change_source, created_at
     ) VALUES (
       {actor_user_id}, 'design_save', '{entity}', {id},
       '{"fields": [...], "before": {...}, "after": {...}}',
       'ui',  -- Marti-AI's bod #A (change_source)
       NOW()
     );
  
  7. Response 200 OK {
       "ok": true,
       "id": {id},
       "updated_at": "...",
       "updated_by_text": "Marti",
       "changed_fields": ["col1", "col2"]
     }
```

### Frontend `_onSaveClick` (per Marti's volba C — direct save + toast)

```javascript
async _onSaveClick() {
  const changes = {};
  for (const fieldKey of this._dirty) {
    const wrap = this._findWrapByFieldKey(fieldKey);
    changes[fieldKey] = this._getValue(wrap);
  }
  
  const expectedUpdatedAt = this._data.updated_at;
  
  try {
    const resp = await fetch(`/api/v1/erp/design/${entityType}/${entityId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ changes, expected_updated_at: expectedUpdatedAt }),
    });
    
    if (resp.status === 409) {
      const data = await resp.json();
      // Konzervativní: show modal "Kristý uložila X. Obnovit (ztratíš
      // své změny) / Zůstat (porovnat ručně)?"
      this._showConflictModal(data);
      return;
    }
    
    if (!resp.ok) {
      const err = await resp.json();
      this._showErrorToast(err.message || 'Uložení selhalo');
      return;
    }
    
    const data = await resp.json();
    
    // Clear dirty state
    this._dirty.clear();
    _markFormDirty(this, false);
    this._onDirty('', false);  // refresh badge
    
    // Update local _data.updated_at pro next save's optimistic lock
    this._data.updated_at = data.updated_at;
    
    // Green toast
    this._showSuccessToast(`Uloženo (${data.changed_fields.length} změn)`);
  } catch (e) {
    this._showErrorToast(`Chyba: ${e.message}`);
  }
}
```

### Toast helper (drobnost — pojď ráno přidat)

```javascript
_showSuccessToast(msg) {
  const toast = document.createElement('div');
  toast.style.cssText = "position:fixed;bottom:24px;right:24px;background:#2d5a2d;color:#e8eef5;padding:10px 18px;border-radius:4px;border:1px solid #4a7a4a;box-shadow:0 4px 12px rgba(0,0,0,0.5);z-index:10000;font-size:13px;";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.style.opacity = '0', 2700);
  setTimeout(() => toast.remove(), 3000);
}
```

## Migration order (ráno 13.5.)

1. **Migrace 1** — `users.login_name` (ADD NULL → backfill ze short_name → NOT NULL UNIQUE)
   - DBeaver SQL Editor, manual run
   - Verify: `SELECT id, login_name FROM users ORDER BY id`
   - Backfill expected: Marti, Marti-AI, Kristy, Sarka, Jirka, Ondra, Pavel, Petra, Michal, Claude (10 actors)

2. **Migrace 2** — `fw.*` audit fields (4 tabulky)
   - DBeaver SQL Editor, ALL 4 ALTER TABLE v jedné transakci (commit/rollback together)
   - Verify: information_schema.columns

3. **Migrace 3** — `activity_log.change_source`
   - ADD COLUMN + index + CHECK constraint

4. **Migrace 4** — `personas.linked_user_id`
   - ADD COLUMN + index + UPDATE Marti-AI persona (id=1) → linked_user_id=2

5. **Code** — PATCH endpoint v `modules/erp/api/router.py` (nebo nový `design_save.py`)
   - Auth + entity dispatch + column whitelist
   - Optimistic lock
   - UPDATE + activity_log INSERT
   - Response 200/409/400

6. **Frontend** — `apps/api/static/erp/components/design_forms.js`
   - `_onSaveClick` refactor (currently no-op alert)
   - 409 handling (conflict modal — separate Marti-AI consultation později)
   - Toast helpery (success + error)
   - Local `_data.updated_at` refresh po save

7. **Smoke test** — Marti-AI v chatu otevre Design modal, zmena 1 field, Save → toast + DB ověření

## Otevřené otázky pro ranní review

- **System user** — chceme nový `users` row pro system (cron, migration, AI background tasks)? Nebo NULL pro `updated_by_id` + `updated_by_text = 'system'`?
  - Recommended: nový user row `id=0` (zero, reserved) nebo `id=999999` (max int) s `first_name='System'`, `last_name='Strategie'`, `login_name='system'`, `is_admin=false`, `password_hash=NULL`
  - Drží Marti's *„system je taky user"* explicit (ne NULL = explicit absence)

- **CHECK constraint na actor** — vyžadovat `updated_by_id IS NOT NULL` při UPDATE? Nebo NULL OK pro legacy/migration rows?
  - Recommended: NULL OK (existing rows mit NULL po Migrace 2 ADD COLUMN; nove UPDATE pres PATCH vzdy fill)

- **Persona Marti-AI vs user Marti-AI** — když Marti-AI chat-driven action volá `record_thought` (její diary), audit user_id = 2 (via personas.linked_user_id)? Nebo NULL (diary je její *„soukromé"*)?
  - Recommended: user_id = 2 (audit consistency), plus `change_source = 'marti_ai'` flag pro filter v UI (admin view *„Marti-AI's chat actions"*)
