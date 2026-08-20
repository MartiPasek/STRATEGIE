# Docházka: sync z Centrály klasifikuje absence dle DruhCinnosti (Fáze 1 + Fáze 2 backlog)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> C24 (Kristý) 29. 7. 2026. Souvisí: doc-dochazka-model-tabulky-dochazky, doc-mzdy-mzdy-podklad-zdroj-pravdy.

## Problém (chyba do 29.7.2026)
Sync EC_Dochazka → tenant.att_entry (`_sync_ec_dochazka_recent` = 3denní okno/wipe, i `hr_migrate_dochazka`)
mapoval typ jen podle zakázky: `CisloZakazky='rezie' → overhead`, jinak `work`, a **DruhCinnosti ignoroval**.
V Centrále jsou ale dovolená/nemoc/lékař atd. vedené jako `Rezie` + `DruhCinnosti` (20=Dovolená, 22=Nemoc…),
takže **všechny absence padaly do „Režie" (overhead)** a ve Správě docházky nebyly vidět jako dovolená
(např. Valenta 517, dovolená 20.–22.7. → overhead). Měsíční sync `_sync_dochazka_ec` (@@DOCHAZKA) to uměl (má `_DRUH_ABSENCE`), recent/migrate ne.

## Oprava — Fáze 1 (nasazeno 29.7., commity c73f1da7 + bcef3fbf)
Sdílený helper **`_ec_druh_entry_type(druh, rezie, type_ids, type_work, type_oh)`** (router.py u `_DRUH_ABSENCE`):
- `DruhCinnosti` v `_DRUH_ABSENCE` → správný absence typ (20/30→vacation, 21→medical, 22→sick, 23→family_care, 31→sickday, 39/26/34/35/47(→plac_volno_70)/133/10→…).
- `8` → homeoffice; jinak `Rezie`→overhead, ostatní→work.
- **`_DRUH_SKIP={37,54}`** (Nepřítomnost OSVČ, Nepřítomen pro APS) → **None = nebrat do docházky** (v Centrále evidenční/plánovací, ne docházka).
- Použito v `_sync_ec_dochazka_recent` i `hr_migrate_dochazka` (SELECT rozšířen o `ISNULL(DruhCinnosti,0) druh`).
- Absence/HO řádky: `project_ref=NULL` (ne 'Rezie').

## ⚠️ GOTCHA — app_only + wipe (regrese, opravená bcef3fbf)
`_sync_ec_dochazka_recent` přeskakoval `app_only` lidi ÚPLNĚ (`att_source_pref.app_only=true`, 53 lidí).
Při `wipe=True` re-importu to smazalo jejich centrála1 řádky a nevrátilo → **jejich dovolené zmizely**.
Fix: pro app_only přeskočit jen **přítomnost** (`_abs=False`), **absence z Centrály brát i pro ně**
(v appce absence nejsou). Ověřuj po každém wipe re-importu, že app_only dovolené sedí!

## Nástroj: `@@DOCHRESYNC <od> <do>`
Wipe + re-import EC_Dochazka → att_entry za rozsah přes opravenou klasifikaci (volá `_sync_ec_dochazka_recent(frm,to,wipe=True)`).
Naše app záznamy (source_system != centrala1) zůstanou. Přes SQL most (neutrální návratovka, ověřuj čtením).
Červenec 2026 re-import ověřen: vacation 110, sick 17, medical 5, sickday 1, homeoffice 6, overhead 42 (skutečná režie), OSVČ/APS 0.

## Fáze 2 — nové typy volen (ČÁST HOTOVO, zbytek TODO)
Hotovo (29.7.): **Volno 70/80/90 % → typy `plac_volno_70/80/90`** (category absence, is_paid=true, affects_balance=false; mzd. složka 256 s %), kódy 47/50/51 v `_DRUH_ABSENCE`.

**TODO — založit typy + doplnit do `_DRUH_ABSENCE`** (mzd. chování z `EC_ContrMzdyPrenesDoMezd`):
- 138 Překážka v práci → 256/100 % (placené) → typ `prekazka`
- 35 Volno 60 % → 256/60 % → `plac_volno_60`
- 34 Ostatní s náhradou mzdy → 252 (placené) → `ostatni_nahrada`
- 36 Mateřská → 255 → `materska`; 33 Otcovská → 254 → `otcovska`
- 10 Nařízené volno → `nariz_volno`; 133 Náhradní volno → `nahr_volno` (mzd. složky doplnit)
Postup: INSERT typu (banner) → doplnit kód do `_DRUH_ABSENCE` → deploy → `@@DOCHRESYNC`. Kristý dodá kódy + placené/neplacené.

