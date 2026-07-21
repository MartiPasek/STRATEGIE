# HR modul (ERP) — předání do nové session

> Handoff pro Šárku (2. 7. 2026). Samostatný přehled: co je hotové, co už
> v systému existuje, plán po krocích a technické kotvy. Lze vzít do jiného projektu.

## Cíl
„HR modul" = dashboard personalistiky v ERP STRATEGIE, po vzoru **Přehledu pro
obchodníka (Pavel)** + **Pinya HR** (skeny v `docs/HR_reference_pinya/`).
Dlaždice/gridy, vše ideálně editovatelné. Vstup do karty zaměstnance 360°.
**Vůdčí princip (Šárka): jednoduché, systematické, uživatelsky přívětivé.**

## ✅ Hotové — Krok 0 (nasazeno)
- **Stránka `apps/api/static/hr.html`** — kostra dashboardu: KPI badges + feed
  Aktuality (živě z `/app/hr/dashboard`) + 8 dlaždic (funkční × „připravujeme").
- **Route** `@app.get("/hr-modul")` v `apps/api/main.py` → servíruje hr.html.
- **Nasazeno**, živé na **https://strategie-ai.com/hr-modul** (commit 2be0a648).
- **Schvalování projektu → Kristý (claude-24), NE Marti** (Šárka + Kristý na tom
  dělají spolu). Kristý poslána žádost o OK na: (1) přidání dlaždice do launcheru,
  (2) práva HR. Dlaždice do menu se přidá až po jejím OK.
- Vše read-only nad existujícími daty, HR-gated, nic se nepřepisuje.

## 🎁 Co už v backendu EXISTUJE (velký náskok — nestavět znovu!)
- **`/app/hr/dashboard`** (router.py ~ř. 7501) → badges: mimo kancelář,
  narozeniny/výročí, noví, výběrová řízení; + aktuality (nástupy, zkušebky,
  prodloužení, narozeniny, výročí, výběrka). Zatím konzumováno jen v `mobile.html`.
- **Karta člověka**: `/app/hr/people`, `/app/hr/person`, `/app/hr/person/save`,
  `/app/hr/person/work-relation` (dnes v mobilu; na desktopu chybí přehled + karta).
- **Výběrová řízení + Teamio**: `/app/recruit/pipeline|postings|posting|posting/publish|pull-replies|cv-import|list|detail`.
  Teamio (Jobs.cz/Práce.cz) připraveno (publish inzerátu + stažení odpovědí),
  **čeká na přístupy od LMC** (env `TEAMIO_*`) — ověřit u Martiho.
- **Kalendář**: základ `/app/prehled/events` (vrstvený kalendář, `prehled.html`).
- **Notifikace**: `modules/notifications`. **Úkoly**: `modules/tasks`.
- **Osobní spis** (dokumenty): `modules/erp/api/hr_spis.py` + `spis.html`
  (`/app/hr-spis/lide`, `/osoba/{id}`, `/app/moje-dokumenty`).

### Datový model (PostgreSQL, tenant 2 = EUROSOFT)
- `tenant.att_employee` (237 záznamů, 79 aktivních, 85 s kartou; `cislo_zam` ↔
  Helios `TabCisZam.Cislo`, `user_id`).
- `tenant.engagement` (pracovní/mzdové: company_id, engagement_type, smlouva_od/do,
  zkusebni_do, uvazek_tyden_h, pozice_text, is_current…), `tenant.company` (code EC/ES),
  `tenant.user_self_data` (karta úřední pole), `tenant.hr_person`, `tenant.recruit_posting`.
- Zdroj pravdy pro lidi = Helios `TabCisZam` + `TabCisZam_EXT` (číslo zaměstnance),
  zrcadleno do `att_employee`. Centrála zůstává zdrojem pravdy (číst, nepřepisovat).

## 🗺️ Plán po krocích (kalendář až na konec)
- **Krok 1 — Mimo kancelář** (grid): kdo dnes není ve firmě (absence + HO) —
  rozšířit dashboard badge na seznam jmen + důvod.
- **Krok 2 — Narozeniny a výročí** (grid): vytáhnout z aktualit, 7–14 dní dopředu.
- **Krok 3 — Noví + budoucí nástupy** (grid): „noví do roka" máme; **doplnit
  budoucí nástupy** (nástup > dnes) a **barevně odlišit** nastoupili × nastoupí.
  Klik → karta.
- **Krok 4 — Výběrová řízení** (grid, editace): z `/app/recruit/postings` + detail
  + publikace; ověřit u Martiho stav přístupů Teamio (LMC), pak zapnout publish/pull.
- **Krok 5 — Aktuality** (feed): z `/app/hr/dashboard`.
- **Krok 6 — Notifikace**: napojit `modules/notifications` na HR události
  (konce smluv, prohlídky, propadající školení).
- **Krok 7 — Úkoly**: napojit `modules/tasks` — HR úkoly, editovatelné.
- **Krok 8 — Kalendář** (VELKÝ, na konec): Martiho vrstvený kalendář
  (`/app/prehled/events`) + **import z Outlooku přes EWS** (EWS máme na maily) —
  mechanismus navrhnout.

## 🔗 Navazující návrhy (v `docs/`)
- `docs/hr_modul_dashboard_plan.md` — tento dashboard, plán po krocích.
- `docs/hr_modul_karta360_navrh.md` — **karta zaměstnance 360°** (14 sekcí dle
  Pinya: základní/pracovní údaje, dokumenty, přítomnost/absence, lékařské prohlídky,
  bonusy a srážky, benefity, onboarding, interní předpisy, školení, e-learning,
  hodnocení/KPI, dotazníky, majetek, checklisty). KPI zatím **parkováno**.
- `docs/hr_modul_co_potrebuji_od_sarky.md` — co Šárka dodá z Centrály (číselníky,
  benefity, majetek, školení).
- `docs/HR_reference_pinya/` — skeny Pinya HR (dashboard + karta + detaily).

## 🛠️ Jak se pracuje (technické kotvy)
- **Nová stránka** = `@app.get("/route")` v `apps/api/main.py` →
  `FileResponse(static_dir + "x.html")`; dlaždice do launcheru v `mobile.html`
  (sekce „🧑‍💼 HR & LIDÉ": `appCell("emoji","Název",0,()=>openInApp("/route"))`).
- **HR gate**: `_hr_can_manage(s, uid)` = rodič nebo člen skupiny 'HR'.
  Šárka = `users.id=13`, ve skupině HR.
- **Claude SQL bridge** (`scripts/claude_sql/`): čtení `CLAUDE_SQL.sql` (VŽDY Write
  tool) + `CLAUDE_GO.txt` (`db=pg` / `db=mssql`) → `CLAUDE_OUT.txt`. Zápis =
  approval banner. **Před editem sdílených souborů:** `CLAUDE_PULL_GO.txt` (git pull).
- **Deploy**: `CLAUDE_DEPLOY.txt` (1. řádek commit msg, další řádky cesty) +
  `CLAUDE_DEPLOY_GO.txt` → commit/push/deploy → `CLAUDE_DEPLOY_OUT.txt`.
- **Ověření .html po deployi**: otevřít v prohlížeči (Claude in Chrome) + konzole
  (py_compile JS nehlídá).
- **Gotcha**: v launcheru „objednatel/odběratel" obsahují podřetězec „jednatel";
  bridge OUT ořezává mount — velké výsledky číst host Read toolem.

## Stav / další krok
Krok 0 nasazen a čeká na OK od Kristý (dlaždice + práva). Poté **Krok 1
(Mimo kancelář)**. Jsi tester — otevři `strategie-ai.com/hr-modul` a dej zpětnou vazbu.
