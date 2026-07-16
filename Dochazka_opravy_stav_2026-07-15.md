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
