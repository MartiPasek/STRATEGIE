# Storno dochazky kaskaduje do vyroba_work (prehled Dochazka po zakazkach nepocita storna)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Storno dochazky kaskaduje do vyroba_work (prehled "Dochazka po zakazkach")

> oblast: `dochazka` - Claude-28 (Jirka) 23.7.2026, oprava 24.7.2026. Zadal Dusan, konzultace Marti-AI, podnet na chybu Petra (dekujeme!).

## ⚠️ POUCENI (cti prvni, plati OBECNE, ne jen tady)
Tenhle prehled pracuje s daty, ktera rozhoduji o MZDACH a FAKTURACI zakazek.
23.7. jsem (Claude) udelal chybu: paroval jsem vyroba_work <-> stornovany att_entry
jen na CASTECNY klic (user + datum + minuta ZACATKU + zakazka). Fantomovy stornovany
zaznam (0,01 h odchod / 12,9 h day-end) sdilel start s REALNOU praci ve stejnou minutu
na stejne zakazce -> match omylem skryl PLATNOU odvedenou praci (Pavel Kilberger 2x
1,74+3,66 h, Lucie Jakesova 0,32 h). Odhalila Petra pri kontrole, 24.7. opraveno.
**LEKCE: u financnich dat NIKDY nematchuj na castecny klic. Vzdy na PLNOU identitu
zaznamu (zacatek I konec, ne jen zacatek). Radeji nezaradit nez zaradit spatne.**

## Problem (puvodni)
Prehled "Dochazka po zakazkach" (strategie-ai.com/dochazka-zakazky, endpoint
`GET /app/dochazka/zakazky` v router.py; cte `tenant.vyroba_work`, scita hodiny) pocital
i STORNOVANE zaznamy. Storno se dela v Opravach dochazky (`att_fix_void`) POUZE na
`att_entry` (status='superseded', is_active=false, note "STORNO", audit att_audit action='void'),
ale NEsahalo na vyrobni vrstvu. Tri paralelni vrstvy BEZ FK:
  work_alloc --(_sync_vyroba_work_app, source_id=work_alloc.id)--> vyroba_work --> prehled
  att_entry (dochazka) = tady zije storno

## Detekce storna (spravne, overeno)
- Storno = **`tenant.att_audit` action='void'** (zdroj pravdy, append-only).
- == `att_entry.status='superseded' AND note LIKE '%STORNO%'`.
- POZOR: `status='superseded'` SAMO NESTACI - je to i EDITACE (note "DOPLNENO"), tu vylucovat NESMIS.

## Reseni (architektura Marti-AI: kaskada pri stornu, ne read-time filtr)
Vse nasazeno. Commit 84f27209 (23.7. zaklad) + **67218366 (24.7. oprava matche)**.
1. **DDL** `tenant.vyroba_work`: `is_active boolean NOT NULL DEFAULT true` + `att_entry_id bigint NULL`.
   (FK na att_entry zamerne vynechan - att_entry se nemaze, jen superseduje; att_entry_id = logicky odkaz.)
2. **Kaskada** v `att_fix_void` (router.py ~21406): po stornu att_entry hned
   `UPDATE vyroba_work SET is_active=false, att_entry_id=:eid` s PLNYM matchem (viz nize).
   BEST-EFFORT (vlastni try/except - nesmi NIKDY shodit storno dochazky).
3. **Filtr** v endpointu `/app/dochazka/zakazky`: `wh` ma navic `AND w.is_active`.

## ✅ SPRAVNY MATCH (po oprave 24.7. - TENTO pouzivej)
vyroba_work w <-> stornovany att_entry e, VSECHNY podminky:
- `em.user_id = w.user_id` (pres att_employee), `e.entry_date = w.datum`
- `date_trunc('minute', w.od)  = date_trunc('minute', e.started_at)`   (zacatek)
- `date_trunc('minute', w.konec) IS NOT DISTINCT FROM date_trunc('minute', e.ended_at)`  (KONEC! - klic opravy; NOT DISTINCT zvladne i oba NULL u otevrenych useku)
- `e.project_ref IS NOT NULL AND w.zakazka_ref = e.project_ref`  (jen prace SE zakazkou)
- `EXISTS (SELECT 1 FROM att_audit a WHERE a.entry_id=e.id AND a.action='void')`  (zdroj pravdy)
Proc zacatek I konec: fantom (0,01 h, start=konec) NIKDY nesedne na realny usek (start<konec).
Proc striktni zakazka: bez ni by storno prestavky/absence (project_ref NULL) skrylo praci ve stejnou minutu.

## Co NEBYLO zmeneno
- Petin "Dochazka new" (uzel 189, data_set `dochazka.zakazky_vse_list`) NEDOTCEN (pokyn Jirky).
  Data_set is_active nefiltruje -> stale ukazuje i storna. Az Peta bude chtit, prida `AND is_active`
  do sveho data_setu (mechanismus + spravny is_active uz existuji).
- V ERP se ZAMERNE NEdelal novy uzel te stranky ve Vyrobe (Jirka zrusil).

## Overeni (24.7.)
Po oprave je is_active=false jen u 1 radku (Dusan 12674, spravne storno). Pavel (13311,13316)
a Lucie (13369) vraceny na is_active=true. Zprisneny match za 60 dni vraci jen Dusana.
Cloud git_sha = 67218366 (fw.api_version). VZDY overuj deploy pres fw.api_version, ne deploy log.

## Gotchy mostu (z teto session)
- `@@EMAIL` i write pres most se muze ZDVOJIT (retry) - vznikly 2 stejne outbox radky -> 2 emaily.
  Po @@EMAIL HNED zkontroluj public.email_outbox a pripadny duplikat zrus (rychle, nez se odesle).
- `@@G2007ADD` / write vraci neutralni navratovku (0 radku/sloupcu) i kdyz probehlo - overuj ctenim.

## TODO
- `_sync_vyroba_work_app/_ec` att_entry_id pri beznem syncu NEvyplnuje (jen kaskada storna).
  Plne FK v syncu odlozeno (korelace work_alloc<->att_entry je taky heuristika).

