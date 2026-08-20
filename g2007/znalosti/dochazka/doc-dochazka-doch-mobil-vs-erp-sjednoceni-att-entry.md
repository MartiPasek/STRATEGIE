# Dochazka: mobil "Dochazka po zakazkach" vs ERP "Opravy" sjednoceni na att_entry (interim 27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Problem Blaha: mobil ukazoval jina cisla (hodiny i zakazky) nez ERP
Overeno v kodu i datech (27.7.2026, i28 Jirka), v souladu s emailem Marti Paska 26.7. (att_entry = jediny zdroj pravdy pro hodiny).

## Kde se data berou (dve ruzne tabulky)
- ERP "Opravy dochazky" (/app/attendance/fix/day) = tenant.att_entry (pichnuti + opravy; zakazka=project_ref, hodiny=hours). Hrube bloky, MA DUPLICITY.
- Mobil "Dochazka po zakazkach" (/moje-dochazka -> /app/dochazka/moje) = drive: hlavicka z att_day_summary (mimo!), radky z tenant.vyroba_work (rozpad z work_alloc = "overlay prirazeni prace MIMO dochazku", router.py ~26851). Att_entry_id byval prazdny (nepropojeno) -> "dve reality".

## Proc se lisily (Blaha 24.7)
att_entry 8,02 h (VR10700 3,20 blok + VR10703 + VR10713 + Rezie) vs vyroba_work 5,24 h (VR10699/94/00/01/02 jemne). Jiny cas, jine zakazky, jiny pocet radku. Att_entry = presnost hodin ale hrube/chybejici zakazky (nekdy cely den jen "Rezie"). Vyroba_work = detailni zakazky ale spatne hodiny/rozsah.

## RESENI (commit b407938b, endpoint /app/dochazka/moje, pro VSECHNY)
Hlavicka dne = MZDOVE HODINY z att_entry pocitane STEJNE jako ERP:
- SLOUCENI prekryvu presence intervalu (kvuli duplicitam: 2x stejna smena da 8h ne 16h) minus prestavky uvnitr prace.
- POZOR: NEscitat ulozene att_entry.hours (da 8,09 kvuli zaokrouhleni/duplicitam). Pocitat z casu started_at/ended_at pres merge -> 8,02 = ERP.
Zakazky dole ZUSTALY z vyroba_work (detail se neztrati). Dopocet radek "REZIE / Neprirazeny cas" = mzdove hodiny - soucet zakazek -> radky + neprirazeny = hlavicka (sedi). att_day_summary se prestal pouzivat.

## GOTCHA: proc NEsel "prepnout mobil cely na att_entry" (varianta A zavrhnuta)
att_entry ma na spouste dni jen "Rezie" bez zakazek (Blaha 23.7 = 7,99 h rezie) + duplicity -> prepnutim by se rozbil rozpad zakazek. Proto HYBRID: hodiny z att_entry, zakazky z vyroba_work.

## Overeno
Zive v Chromu (Blaha 24.7 mobil 8,02 = ERP 8,02) + 218 clovekodnu (prumer 7,24 h; 3 dny >15h = jen admin ucty Marti+Jirka, ERP je ma stejne = konzistentni ne bug).

## Cil Q4 (skutecna naprava): vyroba_work jako PROJEKCE att_entry (plnit att_entry_id, cist pres vazbu ne minutovy match). att_entry_id uz 95,5% vyplneno (z 0%). Interim vyse je nadstavba do te doby.

