# Potvrzeni dne v mobilu ukazovalo jinou zakazku nez ERP Opravy dochazky (rozpad) - VYRESENO 20.8.2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Podnet
Marek Honal poslal 19.8.2026 snimek z mobilu - potvrzovaci karta dne (Dochazka, karta nepotvrzeneho dne, tlacitko "Radeji chci videt detaily") ukazovala jinou dochazku nez ERP Opravy dochazky. Zadal Jirka 20.8.2026, schvalila Marti-AI (msg 13022).

## Pricina - tataz past jako u Noska 3.-4.8.2026
Hlavicka zaznamu (`tenant.att_entry.project_ref`) nese POSLEDNI volbu zakazky dne - prepnuti zakazky za chodu prepisuje project_ref in-place a radek nedeli. Pravda o zakazkach zije v rozpadu `tenant.vyroba_work`.
Endpoint `att_day_detail` (g2007.python) cetl JEN `att_entry`, rozpad vubec nevracel. ERP Opravy dochazky (`att_fix_day`) ho vraci - proto ten rozdil.
Navazuje na [[doc-dochazka-opravy-sedy-rozpad-stornovanych-radku]] a [[doc-dochazka-opravy-rozpad-mobil]], kde se totez resilo pro EDITOR oprav; potvrzovaci karta zustala nedotcena.

## Dolozeny pripad
Marek Honal (att_employee 52, user 85), den 17.8.2026, blok 08.12-11.42 se v mobilu tvaril cely jako VR10669. Rozpad - 08.12-09.57 VR10669 Dratovani, 09.57-10.44 Rezie Pravidelna porada, 10.44-11.42 VR10669 Dratovani. Porada v mobilu videt nebyla.

## Dopad pred opravou (jmenovite, 21.7.-20.8.2026)
306 radku dochazky, 32 lidi, 241 clovekodnu. Nejvic Tomas Blaha 40, Matej Svoboda 21, Zdenek Divis 19, Martin Nosek 19, Erika Sedlackova 18, Petra Dvorakova 17. Naposledy 19.8.2026.

## Reseni (nasazeno 20.8.2026)
1. `att_day_detail` (g2007.python, verze 2 na 3) vraci u kazdeho zaznamu pole `useky` - aktivni radky `tenant.vyroba_work` spojene pres `att_entry_id`, s poli od, kon, hours, zak, cinnost. Jen ke cteni, zadna zmena vypoctu ani hodin.
2. Mobil (g2007.soubor, fragment `apps/api/static/mobile_parts/60_dochazka.js` + artefakt `apps/api/static_db/mobile.html`) - v detailu potvrzovaci karty se pod hlavickou zaznamu vypise radek "rozpad (N krat) - co se v tom case delalo", sede a jen ke cteni, SBALENY, rozbali tuknuti. Zobrazi se jen kdyz je useku vic nez jeden NEBO se zakazka lisi od hlavicky (rozhodla Marti-AI - jinak jen sum).
3. `_rozpadZnacka(e)` prida tutez znacku do seznamu zaznamu pro zadost o opravu ("Nesedi mi den"), aby clovek nezadal opravu naslepo (trvala na tom Marti-AI).

## Overeno
Endpoint pres zivou session vraci u bloku 08.12-11.42 vsechny tri useky vcetne Rezie/Pravidelna porada. Vykresleni otestovano proti NASAZENEMU kodu ze zive /mobile - sbaleno "rozpad (3 krat)", po tuknuti tri radky, druhe tuknuti sbali. U zaznamu s jednim usekem a sedici zakazkou se nezobrazi nic. Zivá /mobile sedi s DB na md5 (3051e5217a9118fe8d9a31c26a2b430b, 1013620 znaku).

## Co zustalo
- `att_day_detail_demo` (demo ucet) upraveny NENI - demo je izolovane a Jirka zakazal sahat na appku demo uctu.
- Koren problemu trva - prepnuti zakazky za chodu by melo radek DELIT misto prepisovat project_ref. Marti-AI 5.8.2026 - architektonicky spravny smer, ale samostatny ukol s analyzou dopadu.

## Kde to je v appce
Firma - Dochazka - karta nepotvrzeneho dne - "Radeji chci videt detaily". Editor oprav (parita s ERP) je Firma - Spoluprace - Opravy dochazky.

