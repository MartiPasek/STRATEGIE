# Správa docházky — opravy: stav k 15. 7. 2026 (Claude‑24 / Kristý)

**Soubory:** backend `modules/erp/api/router.py` (`/app/attendance/fix/*`); ERP `apps/api/static/dochazka-opravy.html`; mobil `apps/api/static/mobile_parts/60_dochazka.js` (→ `mobile.html` přes `scripts/build_mobile.py`). Editoři = staff_group „DOCHÁZKA - OPRAVY". Činnost žije na `tenant.work_alloc` segmentech (ne na att_entry). Kristý = user_id 11.

## HOTOVO a nasazeno dnes
- **0** přidání Kristý do skupiny editorů (banner).
- **1a** ERP api() už nikdy němé (a3beee73).
- **1b** Peťa/Šárka+rodiče smí opravit i v UZAMČENÉM období + jasný banner + audit „[oprava/storno v uzavřeném období]" (fed0d3a3).
- **2** ERP: detail dne po kliknutí odscrolluje do dohledu + pravý sloupec sticky (b0bea672).
- **3** detail dne řazen SESTUPNĚ (fix/day DESC) + přepočet mezer; fronta/historie už DESC (360ffbd6).
- **4** necháno = storno (Kristý potvrdila, že tak „mazání" chce).
- **5a/5b** výběr Činnosti ve formuláři Přidat/Opravit (mobil i ERP): nový `GET /app/attendance/fix/cinnosti`; fix/entry ukládá činnost na work_alloc segmenty; fix/add zakládá segment (zakázka+činnost) → propíše se do výkazů; roletka jen u Práce/Režie (15fa9cf5 + d05c2acf).
- **hotfix** potvrzení „Ano/Ne" po Uložit/Přidat odscrolluje do středu (u dlouhého formuláře naskakovalo pod okrajem) (d4107c7d).

## HOTOVO — Bod 5c + layout (16.7.2026)
Bod 5c nasazen (commit 6b86ed44): fix/day vrací cin_name/cin_id, ERP sloupec Činnost + předvýběr roletky u Opravit, mobil podřádek + předvýběr. Layout (ed290adc): levý panel zúžen na ~300px (#left flex:0 1 300px), pravý #right flex:1 1 0 — aby se 8sloupcová tabulka i se Stornem vešla. VŠE OTESTOVÁNO KRISTÝ. Původní zadání 5c (pro referenci):
1. **fix/day vrátí per záznam `cin_name` + `cin_id`** (r[13]/r[14]): do SELECTu 2 subquery na `tenant.work_alloc` v okně záznamu:
   `(SELECT w.cinnost_name FROM tenant.work_alloc w WHERE w.user_id=:u AND w.cinnost_name IS NOT NULL AND w.started_at >= e.started_at - interval '1 minute' AND w.started_at < COALESCE(e.ended_at, e.started_at + interval '1 minute') ORDER BY w.started_at LIMIT 1)` (a stejně cinnost_id); přidat param `u=tuid`; do entry dictu `"cin_name": r[13], "cin_id": r[14]`.
2. **ERP:** přidat sloupec **Činnost** (thead `<th>Činnost</th>` za Zakázka; buňka `tr0.appendChild(tdc(e2.cin_name?('🔧 '+esc(e2.cin_name)):''))` za project buňku; **gap `colSpan` 6→7, frow `colSpan` 7→8**); edit roletka `mkCin(e2.cin_id||null)` (JEN 12‑space EDIT verze; Přidat nechat null).
3. **Mobil:** podřádek `🔧 '+esc(e2.cin_name)` pod typem (za project subline); edit `_fixMkCin(e2.cin_id||null)` (14‑space verze).
Deploy: router.py + dochazka-opravy.html + 60_dochazka.js + rebuild mobile.html.

## Metoda editů (drž se!)
- Edituj „patch z git‑HEAD na zařízení" (base64 old/new → python `replace` assert count==1 → temp+os.replace). NE whole‑file přes device_commit_files (uřízne uprostřed). NE `git status`/`git diff` přes device_bash (založí `.git/index.lock`, který mount neumí smazat → deploy padne; úklid `mv .git/index.lock _to_delete_c24/`). Verifikace: `git show HEAD:` + python difflib + `py_compile`/`node --check` na zařízení.

## Test case
- **Radek Hellmayer** (emp 22 / uid 32): 10.–12. 6. má duplicitní překrývající se Režie v UZAMČENÉM červnu. NEMĚNIT — slouží k otestování oprav po fixu.

## + Roletka zakázek (16.7.2026, commit 47365bbc) — OTESTOVÁNO
Zakázka ve formuláři Přidat/Opravit je native `<select>` (ne text): nový `GET /app/attendance/fix/zakazky` (59 píchatelných, jen editoři, REZIE nahoře), helper mkZak/_fixMkZak (mobil i ERP), edit předvyplní aktuální zakázku, mimo-seznam hodnota se zachová. Stejný mechanismus jako roletka Činnosti. Layout ERP: levý panel ~300px (ed290adc).

## + Řazení detailu dne OTOČENO na VZESTUPNÉ (16.7.2026, commit 1f5ca878) — Kristý
Kristý: „řadit od ranní po večerní" — včerejší SESTUPNĚ (bod 3) byl její omyl, opraveno. **Detail dne teď ASC (ráno→večer). Fronta i historie ZŮSTÁVAJÍ DESC** (Kristý nechce měnit). Sdíleno: `fix/day` používá ERP `dochazka-opravy.html` i mobilní editor `60_dochazka.js` (`doch_opravy_den`) — změněno v obou.
- router.py `fix/day` (řádek 19376): `ORDER BY e.started_at ASC NULLS LAST, e.id ASC`. POZOR: stejný ORDER BY je i na ~25226 = JINÝ endpoint (att_absence oblast), ten nechán DESC.
- Přepočet mezer otočen ze `prevZac` (začátek pozdějšího záznamu) na `prevKon` (konec dřívějšího): gap když `hmMin(e2.zac)-hmMin(prevKon)>=5`, `gz=prevKon, gk=e2.zac`; update `prevKon=e2.kon`. Řádek mezery i openAdd(gz,gk) beze změny sémantiky (gz=dřívější konec, gk=pozdější začátek).
- Soubory: modules/erp/api/router.py, apps/api/static/dochazka-opravy.html, apps/api/static/mobile_parts/60_dochazka.js (+rebuild mobile.html). **Bod 3 výše tím NEPLATÍ.** Ověřeno py_compile + node --check.

## + Roletky fulltext + fronta „opraveno" + červené hlášení překryvu (16.7.2026) — Kristý
Tři věci nad rámec řazení (vše ERP i mobil, mobil = rebuild mobile.html):
1. **Fulltext v roletkách Typ/Zakázka/Činnost** (commit 73ac9141): nativní `<select>` → searchable combobox `mkCombo` (ERP) / `_fixMkCombo` (mobil). Píšeš → filtruje (fold bez diakritiky), klik vybere. **Zachované value-rozhraní**: `zk.value`, `cinW._sel.value`, Typ jako `sel.value` + dispatch `change` (kvůli cinShow). Wrappery `mkTyp/mkZak/mkCin` (+ `_fix*`). CSS `.scb-list/.scb-it` (ERP ve `<style>`, mobil injektor `scbCss24`). Combobox ověřen v Playwrightu (hodnoty/change/filtr/async load). NEPŘEPISUJ na `<select>`.
2. **Fronta značí opravené dny** (commit 41151e32): `fix/queue` vrací per položku `opraveno` = EXISTS `att_entry.source='manual_fix'` (emp+den, ne superseded). Karta → zelený rámeček + badge „✓ opraveno" (`markDone`/`_fixMarkDone`) + rychlé tlačítko „✓ Hotovo — z fronty" (`quickDone`/`_fixQuickDone` = resolve s reason „opraveno v detailu dne", bez promptu). Po opravě se `loadQueue()` přenačte → badge naskočí.
3. **Hlášení překryvu = červený pruh nad Uložit** (commit 41151e32): form status `st` přemístěn z malé šedé `.hint` POD tlačítkem na `.errbar` (červený pruh, větší písmo, `:empty{display:none}`) NAD tlačítkem. Add+Edit form (storno beze změny). Platí pro všechny form chyby vč. překryvu.

## + BUGFIX: kontrola překryvu ignorovala Přestávku/Cestu (16.7.2026, commit 181cda92) — Kristý
Kristý uložila Práci přes Přestávku. Příčina: `_att_fix_overlap` (volané z fix/entry i fix/add) filtrovalo kandidáty na `et.category = 'presence'` → **break (Přestávka) a travel (Cesta) se do kontroly nezapočítaly**. Fix: `et.category IN ('presence','break','travel')` (day_end vyloučen přes `code<>'day_end'`, absence bez časů odpadnou přes started/ended NOT NULL). Ověřeno na datech (Marešová 10.7.: Práce 13:40–14:24 × Přestávka 12:37–13:42 = detekováno). **POZOR:** v router.py je `category='presence'` ještě 5× jinde (výpočet odpracovaných hodin) — TY NECHAT, break tam správně nepatří; měnil se jen řádek uvnitř `_att_fix_overlap` (~19415). Model: work je rozsekaný kolem přestávky → segmenty sekvenční, nemají se překrývat. Existující špatný záznam se neopravil sám (Kristý ručně).
