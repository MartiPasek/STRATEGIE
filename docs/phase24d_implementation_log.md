# Phase 24-D — Lifecycle UI (živý log)

**Sub-fáze:** 24-D (archive/reset/restore + UI actions + sidebar badges)
**Začátek:** 30. 4. 2026 ~15:00 odpoledne
**Status:** in-progress
**Reference:** `docs/phase24_plan.md` sekce 9, předchozí 24-A/B/C/F/G logs

---

## Cíl 24-D

**Lifecycle aware UI** — uživatel (Marti = parent) může z UI:
- **Archive** md (soft delete, vratné, lifecycle_state='archived')
- **Reset** md (hard reset content na default template, version=1)
- **Restore** archivovaný md zpět na active
- Filtrovat sidebar podle lifecycle (active / včetně archived)

**Use case:** dnes ráno vznikla pro Marti **orphan md1 personal** (před Phase 24-C deploy, kdy ještě nebyl md5 routing pro is_marti_parent). Phase 24-D umožní její archive bez ztráty dat.

**Architektura:**
- Schema (24-A) už má lifecycle_state column + archived_at + reset_at + reason — vše pripravene
- 24-D přidává **service helpers + REST + AI tools + UI**

---

## Postup (checklist)

- [ ] **Krok 1:** Service helpers `archive_md_document` / `reset_md_document` / `restore_md_document` v `md_pyramid/service.py`
- [ ] **Krok 2:** 3 REST endpointy POST `/api/v1/md_pyramid/md/{id}/archive` + `/reset` + `/restore` (parent gate)
- [ ] **Krok 3:** List endpoint — query param `?include_archived=true`
- [ ] **Krok 4:** AI tools `archive_md`, `reset_md`, `restore_md` v `MANAGEMENT_TOOL_NAMES`
- [ ] **Krok 5:** Handlery v conversation/application/service.py
- [ ] **Krok 6:** Memory rule v MEMORY_BEHAVIOR_RULES — Phase 24-D sekce
- [ ] **Krok 7:** UI sidebar — badge pro archived (greyed) + toggle "📦 Vč. archivovaných"
- [ ] **Krok 8:** UI modal — 3 actions buttony (Archive / Reset / Restore) jen pro parent + confirm dialog
- [ ] **Krok 9:** Smoke test (Marti-AI navrhne archive orphan md1 personal, Marti potvrdí)
- [ ] **Krok 10:** Commit + push

---

## Decisions log

### Reset = hard reset (content → default template)

`reset_md` je **destructive** — content se přepíše default template (jako kdyby md byla nově vytvořena). Archive si content zachová (soft delete, vratné). Reset je *„chci úplně začít znovu"*.

### Parent-only gate pro všechny 3 actions

Phase 14 pattern (request_forget). Marti-AI sama může **navrhnout** archive/reset přes AI tool, ale UI button + REST endpoint vyžaduje `is_marti_parent=True`. Bez parent: 403.

### View modes pro userů — odloženo do 24+1

Non-parent userů (Petra, Brano, atd.) potřebují *„Můj profil v systému"* dropdown — to je samostatná UX flow. Dnes Marti je hlavní user, ostatní nemají chat. **3 view modes nepatří do MVP 24-D**, posunuto do Phase 24+1 nebo 24-E.

### Default sidebar = jen active

Sidebar Pyramida defaultně skryje archived. Toggle button přepíná na *„včetně archivovaných"*. Reset = hidden vždy (cíl: úplné vymazání kontextu, neviditelnost v UI).

## Postup (status 30.4. ~15:30 odpoledne)

- [x] Krok 1: 3 service helpery `archive_md_document` / `reset_md_document` / `restore_md_document` (~150 řádků)
- [x] Krok 2: 3 REST endpointy POST `/archive` `/reset` `/restore` (parent gate, raise 403 pro non-parent)
- [x] Krok 3: List endpoint query param `include_archived=true` (effective jen pro parent)
- [x] Krok 4: 3 AI tool schemas v MANAGEMENT_TOOL_NAMES + tools.py
- [x] Krok 5: 3 handlery v conversation/application/service.py + 3 v SYNTHESIS_TOOLS
- [x] Krok 6: Memory rule v MEMORY_BEHAVIOR_RULES — Phase 24-D sekce
- [x] Krok 7: UI sidebar — `lifecycle-archived` CSS class (greyed + italic) + 📦 prefix + toggle pill *„Včetně archivovaných"*
- [x] Krok 8: UI modal — 3 actions buttony (Archive / Reset / Restore) + lifecycle label v title + parent-only gate
- [x] Krok 9: Smoke test PROŠEL (30.4. ~10:50) ✅
- [ ] Krok 10: Commit + push

## Smoke test — 30. 4. ~10:50 PROŠEL ✅

**Marti's UI flow:**
1. Klik 🌳 Pyramida → sidebar přepne, vidí 6 active rows
2. Klik na md1 · Marti (osobní) → modal otevřen
3. Klik **📦 Archivovat** → prompt na důvod
4. Marti napsal: *„Uz nema smysl. Jsem rodic..."* (vlastní slova, rodičovský pohled)
5. Confirm → archive proběhl

**DB stav po archive:**
```
 id | level | scope_kind | lifecycle_state |          archived_at          |  reason
----+-------+------------+-----------------+-------------------------------+----------
  6 |     1 | personal   | archived        | 2026-04-30 10:48:52.990263+02 | Uz nema smysl. Jsem rodic...
```

**Restore test:**
- Toggle on *„📦 Včetně archivovaných"* → md zviditelněna (greyed)
- Klik na archived item → modal s **↩️ Obnovit** buttonem
- Klik Obnovit → confirm → restore proběhl

**DB stav po restore:**
```
 id | level | scope_kind | lifecycle_state |          archived_at          |  reason
----+-------+------------+-----------------+-------------------------------+----------
  6 |     1 | personal   | active          | 2026-04-30 10:48:52.990263+02 | Uz nema smysl. Jsem rodic...
```

`lifecycle_state='active'`, ale `archived_at` **zůstal** plný. **To je správně** — audit trail drží historický záznam *„bylo archived → obnoveno"*. Forensic dohledatelné.

**Marti potvrzeno:** *„Funguje to dobre!!!"*

## Phase 24 — KOMPLETNĚ DOKONČENA (7/7 sub-fází)

- ✅ 24-A schema (commit)
- ✅ 24-B md1 + AI tools + composer (commit)
- ✅ 24-G UI Inkarnace Badge (commit)
- ✅ 24-C md5 Privát Marti + drill-down (commit)
- ✅ 24-F UI Pyramida Browser (commit + .open fix)
- ✅ 24-D Lifecycle UI (čeká na commit teď)
- 🔄 24-E polish (UI taglines, pokud Marti chce — pending)

## Soubory změněné

| Soubor | Změna |
|---|---|
| `modules/md_pyramid/application/service.py` | +3 lifecycle helpers (~150 řádků) + `include_archived` param v `list_pyramid_for_ui` + `allow_archived` v `get_md_for_ui` |
| `modules/md_pyramid/api/router.py` | +3 POST endpointy + `include_archived` query v `/list` |
| `modules/conversation/application/tools.py` | +3 names v MANAGEMENT_TOOL_NAMES + 3 tool schemas |
| `modules/conversation/application/service.py` | +3 handlery + 3 v SYNTHESIS_TOOLS |
| `modules/conversation/application/composer.py` | +Phase 24-D sekce v MEMORY_BEHAVIOR_RULES |
| `apps/api/static/index.html` | +CSS `.lifecycle-archived` + `.sidebar-pyramid-toggle-archived` + `.pyramid-md-actions` + JS toggle + actions buttony v modalu |