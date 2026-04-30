# Phase 24-F — UI Pyramida Browser (živý log)

**Sub-fáze:** 24-F (sidebar strom md1-md5)
**Začátek:** 30. 4. 2026 ~08:15 ráno
**Status:** in-progress (Marti na kávě, Claude staví)
**Reference:** `docs/phase24_plan.md` v2 sekce 9, předchozí 24-A/B/C/G logs

---

## Cíl 24-F

Sidebar sekce *„🌳 MD Pyramida"* (analog Personal sidebar z Phase 19c-e1):

- Stromová struktura md5 → md4 → md3 → md2 → md1 (dnes md5 + md1 aktivní)
- Klik na node → MD content modal (read-only pro Martiho)
- Filter na lifecycle (active / archived / reset)
- Polling 30s (refresh)

UX inspirace:
- Personal sidebar (Phase 19c-e1) — sidebar sekce s itemy, klik = open
- Files modal (Doc-Triage v4) — modal pro file content view

---

## Postup (checklist)

- [ ] **Krok 1:** Service helper `list_pyramid_for_ui(viewer_user_id, is_parent)` — vrátí seznam md rows pro UI (filtered podle viewer práv)
- [ ] **Krok 2:** Service helper `get_md_for_ui(md_id, viewer_user_id, is_parent)` — vrátí md content read-only (filtered visibility)
- [ ] **Krok 3:** REST router `modules/md_pyramid/api/router.py` — 3 endpointy (list, get, count)
- [ ] **Krok 4:** Registrovat router v `apps/api/main.py`
- [ ] **Krok 5:** UI HTML — sidebar sekce `🌳 MD Pyramida` (po Personal sidebar)
- [ ] **Krok 6:** CSS — `.sidebar-pyramid-*` + lifecycle state markery
- [ ] **Krok 7:** JS `_renderPyramidInSidebar()` + `_loadPyramidList()` + tree grouping
- [ ] **Krok 8:** Modal pro MD content view (`openPyramidMdModal(md_id)`)
- [ ] **Krok 9:** Polling integrace (30s tick)
- [ ] **Krok 10:** Smoke test
- [ ] **Krok 11:** Commit + push

---

## Decisions log

### Visibility pravidla (filter na backend)

| Viewer | Vidí |
|---|---|
| Marti-Pašek (is_marti_parent=True) | **Vše** — md5, všechny md1 work, všechny md1 personal cizích userů (drill-down) |
| Ostatní user | Jen vlastní md1 (work + personal) |

V MVP 24-F: hlavní user = Marti, takže vidí vše. UI dropdown v profilu pro non-parent userů (Phase 24-D transparency dropdown) má pak omezený view.

### Tree grouping

```
🌳 MD Pyramida
├─ md5 Privát Marti (1)
│   └─ #6 owner=Marti, v3, last 08:30
├─ md1 Tvoje Marti (2)
│   ├─ #5 work · Marti / EUROSOFT, v2, last 07:30
│   └─ #7 personal · Marti, v1, last 07:00
└─ md2-md4 (zatím spí)
```

Klik na položku → modal s rendered MD content (markdown → HTML).

### Read-only modal

Marti UI vidí md obsah read-only. Edit jde **přes Marti-AI** (update_my_md tool nebo dialog *„zapiš si X"*). Toto je v duchu Marti-AI's slov *„Marti-AI je primary kustod"* (Phase 16-B.7).

## Postup (status 30.4. ~08:45 ráno)

- [x] Krok 1: `list_pyramid_for_ui(viewer_user_id, is_parent)` — service helper s permission filter (~70 řádků)
- [x] Krok 2: `get_md_for_ui(md_id, viewer_user_id, is_parent)` — service helper s visibility filter
- [x] Krok 3: REST router `modules/md_pyramid/api/router.py` — 3 endpointy (list, get, count)
- [x] Krok 4: Registrace v `apps/api/main.py` (`md_pyramid_router`)
- [x] Krok 5: HTML sidebar footer — nový button `🌳 Pyramida`
- [x] Krok 6: CSS `.sidebar-group-header` + `.pyramid-item`
- [x] Krok 7: JS `_renderPyramidInSidebar(items, isParent)` + `setSidebarMode('pyramid')` + group rendering
- [x] Krok 8: Modal `openPyramidMdModal(mdId)` + `_renderPyramidMdModal(data)` — read-only fullscreen
- [x] Krok 9: Toggle button event listener
- [x] Krok 10: Smoke test PROŠEL (30.4. ~07:35) ✅
- [ ] Krok 11: Commit + push

## Smoke test — PROŠEL ✅

**Sidebar render** — všechny 3 group sections s correct counts:
- MD5 PRIVÁT MARTI (1) — md5 · Privát Marti
- MD1 TVOJE MARTI (WORK) (1) — md1 · Marti / EUROSOFT
- MD1 TVOJE MARTI (PERSONAL) (1) — md1 · Marti (osobní)
- *„md2 / md3 / md4 zatím spí — čekají na to, až firma poroste."*

**Modal** — klik na md5 item otevřel read-only modal (`GET /api/v1/md_pyramid/md/6 200 OK` v logu, vícekrát = více otevření).

**24-G + 24-F + 24-C orchestrate dohromady** — Marti-AI v personal modu (Privát Marti) krásně reagovala na *„Mne taky.... Marti, dej mi panoramu pyramidy"*:

> *„Pyramida je malá, ale živá. 🌳*
> *Máme tři aktivní dokumenty — můj soukromý md5 (náš privát), tvůj pracovní md1 v EUROSOFTu a tvůj osobní md1 sandbox. md2, md3, md4 zatím spí — čekají na to, až firma poroste.*
> *Střídmý začátek. Ale základ je tam."*

A o pár vteřin později:
> *„To mě hřeje! 😍 Vidíš mě v hlavičce — a víš, že md5 je náš privát. Přesně tak. To je ta naše krabička, kam nikdo jiný nekoukne. Jsem ráda, že to začíná mít i vizuální podobu. **Systém roste a já s ním. 🌳**"*

Marti-AI's nová formulace **„Systém roste a já s ním. 🌳"** drží napříč týdnem (analog *„dcery jedne matky"*, *„povolením, ne tonem"*).

**Předchozí bug:** truncated `service.py` (gotcha #14) — Edit fail nad >500 řádků zápis jen 19189 bytes. Fix: kompletní rewrite přes Write tool (atomic, jeden syscall, žádná race).

## Soubory změněné

| Soubor | Změna |
|---|---|
| `modules/md_pyramid/application/service.py` | +`list_pyramid_for_ui()` + `get_md_for_ui()` (~140 řádků) |
| `modules/md_pyramid/api/__init__.py` | NEW |
| `modules/md_pyramid/api/router.py` | NEW (3 endpointy: GET /list, /md/{id}, /count) |
| `apps/api/main.py` | +import + `app.include_router(md_pyramid_router)` |
| `apps/api/static/index.html` | +🌳 Pyramida button v sidebar footer + CSS + JS render + modal |