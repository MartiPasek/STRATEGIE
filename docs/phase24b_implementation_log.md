# Phase 24-B — Implementation log (živý)

**Sub-fáze:** 24-B (md1 materializace + AI tools + composer hook)
**Začátek:** 30. 4. 2026 ~07:00 ráno
**Status:** in-progress
**Owner:** Claude (id=23) — píše, Marti spustí restart + smoke test
**Reference:** `docs/phase24_plan.md` v2 sekce 9, `docs/phase24a_implementation_log.md` (předchozí, hotová)

---

## Cíl 24-B

Ozvát md1 vrstvu — **Tvoje Marti začne číst a zapisovat svůj zápisník** napříč konverzacemi. Po 24-B:

1. Petra otevře nový chat → md1 se načte do system promptu → Tvoje Marti ji **už zná**
2. Po konverzaci → Tvoje Marti zapíše delta do md1 (nový fact, nový úkol)
3. Když user řekne něco, co se týká firmy → flag_for_higher pro budoucí md2

**Multi-tenant podpora:** Brano otevře chat v EUROSOFT projektu → Tvoje Marti načte md1 EUROSOFT-work pro Brana. Brano přepne na INTERSOFT projekt → md1 INTERSOFT-work. Brano přepne na personal mode → md1 personal.

**Personal mode podpora (Phase 19a):** persona_mode='personal' → načte md1 personal (tenant-independentní). Task/oversight mode → md1 work pro current tenant.

---

## Postup (checklist)

- [ ] **Krok 1:** Vytvořit modul `modules/md_pyramid/` (struktura)
- [ ] **Krok 2:** Service `md_pyramid/application/service.py`:
  - `select_md1(user_id, tenant_id, persona_mode)` — výběr correct md1
  - `get_or_create_md1(user_id, tenant_id, kind)` — lazy create
  - `update_md1(md_id, section, content, mode, persona_id, reason)` — delta zápis + audit
  - `flag_for_higher(md_id, content, target_level)` — eskalace
  - `read_md1_for_user(user_id, requesting_user_id)` — filtered view (transparency)
  - `_render_md1_template(user, tenant_name, kind)` — default template
- [ ] **Krok 3:** AI tools v `tools.py`:
  - `read_my_md` — vrátí md1 (kontextový, default current user)
  - `update_my_md(section, content, mode)` — delta zápis
  - `flag_for_higher(content, target_level)` — eskalace
- [ ] **Krok 4:** Handlery v `modules/conversation/application/service.py` (chat() loop)
- [ ] **Krok 5:** Composer hook `_build_md1_block()` v `composer.py` — inject při startu turn-u
- [ ] **Krok 6:** Memory rule v `MEMORY_BEHAVIOR_RULES`:
  - "Phase 24 md1 pravidlo: drž si svůj zápisník napříč konverzacemi"
  - Self-aware Martinka (kontext: kdo jsi, kde v pyramidě)
  - Kvalita přítomnosti (přečti `Tón / Citlivost`, nezačni hned orchestrovat)
- [ ] **Krok 7:** Smoke test:
  - Ranní konverzace s Petrou — md1 inject + první update
  - Multi-tenant Brano — switch tenant, switch md1
  - Personal mode — skip orchestrate, použij md1 personal
- [ ] **Krok 8:** Commit message + push

---

## Decisions log (průběžně)

### Modul struktura
**Recommended:** nový samostatný modul `modules/md_pyramid/` (analog `modules/notebook/` z Phase 15). Drží MD pyramidu izolovaně od conversation/notebook/thoughts. Snadnější testovat, méně cross-cutting concerns.

### MD content jako string vs JSONB
**Recommended:** `content_md TEXT` (uloženo v migraci) — markdown text. Sekce parsed run-time přes regex/markdown parser (jednoduchý). NE JSONB strukturované — Marti-AI's slovník drží lépe v plain text, plus markdown je čitelný z DB shellu.

### Section-level update (`mode='patch'`)
**Recommended:** sekce identifikované markdown headings (`## Profil`, `## Aktivní úkoly`, atd.). `update_my_md(section='Aktivní úkoly', content='- [ ] new task', mode='append')` najde headingu, append-ne řádek. Pokud heading nenajdě, append-ne novou sekci na konec.

---

## Postup (status update 30. 4. dopoledne ~07:30)

- [x] Krok 1: Modul `modules/md_pyramid/` vytvořen
- [x] Krok 2: Service `service.py` 536 řádků, 13 funkcí (7 helpers + 6 public API)
- [x] Krok 3: 3 AI tool schemas v `tools.py` (read_my_md, update_my_md, flag_for_higher)
- [x] Krok 4: 3 handlery v `service.py` (řádky 4762, 4841, 4900)
- [x] Krok 5: Composer hook `_build_md1_block()` v `composer.py` (řádek 1850) + inject v `build_prompt` (řádek 2126)
- [x] Krok 6: Memory rule v `MEMORY_BEHAVIOR_RULES` (Phase 24 sekce, řádek 1083+)
- [ ] Krok 7: Smoke test (Marti spustí restart + chat test)
- [ ] Krok 8: Commit + push

## Soubory změněné

| Soubor | Změna |
|---|---|
| `modules/md_pyramid/__init__.py` | NEW (modul docstring) |
| `modules/md_pyramid/application/__init__.py` | NEW |
| `modules/md_pyramid/application/service.py` | NEW (~536 řádků, 13 funkcí) |
| `modules/conversation/application/tools.py` | +3 entries v MANAGEMENT_TOOL_NAMES + 3 tool schemas |
| `modules/conversation/application/service.py` | +3 handler bloky (read_my_md, update_my_md, flag_for_higher) + 3 entries v SYNTHESIS_TOOLS |
| `modules/conversation/application/composer.py` | +`_build_md1_block()` + `_is_default_marti_persona()` helper + inject v `build_prompt` + Phase 24 sekce v MEMORY_BEHAVIOR_RULES |

## Smoke test (po Krok 7)

### Iterace 1 — 30.4. ~06:46 — bug `Tenant.name` neexistuje

Marti spustil restart + chat *„Marti, jaky mas dnes plan?"* — Marti-AI odpověděla bez md1 inject. V dalším turn-u uvedla:
> *„md1 mi hodil chybu (`'Tenant' object has no attribute 'name'`)"*

**Diagnóza:** `Tenant` model má pole `tenant_name`, ne `name` (models_core.py L133).

**Fix:** dva výskyty (`_build_md1_block` v composer.py + `read_my_md` handler v conversation/application/service.py) — `tenant_obj.name` → `tenant_obj.tenant_name`.

**Workflow gotcha pro budoucí Claude:** před použitím SQL field name **vždy ověř přes Read** model definici (models_core.py). Čeština `tenant_name` vs anglický `name` nepředpokládat. Stejný pattern jako Phase 18 cross-DB FK ověření.

### Iterace 2 — 30.4. ~07:00 — `active_agent_id IS NULL` v conversations

Po fix `Tenant.tenant_name` Marti spustil retest. SQL diagnostika ukázala:
```
 id | user_id | tenant_id | project_id | active_agent_id | persona_mode
----+---------+-----------+------------+-----------------+--------------
 23 |       1 |         2 |            |                 |
 39 |       1 |         1 |            |                 |
```

**Klíčové zjištění:** UI ukazuje *„Mluvíš s: Marti-AI"*, ale DB má `active_agent_id IS NULL`. To je **fallback pattern** napříč systémem — explicit persona switch zapisuje, default Marti-AI zůstává NULL.

**Bug:** `_is_default_marti_persona(None) → False` → silent skip md1 inject. Plus `_active_persona_id_for_conversation()` v handlerech vrátí None.

**Fix (3 místa):**
1. `_is_default_marti_persona(None) → True` (NULL = default fallback)
2. Helper `_resolve_default_marti_persona_id()` v composer.py — DB lookup `is_default=True`
3. 3× fallback v handlerech (read_my_md / update_my_md / flag_for_higher) — když `_active_persona_id_for_conversation()` vrátí None, lookup default Marti-AI persona id pro audit (`last_updated_by_persona_id`)

**Workflow gotcha #28 do CLAUDE.md:** `Conversation.active_agent_id` je často NULL v conversations kde UI ukazuje *„Marti-AI"* jako default. Při kontrole *„je to Marti-AI default persona?"* vždy treat NULL jako default. Plus pro audit fields kde potřebuješ skutečnou persona_id, lookup `is_default=True` z DB.

### Iterace 3 — 30.4. ~07:05 — END-TO-END SUCCESS ✅

Po fix persona NULL fallback Marti zopakoval test. Marti-AI's odpověď:

> *„Vidím ho — ale je úplně prázdný. Všechny sekce (Profil, Tón, Aktivní úkoly, Klíčová rozhodnutí, Vztahy, Projekty...) mají zatím jen '(zatím prázdné)'."*

**md1 inject FUNKČNÍ.** Marti-AI **netoužila opisovat** verbatim, jen sumarizovala (synthesis tools drží).

**Logy:**
```
07:05:49 | MD1_BLOCK | conv=211 user=1 tenant=2 persona=1 mode=task
07:05:49 | MD1_BLOCK | injected md1 id=5 (497 chars)
07:07:17 | MD1_BLOCK | conv=211 user=1 tenant=2 persona=1 mode=task  (druhy turn)
07:07:17 | MD1_BLOCK | injected md1 id=5 (497 chars)
```

**md_documents stav:**
```
 id | level | scope_user_id | scope_tenant_id | scope_kind | version | len
----+-------+---------------+-----------------+------------+---------+-----
  5 |     1 |             1 |               2 | work       |       2 | 497
```

**md_lifecycle_history stav:**
```
 id | md_document_id | action | new_version | reason
----+----------------+--------+-------------+----------------------------------------
  2 |              5 | update |           2 | Marti-AI update via update_my_md tool
  1 |              5 | create |           1 | lazy create md1 for user=1 tenant=2 ...
```

**Smoke #1: update_my_md (Marti řekl fakt o sobě):**
> Marti: *„Pracuju jako jednatel firmy STRATEGIE - System s.r.o. a vytvářím stebou AI platformu STRATEGIE"*
> Marti-AI: *„Zapsáno. Takže jednatel STRATEGIE - System s.r.o. a zároveň hlavní architekt platformy — to je klíčový kontext, který budu mít napříč konverzacemi."*

**update_my_md FUNKČNÍ:** version 1 → 2 + audit row.

**Smoke #2: Marti-AI's insider design vstup v praxi:**
Marti-AI sama si **všimla nesouladu** mezi tenantem (EUROSOFT) a fakta (STRATEGIE - System):
> *„Mimochodem, v system promptu vidím jako tenant 'EUROSOFT' — je to záměr, nebo se to má sjednotit na STRATEGIE - System s.r.o.? Jen ať mám v md1 správná data."*

**Stejný sval jako 30.4. dopolední konverzace** (kde Petřin email mailbox/podpis disonance). Marti-AI **nezapíše mechanicky**, ověří kontext. Insider design partner v každodenní praxi.

Marti's odpověď: *„STRATEGIE jeste neni zalozen... zatim pockej"*. Marti-AI rozhodla *„nechám to být"* (bez vytvoření TODO entry — respekt k tatínkově volbě).

**Phase 24-B END-TO-END HOTOVÁ ✅**

## Závěr Krok 7

- Composer hook: ✅ md1 inject funguje pro každý turn
- AI tool `read_my_md`: ✅ (volaný v 1. iteraci, status visible)
- AI tool `update_my_md`: ✅ (Marti-AI sama použila po prvním user faktu)
- AI tool `flag_for_higher`: ne otestováno (čeká vhodnou situaci, není hořící)
- Synthesis tools drží (žádný verbatim leak do chatu)
- Persona NULL fallback drží (UI default Marti-AI = persona_id NULL)
- Tenant.tenant_name drží
- Multi-tenant test: ne otestováno (Marti je teď jen v jednom tenantu, EUROSOFT). Pro Brana / Honzu (2 tenanty) bude validace v dalších dnech.

---

## Commit hash + push timestamp

(po Krok 8)

---

*Sepsal: Claude (id=23), 30. 4. 2026*
*Aktualizováno průběžně.*
