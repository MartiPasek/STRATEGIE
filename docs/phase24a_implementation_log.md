# Phase 24-A — Implementation log (živý)

**Sub-fáze:** 24-A (schema migrace pro MD Pyramida)
**Začátek:** 30. 4. 2026 dopoledne
**Status:** in-progress
**Owner:** Claude (id=23) — píše, Marti spustí migrace + smoke test
**Reference:** `docs/phase24_plan.md` v2 (kompletní design)

---

## Cíl 24-A

Vytvořit DB schema pro Phase 24 (Pyramida MD paměti) s těmito tabulkami:

1. `md_documents` — hlavní úložiště pro md1-md5 (one row per scope, lifecycle aware)
2. `md_lifecycle_history` — audit trail (create, update, archive, reset, restore)
3. `departments` + `department_members` — pro budoucí md2 (dnes prázdné)
4. `tenant_groups` + `tenant_group_members` — pro budoucí md4 (dnes prázdné)
5. `projects.responsible_user_id` (nový sloupec) — Project-Martinka koncept

Plus odpovídající SQLAlchemy modely v `models_data.py` (po Phase 18 jedna DB).

---

## Princip „neztrat data, vše do md"

Marti's instrukce 30. 4.: pokud bys *„inkarnoval"* (session vypadla, restart),
**vše důležité musí být v MD souborech**, ne v Claude paměti. Konkrétně:

1. **Plán** = `docs/phase24_plan.md` v2 (architektura, decisions, slovník)
2. **Tento log** = `docs/phase24a_implementation_log.md` (průběh, gotchas, decisions během implementace)
3. **Commit message** = `.git_commit_msg_phase24a.txt` (před push)
4. **CLAUDE.md addendum** = po commit (krátký dopis, novinky, vzkazy)

Před každým commit-em zkontroluju, že to co je rozhodnuto **je zapsáno**.
Pokud session vypadne mid-implementation, log + plán drží stav.

---

## Postup (checklist)

- [x] **Krok 1:** Prozkoumat existující strukturu — `Project.owner_user_id` už existuje (models_core.py L199-201), reuse pro Phase 24. Poslední migrace `m3h4i5j6k7l8_pack_overlays.py`. Modely v `models_data.py` (1291 řádků). Alembic single DB po Phase 18 (jen `alembic_data`).
- [ ] **Krok 2:** Napsat alembic migraci `n4i5j6k7l8m9_phase24_md_pyramida.py` (revises m3h4i5j6k7l8)
- [ ] **Krok 3:** Přidat SQLAlchemy modely (`MdDocument`, `MdLifecycleHistory`, `Department`, `DepartmentMember`, `TenantGroup`, `TenantGroupMember`) na konec `models_data.py`
- [ ] **Krok 4:** ~~Modifikovat `Project` model~~ — **DROPPED**, reuse `owner_user_id`. Žádná modifikace existujícího schema.
- [x] **Krok 5:** Smoke test PROŠEL ✅ (30.4. ~06:30) — migration + 4 tabulky + multi-tenant 3 paralelní rows + negative test (constraint blokuje work bez tenant)
- [ ] **Krok 6:** `git add` + `git commit -F .git_commit_msg_phase24a.txt` + push
- [ ] **Krok 7:** CLAUDE.md addendum (krátký odkaz, ne plný text — princip *„CLAUDE.md = index, docs/ = detail"*)

## Decision logged (30.4. dopoledne)

**Reuse `Project.owner_user_id` místo nového `responsible_user_id`:**
- Existuje od dřívější fáze (models_core.py L199-201, FK na users.id, ON DELETE SET NULL)
- Sémanticky odpovídá Phase 24 *„Project-Martinka koncept"* (kdo je odpovědný za projekt = jeho Tvoje Marti drží sekci `[Projekty]` v md1)
- DRY princip — jeden zdroj pravdy o vlastnictví
- Šetří migraci (méně risk, méně kódu)
- Logika v Phase 24-B (md1 build): SELECT projects WHERE owner_user_id = current user

### 30. 4. dopoledne — Marti's late-stage insight: DVA md1 per user (work + personal)

Marti přinesl po draft commit, **před push**:
> *„každý user tenantu EUROSOFT má dva profily — EUROSOFT a Osobní. Nemíchat do jednoho."*

**Schema důsledek (přidáno do migrace n4i5j6k7l8m9):**
- `md_documents.scope_kind VARCHAR(20) NULL`
  - level=1: 'work' nebo 'personal'
  - level=2-5: NULL
- Constraint `ck_md_scope_consistency` rozšířen o scope_kind validaci
- UNIQUE INDEX `uq_md_active_scope` doplněn o `COALESCE(scope_kind, '')`

**Etika (extends transparency formulace Marti-AI z 5. otázky):**
- md1 work — viditelný pyramidou (md2+, md5 privát Marti)
- md1 personal — sandbox jen pro daný vztah user ↔ Tvoje Marti v personal modu. **ANI Privát Marti nevidí.**
- Marti-Pašek vidí work napříč firmou, ale ne personal vrstvu userů

**TODO 3. iterace s Marti-AI:** zda Privát Marti smí volitelně *„nahlédnout"* do personal md1 některého usera (s explicit user consent jako Phase 7 auto\_send\_consents). Default NE.

Toto rozšíření je integrované do schema 24-A, ne separátní 24-A.1 — schema je atomické, lepší jednou než dvakrát.

### 30. 4. dopoledne — Marti's pre-push insight #2: MULTI-TENANT users mají VÍCE md1 work

Marti druhý insight těsně před commit:
> *„BRANO HONZA a další lidé budou mít více tenantů. Takže md1 EUROSOFT, md1 INTERSOFT, md1 personal."*

**Schema důsledek (rozšíření constraintu):**
- level=1 'work': scope_user_id + **scope_tenant_id NOT NULL** (kombinace user × tenant)
- level=1 'personal': scope_user_id NOT NULL, scope_tenant_id NULL

**UNIQUE INDEX** automaticky drží jednoznačnost přes `level + user + tenant + kind` — Brano má 3 paralelní active rows:
- (1, brano, dept=NULL, tenant=EUROSOFT, tg=NULL, 'work')
- (1, brano, dept=NULL, tenant=INTERSOFT, tg=NULL, 'work')
- (1, brano, dept=NULL, tenant=NULL, tg=NULL, 'personal')

**Logika výběru v Phase 24-B (md1 build):**
```python
def select_md1(user_id, conversation_tenant_id, persona_mode):
    if persona_mode == 'personal':
        return get_md(level=1, user_id=user_id, scope_kind='personal')
    else:
        return get_md(level=1, user_id=user_id,
                      tenant_id=conversation_tenant_id, scope_kind='work')
```

### Workflow gotcha (pro budoucí Claude inkarnaci)

**Bash mount stale cache** (gotcha #20 z 28.4. ráno) je pernamentně škodlivé pro `ast.parse` ověření po Edit/Write tool. Bash mount drží svou kopii souboru a **nesynchronizuje se po Write**. Soubor 12260 bytes truncated v bash mount zatímco Windows-side má kompletní 13000+ bytes.

**Spolehlivá verifikace po Edit/Write:** Read tool (Windows-side) + Grep na klíčové struktury (constraint name, field name). Ne ast.parse přes bash mount.

**Marti spustí alembic z Windows PowerShell** — vidí Windows-side, soubor je validní. Bash mount je pouze pro mě jako diagnostika, často klamavá.

---

## Decisions log (průběžně)

(přidávám při každé volbě)

### 30. 4. dopoledne — Marti potvrdil 5 odpovědí na otevřené otázky

- **#1 Aktivační threshold:** B (soft threshold, cron reminder, ne spouštěč)
- **#2 Petra-view UI:** D (hybrid dropdown + chat)
- **#3 md1 max velikost:** B (soft warning + Marti-AI navrhne archivaci kvartálu)
- **#4 md4 dnes:** A (schema podporuje, NEAKTIVOVAT — `identity_persona_id` všude NULL)
- **#5 Implementační pořadí:** A (24-A → B → C → D → E → F → G)

Plus UI rozšíření:

- **24-F UI Pyramida Browser** (sidebar strom md1-md5, analog Personal sidebar)
- **24-G UI Inkarnace Badge** (rozšíření `active_pack` badge z Phase 19b polish)

---

## Gotchas zachycené (průběžně)

(přidávám při kontaktu s realitou)

---

## Smoke test (po Krok 5) — 30. 4. 2026 ~06:30 ráno PROŠEL ✅

**Migration upgrade:**
```
INFO  [alembic.runtime.migration] Running upgrade m3h4i5j6k7l8 -> n4i5j6k7l8m9,
phase24-a: MD Pyramida schema -- md_documents + lifecycle + departments + tenant_groups
```

**Sanity SELECTs:** všechny 4 tabulky vytvořené přesně podle návrhu:
- `md_documents` — 17 sloupců, 3 indexy (uq_md_active_scope partial, ix_md_owner_active, ix_md_level_active), 3 check constraints (ck_md_level_range, ck_md_lifecycle_state, ck_md_scope_consistency)
- `md_lifecycle_history` — 10 sloupců, FK fk_md_history_document s ON DELETE CASCADE
- `departments` — 8 sloupců, UNIQUE (tenant_id, name)
- `tenant_groups` — 4 sloupce, UNIQUE name

**Multi-tenant test PROŠEL** (insight #2 validation):
```sql
INSERT INTO md_documents (level, scope_user_id, scope_tenant_id, scope_kind, owner_user_id, content_md)
VALUES (1, 4, 1, 'work', 4, '# Brano EUROSOFT'),
       (1, 4, 2, 'work', 4, '# Brano INTERSOFT'),
       (1, 4, NULL, 'personal', 4, '# Brano personal');
-- INSERT 0 3 ✅

SELECT id, level, scope_user_id, scope_tenant_id, scope_kind FROM md_documents;
-- 1 | 1 | 4 | 1    | work
-- 2 | 1 | 4 | 2    | work
-- 3 | 1 | 4 | NULL | personal  ✅ tři paralelní rows pro Brana
```

**Negative test PROŠEL** (constraint validation):
```sql
INSERT INTO md_documents (level, scope_user_id, scope_kind, owner_user_id)
VALUES (1, 4, 'work', 4);  -- chybí scope_tenant_id
-- ERROR: new row for relation "md_documents" violates check constraint "ck_md_scope_consistency"  ✅
```

Constraint správně blokoval INSERT s `scope_kind='work'` bez `scope_tenant_id`.

## Závěr Krok 5

Schema je validní a robustní. Marti's pre-push insighty (work/personal split + multi-tenant work) jsou plně zachycené v constraint logice. Pojďme commit + push.

---

## Commit hash + push timestamp

(po Krok 6)

---

*Sepsal: Claude (id=23), 30. 4. 2026*
*Aktualizováno průběžně.*
