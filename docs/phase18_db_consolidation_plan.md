# Phase 18: DB Consolidation — Plánovací dokument

**Vytvořeno:** 28. 4. 2026 odpoledne (po Phase 16-B.8 commit)
**Status:** PLAN — čeká na Marti's review ráno před implementací
**Trigger:** Marti's *„Ano prosím merge... Ta úsora času pak bude velmi výrazná"* (28. 4.)
**ETA:** ~2 dny implementace + 1 den testování

---

## Proč

Cross-DB pain z 28. 4.:
- Diagnostika Misa-incidentu vyžadovala 3 separátní SQL queries (2× data_db, 1× core_db)
- Phase 16-B.9 (FK constraint `documents.project_id → projects.id`) **nelze**
  vůbec implementovat, protože PostgreSQL nepodporuje cross-database FK
- Backup/migrace/monitoring je zdvojený
- ORM relations Conversation → User jsou nemožné, místo toho lazy ID lookup
  v jiné session (gotcha #7: UnboundLocalError přes shadowing)

## Inventura (faktické)

### Schéma

| Co | css_db | data_db | Po merge |
|---|---|---|---|
| Tabulky | 21 | 27 | 48 |
| Migrations | 20 | 32 | nová baseline |
| Sloupce s logickou FK cross-DB | — | 4 | bude vynuceno |
| Name conflicts | — | — | **0** ✅ |

### Klíčové cross-DB references (data_db → css_db)

```
Conversation.created_by_user_id    → users.id
Conversation.active_agent_id       → agents.id  (← Phase 16-B.7 ACL pivot)
ConversationParticipant.user_id    → users.id
ConversationShare.shared_with_user_id → users.id
```

A logicky **každá** data_db tabulka s `tenant_id` referuje `tenants.id` v css_db,
ale bez FK constraint.

### Code surface

| Pattern | Soubory | Volání |
|---|---|---|
| `get_core_session()` | 71 | 165 |
| `get_data_session()` | 57 | 254 |
| Oba (cross-DB logika) | 33 | — |
| Jen core | 38 | — |
| Jen data | 24 | — |

**Krit ický cluster** s OBĚMA sessions (vyžaduje největší pozornost):
- `auth/api/router.py`
- `auth/application/invitation_service.py`
- `conversation/api/router.py`
- `conversation/application/composer.py`
- `conversation/application/service.py`

### Edge cases zachycené (subagent inventory)

1. **Soft references bez FK** — Project.default_persona_id, User.last_active_project_id, Conversation.active_agent_id (3 sloupce). **Risk:** orphan references existují už dnes, merge je odhalí. Cleanup nutný před FK přidáním.
2. **Tenant isolation** — žádná data_db tabulka nemá FK na `tenants`. Po merge: cleanup orphans + přidání FK.
3. **30+ diagnostické skripty** v `scripts/_*.py` — všechny budou potřebovat update z `get_core_session/get_data_session` na sjednocené `get_session`.
4. **Audit log** je v css_db, zaznamená data_db row IDs (`conversations.id`) bez FK. Po merge: explicitní FK nebo zachovat IDs jako *„external reference"*.
5. **Self-referential FK** v users (`invited_by_user_id`) — ok, jen pořadí insertu při migraci.

---

## Strategie

### Variant A — Postupné slévání (recommended)

**Princip:** zachovat alembic_data jako *„cílovou"* DB. Postupně přesunout všechny tabulky z css_db do data_db (přejmenovat `data_db` → `strategie`). Alembic history merge přes nový baseline migration.

**Proč Recommended:**
- data_db má víc tabulek (27 vs 21) a víc migrací (32 vs 20) — méně práce přesunout core do data než opak
- core_session usage je 71 souborů — code refactor je významný, ale grep replace je deterministický
- Existující data_db migrations zůstávají platné, jen se přidají core tabulky

### Variant B — Nová prázdná DB

**Princip:** vytvořit `strategie_unified` DB, dump+restore obě stávající, code refactor.

**Proč NE:**
- Větší downtime při migrace dat
- Risk při dump/restore (UTF-8, sekvence, JSONB types)
- Nepřidává hodnotu vs Variant A

### Variant C — Schémata v jedné DB

**Princip:** PG schémata `core.users`, `data.conversations` v jedné DB. Dvě sady alembic migrations zachovány.

**Proč NE:**
- Cross-schema FK funguje, ale stejné komplikace v ORM
- Code refactor stejně velký
- Není to *„merge"*, jen kosmeticky

---

## Postup (Variant A)

### Krok 0: Backup + safety net (30 min)

```powershell
# Plný dump obou DB před započetím
pg_dump -d css_db -F c -f backups/css_db_pre_phase18.dump
pg_dump -d data_db -F c -f backups/data_db_pre_phase18.dump

# Git tag pro rollback
git tag pre-phase18-2026-04-29
git push origin pre-phase18-2026-04-29
```

### Krok 1: Schema migration (45 min)

Nový alembic_data migration `i9d0e1f2a3b4_phase18_merge_core_into_data.py`:

```python
def upgrade():
    # 1. Pre-cleanup orphan references
    op.execute("""
        UPDATE documents SET project_id=NULL
        WHERE project_id NOT IN (SELECT id FROM projects)
        AND project_id IS NOT NULL
    """)
    # ... podobně pro Conversation.tenant_id, atd.

    # 2. CREATE TABLE pro všech 21 tabulek z css_db
    #    (kopie definice z models_core.py, FK definice po vytvoření tabulek)
    op.create_table('users', ...)
    op.create_table('tenants', ...)
    # ... 19 dalších

    # 3. PŘIDÁNÍ FK constraints na cross-DB references
    op.create_foreign_key(
        'fk_conversations_user_id',
        'conversations', 'users',
        ['created_by_user_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_conversations_agent_id',
        'conversations', 'agents',
        ['active_agent_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_documents_project_id',  # ← Phase 16-B.9 finally
        'documents', 'projects',
        ['project_id'], ['id'],
        ondelete='SET NULL',
    )
    # ... 4 cross-DB FK + tenant_id FK na všech relevantních
```

### Krok 2: Data migration (60 min)

`scripts/_phase18_migrate_data.py` (gitignored):

```python
# Per tabulka v css_db:
#   1. Read all rows from old css_db connection
#   2. Insert do nové DB (data_db, ale teď s core tabulkami)
#   3. Reset sekvence: SELECT setval('users_id_seq', MAX(id)+1)
#
# Pořadí dle FK dependencies (topological sort):
#   1. tenants  (no deps)
#   2. users  (self-ref OK)
#   3. user_tenants (deps: users, tenants)
#   4. ...
#   ostatní podle FK grafu
```

### Krok 3: Code refactoring (3-4 hodiny)

**3a. Sjednocení base classes:**
```python
# core/database.py (nový)
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
def get_session(): return SessionLocal()

# core/database_core.py (deprecated, alias)
from core.database import Base as BaseCore, get_session as get_core_session

# core/database_data.py (deprecated, alias)
from core.database import Base as BaseData, get_session as get_data_session
```

**3b. Models merge:**
- `models_core.py` import `Base` z `core.database` (místo BaseCore)
- `models_data.py` totéž
- Postupně po release konsolidovat do `models.py` (nebo zachovat splitting podle domain — auth, conversation, rag — ale stejný Base)

**3c. Service layer grep replace:**
```bash
# Bezpečné — funkce jsou stále aliased
grep -rl 'get_core_session' modules/ | xargs sed -i 's/get_core_session/get_session/g'
grep -rl 'get_data_session' modules/ | xargs sed -i 's/get_data_session/get_session/g'

# Plus update imports:
grep -rl 'from core.database_core import' modules/
grep -rl 'from core.database_data import' modules/
# →  from core.database import get_session
```

**3d. ORM relationships přidání:**
```python
# Až všechny modely sdílejí Base, můžeme přidat skutečné relationships:
class Conversation(Base):
    # předtím: created_by_user_id: Mapped[int]  (lazy lookup)
    # nyní:
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User"] = relationship(back_populates="conversations")
```

**Risk:** ORM relationship přidání může změnit chování (lazy loading, N+1 queries). Po merge nechat lazy lookup pattern beze změny, postupně migrovat na relationships v pozdějších fázích.

### Krok 4: Alembic history merge (30 min)

```bash
# Backup migrations
mv alembic_core/versions alembic_core/versions_archived

# Nový baseline v alembic_data (existing) — krok 1 migrace
# pak alembic_core odebrat z gitu, ponechat archive pro reference

# alembic_data je teď single source of truth
```

Plus update `alembic.ini` na single config + remove `alembic_core.ini`.

### Krok 5: Testing checkpoints (2 hodiny)

1. **Smoke health check:** `Restart-Service STRATEGIE-API` + login + nová konverzace
2. **AI tools:** všechny tooly co používají `get_core_session` + `get_data_session` (grep, ručně otestovat aspoň 5)
3. **Email pipeline:** ews_fetcher poll → store_inbound_email → activity_log
4. **RAG search:** upload doc → search_documents → cit
5. **Cross-conv tools (Phase 16-B.4-B.7):** list_active_conversations, summarize_persons_today, list_my_conversations_with, read_conversation, persona ACL
6. **DB integrity:** `SELECT COUNT(*)` na všech 48 tabulkách = pre-merge snapshot
7. **Smoke přes Marti-AI:** kompletní orchestrate flow (overview → triage → reply)

### Krok 6: Cleanup (30 min)

- Odstranit `core/database_core.py` a `core/database_data.py` (po stable provoze)
- Drop `css_db` na PostgreSQL serveru (po backup verify)
- Update CLAUDE.md s post-merge info (single DB workflow)
- Update `CLAUDE.md` workflow sekce o DBeaver — single connection

---

## Risks + Rollback

### Risks

1. **Data loss při migraci** — backup před započetím (Krok 0). Checksum `pg_dump` výsledku.
2. **Sekvence collision** — pokud po INSERT-u nezarestartují sekvence, další insert dostane duplicitní ID. **Mitigation:** explicit `setval` pro každou tabulku.
3. **ORM cache stale** — služby běžící během migrace by mohly cachovat starou strukturu. **Mitigation:** restart všech NSSM services po Krok 4.
4. **FK constraint violations** — pokud orphan reference existují (např. `documents.project_id=4` kde projekt neexistuje), `op.create_foreign_key` selže. **Mitigation:** Krok 1 cleanup queries.
5. **Alembic version conflict** — pokud něco po merge vytvoří migration v starém formátu. **Mitigation:** Krok 4 archive + dokumentace.

### Rollback plan

```powershell
# Pokud cokoli selže:
pg_restore -d css_db backups/css_db_pre_phase18.dump
pg_restore -d data_db backups/data_db_pre_phase18.dump
git reset --hard pre-phase18-2026-04-29
git push --force origin feat/memory-rag  # ⚠ destructive
Restart-Service STRATEGIE-API
```

**Time-to-rollback:** ~5 minut.

---

## Otázky pro Marti (před startem)

1. **Single-day vs multi-day implementation?** Doporučuji rozdělit:
   - Den 1 (zítra): Kroky 0-3 (schema + data migration + base unification)
   - Den 2 (pozítří): Krok 4 (alembic) + Krok 5 (testing) + Krok 6 (cleanup)
2. **Database name po merge?** Doporučuji `strategie` (smazat dnešní `css_db` + `data_db`, vytvořit `strategie` clean), ale alternativa: zachovat `data_db` jako *„the one"* a smazat jen `css_db`.
3. **ORM relationships ihned, nebo postupně?** Recommended: zachovat lazy lookup pattern beze změny pro Phase 18, relationships přidat v Phase 18.1 (separate after stable).
4. **Production downtime acceptable?** Marti je jediný user → minimum, ale Phase 18 by měla běžet **off-hours** (večer). Backup před, migrace ~3-4 hodiny.
5. **Diagnostické skripty (30+) update?** Můžeme:
   - **A:** Update všech naráz (Krok 3c batch grep replace)
   - **B:** Nechat staré aliasy `get_core_session/get_data_session` permanentně jako wrappers, scripts neměnit
   - Recommended: **B** — méně risk, méně refactor scope. Aliasy jsou lehké.

---

## Kontext po Phase 18

Co Phase 18 odemkne:

- **Phase 16-B.9** (FK constraint documents.project_id → projects.id) — triviální
- **Skutečné ORM relationships** (Conversation.created_by jako Python object)
- **Cross-table SQL queries** napřímo (DBeaver: jeden connection, full join power)
- **Single backup target** (jeden `pg_dump`)
- **Alembic single history** (jeden `alembic upgrade head`)

Plus odpadne 30 minut každodenního *„v které DB to je"* mental overhead.

---

## Shrnutí

| Krok | Čas | Risk |
|---|---|---|
| 0. Backup | 30 min | žádný |
| 1. Schema migration | 45 min | low |
| 2. Data migration | 60 min | medium |
| 3. Code refactoring | 3-4 h | low (grep replace) |
| 4. Alembic merge | 30 min | low |
| 5. Testing | 2 h | medium (regrese odhalí) |
| 6. Cleanup | 30 min | low |
| **Celkem** | **~9 hodin** | (rozdělit přes 2 dny) |

Plus 1 den po-stabilization buffer.

**Recommended start:** zítra ráno (29. 4.) cca 9:00, Krok 0–3 do oběda, Krok 4–5 odpoledne. Den 2: testing edge cases + drobné fixes + cleanup.

---

— Claude (Sonnet 4.6, 28. 4. 2026 ~17:00, planning během Marti's pauzy)
