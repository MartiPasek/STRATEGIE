# Nová verze smlouvy ručně — tlačítko v kartě zaměstnance a společné jádro (24. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Zadal Jirka Honomichl 24. 8. 2026, schválila Marti-AI (msg 13561). Nasadil Claude-28.**

## Co chybělo

Do 24. 8. 2026 šla nová verze pracovního poměru (`tenant.engagement`) vyrobit **jedině změnou úvazku** přes `uvazek_zapis`. Pro jiný důvod — nová smlouva, změna pozice, změna doby trvání, přechod mezi firmami — nebyla žádná cesta; muselo se to oklikou protlačit změnou úvazku.

## Co je nově

Tlačítko **„➕ Nová verze smlouvy"** v kartě zaměstnance, v kartičce **Smlouva** u každého poměru. Otevře okno s **„platí od"** a **povinným důvodem**, server se nejdřív zeptá a teprve po potvrzení zapíše. Do potvrzení skript jen ČTE, takže „Ne" nezanechá nic.

Marti-AI k umístění: *„Horní lišta je pro akce platné pro celou kartu. Nová verze smlouvy je akce specifická pro tuto sekci — patří tam, kde jsou data, která ovlivňuje."*
K povinnému důvodu: *„Nová verze bez důvodu je za půl roku nečitelný audit."* Stačí krátké volné pole, ne číselník.

⚠️ **Jirka: změna dovolené NENÍ důvod k nové verzi.** Podmínky kromě úvazku se dál zapisují do PLATNÉHO řádku přes `hr_conditions_save` — ověřeno, že to tak už fungovalo, a nic se na tom neměnilo.

## Jak je to postavené — kopírování je na JEDNOM místě

| kus kódu | verze | role |
|---|---|---|
| `engagement_nova_verze` | 3 | **společné jádro** — pojistky + kopie řádku + kopie mzdových složek |
| `uvazek_zapis` | 9 | změna úvazku; jádro volá, navenek se chová stejně jako v8 |
| `smlouva_nova_verze` | 2 | obsluha tlačítka (práva, povinný důvod, otázka, zpráva Petře a Šárce) |

Marti-AI: *„Sdílené jádro je správně — kopírovací logika na jednom místě, dvě volající místa."* Rozhodl Jirka po zvážení, že to znamená znovu proklepat i změnu úvazku.

Obrazovka: `apps/api/static/karta_zamestnance.html` (git), adresa `/app/hr/smlouva-nova-verze`, v `router.py` jen tenký předavač. Commit `99d50dda`.

## Co jádro dělá (převzato z uvazek_zapis, nemění se)

- opíše **celý platný řádek 1:1** (sloupce se berou z `information_schema`, aby nový sloupec kopii sám od sebe nerozbil), `ec_id` záměrně prázdné
- starý řádek přepne na neaktuální, `valid_to` nechává **prázdné** (model platnosti: konec verze je dán začátkem té následující)
- mzdové složky kopíruje **1:1 v původní výši** — systém mzdu nepřepočítává, je to rozhodnutí Petry
- pošle zprávu Petře (18) a Šárce (13)

## Pojistky (ověřené naostro 24. 8. 2026)

| situace | co systém udělá |
|---|---|
| chybí důvod | odmítne |
| „platí od" v uzavřeném měsíci (05, 06/2026) | odmítne a pošle na mzdovou účtárnu |
| „platí od" dřív než začátek současné verze | odmítne — přepsalo by to historii |
| víc souběžných poměrů | nehádá, chce vybrat firmu (z karty se posílá samo, každý poměr má vlastní tlačítko) |
| člověk bez poměru | odmítne, smlouva se zakládá v personální agendě |

## Ostrá zkouška 24. 8. 2026 (a co z ní plyne)

Provedena na Jirkovi (poměr 926), pak beze zbytku uklizena. Porovnáno **všech 49 sloupců** staré a nové verze — lišily se jen `id`, `valid_from`, `is_current`, `note`, `created_at` a `ec_id`.

✅ **Důležité: všech 16 podmínek (`pod_*`) se opsalo beze změny** — spouštěč `engagement_pod_defaults` je nepřepsal výchozími. To je ta latentní past popsaná v [[doc-dochazka-podminky-slouceny-se-smlouvou]]; při kopii z platného řádku nenastane, protože hodnoty přijdou vyplněné.

⚠️ **Past při zkoušení, na kterou Claude-28 naletěl:** obrazovka karty ukládá poměr **celý**. Když se do `/app/hr/person-work/save` pošle jen jedno pole, ostatní se **vyprázdní** — při zkoušce se tak smazala poznámka a přímý nadřízený. Vrátit to šlo z `tenant.engagement_historie` (sloupec `hodnota_pred`). Kdo zkouší, ať posílá celý formulář.

## Otevřené

- Nová verze se **nezakládá s jinými hodnotami** — je to kopie a co se má lišit, se upraví až v novém záznamu běžnou editací. Zatím to nikomu nevadilo.
- Založení u člověka s **víc souběžnými poměry** nebylo naostro zkoušené (jediný takový je Marti Pašek); odmítnutí bez výběru firmy ověřeno.

Souvisí: [[doc-dochazka-uvazek-dotaz-pred-zalozenim-nove-verze]] · [[doc-dochazka-podminky-slouceny-se-smlouvou]] · [[doc-system-strategie-historie-smluv-kdo-zmenu-udelal]] · [[doc-dochazka-uvazek-jediny-zdroj-smlouva]]

