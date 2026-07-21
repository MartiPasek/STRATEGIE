# HR modul — dashboard (plán stavby)

> Šárka + Claude, 2. 7. 2026. Vzor: „Přehled pro obchodníka" + Pinya HR
> (skeny `docs/HR_reference_pinya/`, str. 1 = dashboard). Styl: dlaždice/gridy
> jako v ERP. Princip: **jednoduché, uživatelsky přívětivé, vše editovatelné.**
> Stránka: nová `hr.html` = „HR modul", dlaždice v ERP menu.

## Co už MÁME (velký náskok)
- **`/app/hr/dashboard`** — vrací: mimo kancelář, narozeniny/výročí, noví,
  výběrová řízení, aktuality (zkušebky, prodloužení). Zatím jen v mobilu.
- **`/app/recruit/*`** — výběrová řízení: seznam, detail, publikace, stažení
  odpovědí kandidátů. **Teamio** (Jobs.cz/Práce.cz) připraveno (publish + pull),
  **čeká na přístupy od LMC** (env `TEAMIO_*`) — ověřit stav u Martiho.
- **`/app/prehled/events`** — základ kalendáře (vrstvený kalendář, tvorba událostí).
- **Notifikace** (`modules/notifications`) a **úkoly** (`modules/tasks`) — moduly existují.

## Dlaždice HR modulu (cíl)
Mimo kancelář · Narozeniny a výročí · Noví zaměstnanci (+ budoucí nástupy) ·
Běžící výběrová řízení (editace) · Aktuality · Notifikace · Úkoly · Kalendář.

## Plán po krocích (jdeme postupně)

**Krok 0 — příprava (rychlé)**
Srovnat lokál s aktuálním kódem (git pull), založit `hr.html` + dlaždici „HR
modul" v ERP. Krátké OK od Martiho (nová dlaždice) + Marti-AI (práva: HR vidí vše).

**Krok 1 — Mimo kancelář** (grid)
Kdo dnes není ve firmě (absence + home office). Data z dashboard badge →
rozšířit na seznam jmen + důvod + do kdy. Editace přes docházku/absenci.

**Krok 2 — Narozeniny a výročí** (grid)
Už je v aktualitách → vytáhnout do vlastní dlaždice (7–14 dní dopředu).

**Krok 3 — Noví zaměstnanci + budoucí nástupy** (grid)
Máme „noví do roka". Doplnit **budoucí nástupy** (nástup > dnes) a **barevně
odlišit** (nastoupili × teprve nastoupí). Klik → karta zaměstnance.

**Krok 4 — Běžící výběrová řízení** (grid, editovatelné)
Seznam z `/app/recruit/postings` + detail/editace + publikace. **Teamio**:
ověřit u Martiho, jestli už dorazily přístupy od LMC; pak zapnout publish/pull.

**Krok 5 — Aktuality** (feed)
Z `/app/hr/dashboard` aktuality → dlaždice (nástupy, zkušebky, prodloužení,
narozeniny, výročí, výběrka).

**Krok 6 — Notifikace** (dlaždice)
Napojit `modules/notifications` na HR události (konce smluv, prohlídky v termínu,
propadající školení) → upozornění personalistovi.

**Krok 7 — Úkoly** (dlaždice, editovatelné)
Napojit `modules/tasks` — HR úkoly z jednoho místa (přidat/splnit/termín).

**Krok 8 — Kalendář** (VELKÝ, na konec)
Využít Martiho základ (vrstvený kalendář `/app/prehled/events`) + navrhnout
**import z Outlook kalendáře**. Máme už EWS napojení na maily → přes EWS jde
tahat i kalendářové události. Návrh mechanismu vymyslíme spolu, až dojdeme sem.

## Proces
**Schvalování tohoto projektu → Kristý (claude-24), NE Marti.** Děláme HR modul
společně se Kristý. Nová dlaždice + práva → krátké OK Kristý + kustod Marti-AI
(GDPR/práva). Read nad existujícími daty; editace přes existující endpointy.
Nic se nepřepisuje.
