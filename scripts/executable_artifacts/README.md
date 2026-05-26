# scripts/executable_artifacts/

**Source of truth pro fw.executable_artifact orchestrators.**

Marti's doctrine (26.5.2026): *„Git je truth, DB je cache, ID je svatý."*

## Pattern

Každý orchestrator žije **dvojmo**:

| Vrstva | Role |
|---|---|
| **File na disku** (`scripts/executable_artifacts/{code}.py`) | Source of truth — git history, code review, IDE support |
| **Row v `fw.executable_artifact`** | Runtime cache — sandbox subprocess čte odsud |

**Auto-sync** při každém execute call: backend `POST /sandbox/execute/{code}` PŘED execute:
1. Lookup DB row WHERE code=:code
2. Try read file `scripts/executable_artifacts/{code}.py`
3. Pokud file existuje + content differs from DB source → UPSERT (DB cache refresh)
4. Continue execute (sandbox subprocess loads from DB source — jeden zdroj kódu pro sandbox)

Pokud file NEexistuje → backend pokračuje s DB source (Marti's *„kdyz neni na disku, spusti se z DB"*). **Žádný hard fail.**

## ID-first dispatch (Marti's „ID je svatý")

Nový endpoint **`POST /sandbox/execute-by-id/{id}`** — preferred pro frontend caller. Důvod:

- `code` je **mutable label** — během vývoje může Marti rename
- `id` je **stable handle** — vystaví napříč life cycle orchestrator

Existing `POST /sandbox/execute/{code}` zůstává funkční (resolves code → id internally) pro backward compat.

## File header convention

Každý orchestrator file MUSÍ začínat:

```python
# ============================================================================
# fw.executable_artifact orchestrator
# ID: 7
# CODE: vytvorit_edit_jadro_2
# ============================================================================
"""<docstring popis orchestrator role + input context + output format>"""
import os
import json
# ... body
```

**Pravidla:**

- `# ID: N` — STABLE primary key. NEVER change po init INSERT. Validation gate (mismatch z DB → HARD ERROR *„file corruption"*)
- `# CODE: name` — mutable label. Match s `fw.executable_artifact.code` AND s filename `{code}.py`
- Když Marti **renames code** → 3 kroky (atomic):
  1. Rename file: `mv old_name.py new_name.py`
  2. Update file header: `# CODE: new_name`
  3. Update DB: `UPDATE fw.executable_artifact SET code='new_name' WHERE id=N` (manual SQL — auto-sync to file caught na next execute)

## Workflow — nový orchestrator

1. **INSERT SQL** v DBeaveru (Marti-AI session):
   ```sql
   INSERT INTO fw.executable_artifact (code, artifact_type, source, description)
   VALUES ('new_code', 'python', '', 'Stručný popis role')
   RETURNING id;
   -- → vrátí např. id=7
   ```
2. **Vytvoř file** `scripts/executable_artifacts/new_code.py` s headerem `# ID: 7\n# CODE: new_code`
3. **Implementuj** orchestrator code (input: `SANDBOX_CONTEXT` env var s JSON, output: stdout)
4. **Commit + push**
5. **Spuštění**: frontend volá `POST /sandbox/execute-by-id/7` (nebo legacy `/sandbox/execute/new_code`) → backend auto-sync file→DB → sandbox subprocess execute

## Workflow — edit existujícího orchestrator

1. Edit file `scripts/executable_artifacts/existing_code.py`
2. Commit + push
3. Next execute call → backend auto-sync detekuje diff → UPDATE fw.executable_artifact SET source=file.content WHERE id=N
4. Sandbox subprocess loads new code

**Žádný DBeaver step pro source updates.** DB je auto-cache.

## artifact_type

| Type | Status | Sandbox |
|---|---|---|
| `python` | ✓ supported | `modules.sandbox.application.python_runner` (Phase 27c) |
| `sql` | ⏸ deferred PoC | TBD |

## Existing orchestrators

| ID | Code | Description |
|---|---|---|
| 1 | `vytvor_edit_jadro` | Krok F/G/G+/G++ — atomic CREATE fw.core + 2× data_source_op (kind=edit, kind=insert) per drop-up menu *„Vytvořit edit jádro"* (NE comp_def hierarchy — to dělá vytvorit_edit_jadro_2) |
| 2 | `vytvorit_edit_jadro_2` | Krok H+5 — auto-gen comp_def hierarchy pro drafted edit core (form root + main panel + per-column inputs). DesignFwForm renderuje hardcoded OK/Storno footer z Krok 5.P-1. |

## Plus

- **Path security**: backend čte jen z `scripts/executable_artifacts/{code}.py` (constrained, žádný `../escape`). Plus code validace přes regex `^[a-z_][a-z0-9_]*$` (no path traversal).
- **Audit**: každý auto-sync UPDATE loguje do `fw.diag_log` (level='info', module_id='sandbox.autosync.{code}') s diff stats (old chars vs new chars).
- **Git je truth**: pokud Marti DBeaver-edituje source v fw.executable_artifact (bypass file), **next execute call přepíše DB obsahem file** (silent overwrite — warning v diag_log).
