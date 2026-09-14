# Mobil, obrazovka Docházka: dlaždice „Nemocenská" a „Lísteček od lékaře" — celý průběh a stav k 14. 9. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Nemocenská a Lísteček od lékaře — co přesně dělají (stav 14. 9. 2026)

Rozbor zadal Jirka Honomichl 14. 9. 2026, zápis schválila Marti-AI (msg 15615).
Vše ověřeno téhož dne ze živých zdrojů: `g2007.soubor` (artefakt `apps/api/static_db/mobile.html`
a dílek `apps/api/static/mobile_parts/60_dochazka.js`), `g2007.python`
(`att_med_start`, `att_sick_end`, `att_sick_balance_h`, `att_ocr_fill_dochazka`),
jádro `modules/erp/api/router.py` a data v `tenant.att_sick_case` / `tenant.att_med_note`.

## Kde dlaždice jsou a kdo je otevře

Obě sedí na obrazovce **Docházka** v sekci **„NEMOC A LÉKAŘ"** (vlastní sekce od 8. 9. 2026,
protože mezi běžné dlaždice docházky nepatří — obě se teprve připravují).

**Jsou zamčené.** Vidí je všichni, mají v pravém horním rohu šedý zámeček.
Po ťuknutí se volá `GET /api/v1/erp/app/cockpit/access` a otevře se to **jen uživateli 20 (Jirka)** —
číslo je zapsané natvrdo ve funkci `_zamek()`. Ostatním se ukáže hláška
„… se připravuje. Jakmile bude hotová, odemkneme ji všem."
Poznámka v kódu (Jirka, 6. 9. 2026): zamčeno, dokud si obě obrazovky neprojde a neřekne odemknout.
**TODO v kódu:** nahradit natvrdo zapsané číslo uživatele oprávněním.

## Nemocenská — průběh od začátku do konce

1. Zaměstnanec nahlásí: číslo rozhodnutí o DPN (nepovinné), datum od, předpokládaný konec (nepovinné).
2. `POST /app/sick/start` (žije v jádře, ne v `g2007.python`) založí dva záznamy:
   `tenant.att_absence_request` (typ `sick`, stav `pending`, 8 h/den, schvalovatel z `_abs_resolve`)
   a `tenant.att_sick_case` (stav `novy`).
3. Zavolá `att_ocr_fill_dochazka` → na každý **pracovní den** rozsahu zapíše do `tenant.att_entry`
   **8 hodin** typu `sick` a **odstraní z toho dne všechny ostatní záznamy** (práce, režie, pauza).
   Záměr Martiho z 28. 6. 2026: kdo je nemocný, nemá mít docházku.
4. Schvalovatelům absence přijde zpráva do telefonu.
5. Dokud případ běží, hodinový automat `_ocr_extend_active` (volaný z `_att_sync_loop`) dopisuje
   další pracovní dny do docházky sám. Bere případy ve stavu `novy`/`probiha` bez `datum_do`.
6. Po uzdravení člověk doplní datum do → `att_sick_end` (živá logika v databázi):
   stav `ukonceno`, dopíše se celý rozsah do docházky a zpráva jde na **HR**
   (`_hr_prijemci` = rodiče + skupina HR, aktivní v tenantu), vedoucí ji dostane jen na vědomí.
   Doklad rozhoduje HR, ne vedoucí výroby (Marti-AI 5. 8. 2026).
7. `POST /app/sick/approve` (jen rodič nebo člen skupiny HR, kontrola `_hr_can_manage`) →
   případ `schvaleno`, žádost o absenci `approved` + `materialized`, člověku tiché potvrzení.
8. **Navazuje na mzdy:** `mzdy_status_check` porovnává tyto případy proti Heliosu a hlásí,
   když k nemoci chybí mzdová složka (203 / 213 / 882 / 106).

## Lísteček od lékaře — průběh od začátku do konce

1. Formulář: datum, čas od/do, typ (vyšetření / preventivní prohlídka / doprovod),
   u doprovodu jméno a vztah, zdravotnické zařízení a **povinně foto lístečku**.
2. `att_med_start` (živá logika v databázi) spočítá dobu z časů a rozpočítá krytí ve třech krocích:
   - **sick day** do výše zůstatku (`att_sick_balance_h`),
   - zbytek **lísteček do limitu** (podmínka `lekar_listecek_limit_h`, kaskáda smlouva → skupina →
     systém, výchozí 4 h),
   - co přeteče, je **neplacené**.
   Uloží řádek do `tenant.att_med_note` i s fotkou, stav `nahlaseno`.
3. Zpráva jde na **HR** (s cílovou obrazovkou `med_schval`), schvalovatelům absence jen na vědomí.
4. `POST /app/med/approve` (opět jen rodič nebo HR): stav `schvaleno`, HR smí rozpad hodin
   ručně přepsat. Člověku přijde tiché potvrzení.

## ⚠️ GOTCHA — schválený lísteček nikam nepokračuje

**Schválení lístečku nezapíše nic do docházky ani do mezd** — změní jen stav řádku
v `tenant.att_med_note`. Zůstatek sick days se od 17. 8. 2026 **záměrně počítá z docházky**
(`tenant.att_entry`, typ `sickday`), takže rozpad hodin, který se u lístečku zobrazí,
je **jen informace** — sick day se reálně odečte, až když se den zadá běžnou cestou přes docházku
(`sickday_lekar_apply`).

Ověřeno dohledáním **všech** čtenářů `tenant.att_med_note`: v `g2007.python` jen `att_med_mine`
a `att_med_start` (v `att_sick_balance_h` je název už jen v komentáři o opravě ze 17. 8. 2026),
v jádře jen `/app/med/photo`, `/app/med/inbox`, `/app/med/approve` a `/app/hr/med-overview`.
Žádný mzdový ani docházkový automat tu tabulku nečte.

## Kolika lidí se to týká (k 14. 9. 2026)

**Přes obě dlaždice zatím neprošel nikdo.**

- `tenant.att_med_note`: **1 řádek**, stav `nahlaseno`, ze 17. 6. 2026.
- `tenant.att_sick_case`: **4 řádky**, všechny ve stavu `ukonceno`, **žádný nemá `absence_request_id`** —
  tedy nevznikly v aplikaci, ale z automatu ČSSZ (`att_eneschopenka_to_sick`, neschopenky z datovky).

Až se dlaždice odemknou, platí pro každého, kdo je uvidí — proto je gotcha výše potřeba dořešit dřív.

