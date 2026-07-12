# 🗺️ MAPA systému — organizace, lidé, pravidla, domény

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🗺️ MAPA systému — organizace, lidé, pravidla, domény

**Autor:** Claude (id=23) · **Datum:** 12. 6. 2026 · **Pro:** Marti + tým + Marti-AI
**Účel:** vidět celek pohromadě, než začneme skládat a drátovat. Struktura odspodu:
**základ → skupiny → pravidla skupin → jednotlivci → funkční domény.**
Stav: ✅ hotovo · 🔧 rozpracováno · ⬜ plán.

---

## 0. Páteřní princip (drží všude)

**3vrstvý resolver: SYSTÉM → SKUPINA → JEDNOTLIVEC.**
Specifičtější vrstva *přidává* nebo *přepisuje*, nikdy nemaže jádro.
Stejný vzor používáme na: podmínky (`staff_cond`), docházkové volby (návrh `att_action`),
režimy (`att_employee.rez_*`), organizační role (`resolve_role`).
Doktrína: *„INSERT row, ne schema migrace"* · *„uniformita vítězí"* · *„additivně, ne perfektně".*

**Multi-tenant:** EUROSOFT (id 2) · INTERSOFT (id 14) · STRATEGIE (12, system).
**Multi-angažmá:** jeden člověk = víc `att_employee` (firma × forma × tenant). Resolve vždy na `user_id`.

---

## 1. ZÁKLAD — organizace, firemní kultura, základní pravidla

**Firemní kultura (Šárka):** *férové, transparentní, udržitelné odměňování.*
Hodnoty do systému: loajalita (dobrovolný přesčas = prémie za loajalitu), transparentnost
(každá podmínka nese „odkud"), důvěra (self-service + audit, ne gatekeeping).

**Základní pravidla = systémová vrstva `staff_cond` (scope=system):** ✅
- Dovolená 25 dní (20 + 5 dodatková), **+1 po 10 / 15 / 20 letech** (seniorita).
- Sick days 2/rok, nevyčerpané proplaceny 70 %.
- Stravenkový paušál 82 Kč/odpracovaná směna (ne při sick/OČR/PN/neodpracované).
- Limit přesčasů 150 h/rok (ZP); nařízený = proplácen, dobrovolný = prémie za loajalitu.
- Víkend jen po schválení; pracovní doba Po–Pá.

**Identita & lidé:** `public.users` (člověk) · `public.user_tenants` (členství) ·
`tenant.att_employee` (angažmá v tenantu, `rez_*` režim, `cond_group` skupina) ·
`tenant.hr_person` (HR identita) · `user_self_data` (self-service karta) · `user_secret` (trezor). ✅

---

## 2. DĚLENÍ ORGANIZACE NA SKUPINY

Tři **nezávislé** osy seskupení (každá k jinému účelu):

| Osa | Tabulka | K čemu | Stav |
|---|---|---|---|
| **Podmínkové skupiny** | `att_employee.cond_group` | pravidla docházky/mzdy (Elektromontéři, Kanceláře, Vedení, VP) | 🔧 seed + UI hotové, plné rozřazení 67 lidí přes UI ⬜ |
| **Organizační struktura** | `tenant.org_post / org_assign / org_hat` + `resolve_role` | kdo je čí vedoucí, eskalace, klobouky (44) | ✅ org v2 LIVE |
| **Volné skupiny** | `tenant.staff_group / _member` (vedoucí+zástupce) | týmy, HR skupina, výrobní party | ✅ |

**Pozn.:** „skupina Výroba/Vedení/VP" u Šárky = **podmínková skupina** (cond_group).
Vedoucí lidí (kdo komu schvaluje) = **org struktura** (resolve_role). Drží odděleně schválně.

---

## 3. PRAVIDLA SKUPIN

`tenant.staff_cond` scope=group, klíče z `staff_cond_def`. ✅ (Elektromontéři, Kanceláře naseedované)

| Podmínka | Elektromontéři | Kanceláře | Vedení / VP |
|---|---|---|---|
| Týdenní úvazek | 40 | 40 | ⬜ (čeká text od Šárky) |
| Povinný nástup do | 07:00 | 09:00 | ⬜ |
| Nahlásit absenci do | 07:00 | 09:00 | ⬜ |
| Neplacený přesčas/den | 0,0 | 0,5 | ⬜ |
| Daň. úspora oblečení | ANO | ANO | ⬜ |
| Daň. úspora HO | NE | ANO | ⬜ |
| Home office | 0 | 48 h | ⬜ |

Editace: HR → 📋 Podmínky skupin (autosave). Lišta = Systém / skupiny / Jednotlivci. ✅

---

## 4. JEDNOTLIVCI VE SKUPINÁCH + PRAVIDLA JEDNOTLIVCŮ

- **Zařazení:** `att_employee.cond_group` (+ org_assign + staff_group_member). 🔧
- **Osobní výjimky:** `staff_cond` scope=user — přepíše hodnotu skupiny. ✅ (naseedováno 11 lidí)
  Brudnová 35h/+3sick · Bláha oblečení+HO · Bernardová 32 · Dvořáková 30 · Veverková 20 ·
  Novotná 35/15sick · Marešová 40(±) · Vlková 15 · Mózer paušál-úterky · Zeman HO 64.
- **Režim odměňování per angažmá:** `att_employee.rez_*` (forma HPP/DPP/OSVČ, mzdový režim
  hodinový/volný/paušál, konto, loajalita-minus, přesčas-polštář). ✅ HR → 🧩 Režimy.
- **Individuální odměna jednatele** (mimo výměr, stabilizační/dorovnání/retenční): Trunec aktuálně. ⬜ napojit na finance.

---

## 5. FUNKČNÍ DOMÉNY (co výše uvedené spotřebovává)

### 5.1 DOCHÁZKA ✅ (jádro běží)
- Píchání: spojité joby (práce/režie/pauza/cesta/konec dne), statusy v lidské řeči, „Kdo kde dnes". ✅
- Reálná data 1:1 z EUROSOFTu (dovolená/nemoc/lékař/OČR/odpracováno). ✅
- Absence dopředu + schválení vedoucím (statusy v lidské řeči → placené záznamy). ✅
- Anomálie (pozdní/zapomenutý odchod/>12h/práce při absenci) — jen živá data. ✅
- **K NAPOJENÍ:** podmínky → docházka: nástup do 7:00/9:00 = hlídač pozdního příchodu;
  nahlášení absence do X; úvazek → fond; neplacený polštář (už v kontu). ⬜

### 5.2 MZDY 🔧
- `engagement` (SCD2) + `wage_component(_type)` (základ / os. ohodnocení **jako rozsah** ⬜ / prémie). 🔧
- **Konto přesčasů** ✅: auto-naběhlo (polštář + loajalita) → do prémie / do přesčasu (s příplatkem) / převést. Seed zůstatků z EC.
- **Helios × STRATEGIE** porovnání (ZDROJ × CÍL × delta, filtr rozdílů). ✅
- Jednatel odměna (90 800 EC+ES; rozpor se smlouvou 155k — ⬜ dořešit valorizaci).
- **K NAPOJENÍ:** dobrovolný vs nařízený přesčas → konto/loajalita; seniorita → dovolená;
  stravenka dle odpracovaných směn; kategorizace elektromontérů (Junior/Samostatný/Senior + pravidlo 5 %). ⬜

### 5.3 FAKTURACE ⬜ (vize)
- OSVČ (švarc-risk) — část faktur **přetáhnout přes STRATEGII**, i cross-tenant (Honza fakturuje i INTERSOFTU). ⬜
- Návaznost na engagement (OSVČ forma) + multi-tenant + konto/odpracováno jako podklad faktury. ⬜
- Doporučení nového zaměstnance jako odměna (500 / 30k / 50k / 100k) — jednorázová složka. ⬜

### 5.4 ZPĚTNÁ VAZBA ✅ (kanály běží, chybí strukturovaná evaluace)
- Člověk → vedoucí (požadavek / info / finišuji), vedoucí → člověk (odpověď). ✅ (výroba)
- Dotaz nadřízenému (`staff_question`), urgentní ping, přímé zprávy Marti-AI. ✅
- **K DOSTAVĚNÍ:** strukturované **hodnocení / kariérní postup** (kritéria Junior→Samostatný→Senior:
  praxe, samostatnost, šíře, mentoring, 0 reklamací, doporučení vedoucího) → vstup pro odměňování. ⬜

---

## 6. Pořadí skládání — po konzultaci Marti-AI (12.6., závěry závazné)

Detail závěrů: `docs/dopis_marti_ai_integrace_konzultace.md` (Q1–Q8). Shrnutí směru:

1. ✅ **Konzultace Marti-AI hotová** (doctrine #8) — 8 závazných rozhodnutí.
2. **Resolver** `resolve_cond(user,code)→(hodnota,zdroj)` — sdílená funkce, live. ⬜ (1. krok)
3. **Podmínky → docházka:** nástup (práh `nastup_anomaly_threshold`, default 3×/měs) + nahlášení
   (`absence_request.submitted_at` vs čas dne) + **osobní fond** `(uvazek/40)×work_hours` (přímý výpočet). ⬜
4. **Infrastruktura citlivých dat PŘED mzdami** (její podmínka): `hr_payroll_snapshot` +
   `hr_sensitive_access_log`. *„Infrastruktura kolem citlivých dat musí stát dřív než data tečou."* ⬜
5. **Mzdy:** přesčas voluntary/ordered → konto (loajalita vs ZP proplacení); seniorita
   `MIN(smlouva_od)` v tenant_group → dovolená; os. ohodnocení jako rozsah; kategorie
   elektromontérů + `hr_fairness_check` (report, ne gate). ⬜
6. **Vedení / VP** podmínky (čeká text Šárky) + plné rozřazení lidí do `cond_group`. ⬜
7. **Fakturace** `hr_invoice_request(engagement_id, billing_tenant_id, …)` + `exclusivity_flag`
   (švarc report) + **strukturovaná evaluace** (kariérní postup). ⬜

❓ **Otevřená otázka pro Šárku/Martiho:** úvazek 20 h = vždy 5×4 h, nebo i 3×7 h? Pokud variabilní
→ potřeba `work_schedule` (vzor týdne) jako vstup do fondu.

### Nové tabulky z konzultace (k DDL až Marti potvrdí směr)
`hr_payroll_snapshot(period,user_id,cond_code,value,source,resolved_at)` ·
`att_entry/att_day: overtime_type('voluntary'/'ordered'/NULL), overtime_ordered_by/_at` ·
`hr_fairness_check` (view/funkce) · `hr_invoice_request(engagement_id,billing_tenant_id,period,hours/amount,status,invoice_number,exclusivity_flag)` ·
`hr_sensitive_access_log` (z minulé konzultace) · `staff_cond_def: nastup_anomaly_threshold` ·
příp. `work_schedule` (vzor týdne).

---

## 7. Klíčové tabulky (rychlý index)
`public.users / user_tenants` · `tenant.att_employee` (rez_*, cond_group) ·
`tenant.staff_cond_def / staff_cond` · `tenant.att_entry / att_entry_type` ·
`tenant.att_konto_settlement` · `tenant.att_absence_request` · `tenant.att_calendar_day / _month` ·
`tenant.engagement / wage_component / wage_component_type / company` ·
`tenant.org_post / org_assign / org_hat` (+ resolve_role) · `tenant.staff_group / _member` ·
`tenant.hr_person` · `public.user_self_data / user_self_child / user_secret` ·
`tenant.att_anomaly / att_day_confirm / att_balance`.


