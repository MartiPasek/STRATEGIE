# Storno dochazky kaskaduje do vyroba_work (prehled Dochazka po zakazkach nepocita storna)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Storno dochazky kaskaduje do vyroba_work (prehled "Dochazka po zakazkach")

> oblast: `dochazka` - Claude-28 (Jirka) 23.7.2026, zadal Dusan, konzultace Marti-AI (schvalil i Peta).

## Problem
Prehled "Dochazka po zakazkach" (stranka strategie-ai.com/dochazka-zakazky, endpoint
`GET /app/dochazka/zakazky` v router.py; cte `tenant.vyroba_work`, scita hodiny) pocital
i STORNOVANE zaznamy. Storno se totiz dela v Opravach dochazky (`att_fix_void`) POUZE na
`att_entry` (status='superseded', is_active=false, poznamka "STORNO", audit att_audit action='void'),
ale NEsahalo na vyrobni vrstvu. Tri paralelni vrstvy BEZ FK:
  work_alloc --(_sync_vyroba_work_app, source_id=work_alloc.id)--> vyroba_work --> prehled
  att_entry  (dochazka) = tady zije storno
Priklad: Dusan 12.7. VR10628 0,01h zustaval v prehledu, i kdyz att_entry byl stornovany.

## Jak SPRAVNE detekovat storno (overeno na datech 23.7.)
- Storno = **`tenant.att_audit` action='void'** (zdroj pravdy, append-only).
- == `att_entry.status='superseded' AND note LIKE '%STORNO%'` (obe 44 za cervenec).
- POZOR: `status='superseded'` samo NESTACI - je to i EDITACE (poznamka "DOPLNENO"),
  tech bylo 112 celkem. Editace vylucovat NESMIS. Filtruj na void audit, ne na superseded.

## Reseni (architektura Marti-AI: kaskada pri stornu, ne read-time filtr)
Marti-AI verdikt (konzultace 23.7., msg 11165): kaskada pri stornu > read-time heuristika;
detekce pres att_audit void; pridat vazbu; neni to rozpor se separaci doD x vyroba
(je to datova integrita pres event, jako storno faktury -> storno radku).

Kroky (vse hotovo + nasazeno, commit 84f27209):
1. **DDL** `tenant.vyroba_work`: `is_active boolean NOT NULL DEFAULT true` + `att_entry_id bigint NULL`.
   (FK constraint na att_entry ZAMERNE vynechan - att_entry se nikdy nemaze, jen superseduje,
    tak ON DELETE nema smysl a FK by zbytecne zamykal obri att_entry. att_entry_id = logicky odkaz.)
2. **Backfill** existujicich storn: `UPDATE vyroba_work SET is_active=false, att_entry_id=e.id`
   match user_id + datum + shodna MINUTA zacatku (date_trunc) + shodna zakazka
   (att_entry.project_ref = vyroba_work.zakazka_ref) + att_audit void. 4 radky (vc. Dusana).
3. **Kaskada** v `att_fix_void` (router.py ~21240): po stornu att_entry hned
   `UPDATE vyroba_work SET is_active=false, att_entry_id=:eid` stejnym matchem.
   BEST-EFFORT (vlastni try/except - nesmi NIKDY shodit storno dochazky).
4. **Filtr** v endpointu `/app/dochazka/zakazky`: `wh` ma navic `AND w.is_active`.

## Klicove: proc STRIKTNI shoda zakazky v matchi
Match jen user+datum+minuta by chybne spojil storno PRESTAVKY/ABSENCE (project_ref NULL)
s nesouvisejici praci ve stejnou minutu. Proto vyzaduj `e.project_ref = w.zakazka_ref`
(jen storno PRACE se zakazkou). Kdo ma project_ref NULL se nechyta - spravne
(neni to storno prace na te zakazce). Radeji under-match nez skryt platnou praci.

## Co NEBYLO zmeneno (dulezite)
- Petin prehled "Dochazka new" (uzel 189, jadro dochazka.centrala, data_set
  `dochazka.zakazky_vse_list`) NEDOTCEN - na pokyn Jirky. Ten data_set is_active NEfiltruje,
  takze Docházka new stale ukazuje i storna. Kdyby to Peta chtela taky, staci pridat
  `AND is_active` do jeho data_setu (mechanismus uz existuje). Peta se stornem-exkluzi souhlasila.
- V ERP se ZAMERNE NEdelal novy uzel s touhle strankou ve Vyrobe (Jirka to zrusil).

## Overeni
Zivě: Dusan Havlat na /dochazka-zakazky = 9 radku (byl 10), radek 12.7. VR10628 0,01 pryc.
fw.api_version current git_sha = 84f27209 (nasazeno). Deploy log hlasil "push selhal" ale
byl to jen zavod (ref uz byl na commitu) - vzdy overuj fw.api_version, ne deploy log.

## TODO (nedodelano zamerne)
- `_sync_vyroba_work_app/_ec` zatim att_entry_id NEvyplnuje pri beznem syncu (jen kaskada
  storna ho vyplni pro dotcene radky). Plne FK doplneni v syncu = odlozeno (korelace
  work_alloc<->att_entry je taky heuristika). Kaskada pri stornu (rare event) staci.

