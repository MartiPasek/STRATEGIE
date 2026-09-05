# Rederivace fragmentu mobile.html HOTOVA - publikacni cesta @@G2007SESTAV je opet DUVERYHODNA (3.8.2026 vecer)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **NEPLATNE od 5. 9. 2026.** Postup publikace obsahu mobilu popsany nize UZ NEPLATI - plati @@G2007PUBLISH, viz doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje (24. 8. 2026) a doc-system-strategie-po-updatu-g2007-soubor-nutny-publish (31. 8. 2026). Duvod - @@G2007SESTAV vydava i cizi nepublikovanou praci. Rozhodl Jirka Honomichl 5. 9. 2026. Dokument zustava jen jako historie.

## Vysledek (uzavira doc-system-strategie-todo-mobile-fragmenty-rederivace-vecer)
Vsech 28 puvodnich fragmentu mobile_parts/* PREPSANO bajtove presnymi vyrezy ziveho monolitu v5 (910 328 zn, md5 894785636b6e...): rez veden sekvencnim hledanim prvnich radku puvodnich fragmentu + rucni dolazeni hranice 30_contacts (sekce nalezena uvnitr 25_tasks). INVARIANTA overena: concat(28 novych fragmentu) == v5 NA ZNAK. Fragment 73_zvp_finance_zakazky.js (Kristy/C24, 4 778 zn, pridan 3.8. dopoledne) NEDOTCEN - byl to novy obsah cekajici na publikaci (stejna zed jako Jirka rano).

## Ostry test slozeni (Marti GO 20:13)
@@G2007SESTAV apps/api/static/mobile.html -> artefakt v12 (915 450 zn, md5 67f8e690...) = SESTAV hlavickovy komentar + v5 + B2 Kristy. Diff proti ocekavani: JEDINY rozdil = hlavicka "GENEROVANO prikazem @@G2007SESTAV / NEEDITUJ", zbylych 10 685 radku identickych. Zivy /mobile: 200, appka NABEHLA (ERP spojeni zive, konzole bez chyb), B2/SCREENS.vpfinzak pritomen, Jirkova hlaska spravne NEpritomna (zustava v historii v6). TIM SLA VEN funkce B2 Finance zakazek pro VP (Kristy).

## Pravidla od ted (dulezite pro vsechny instance + Marti-AI)
1. Publikacni cesta mobile.html je zase duveryhodna: edituj fragment pres @@G2007SOUBOR -> @@G2007SESTAV (nebo PUBLISH az bude opravena sanity kontrola - doladovaci ukol Marti-AI). NIKDY vice needitovat zivy artefakt/disk primo - fragmenty jsou zdroj pravdy.
2. Fragmenty MUSI zustat doslovnymi vyrezy (vc. <script> obalku) - zadna normalizace pri editaci; sestav = proste slepeni v poradi slozeno_z + hlavickovy komentar.
3. Znama kosmetika: v 00_head zustal stary sandbox komentar z 1.8. (artefakt ma ted 2 hlavicky) - neskodne, pri pristim zasahu do 00_head smazat. Hranice 03_shell je jen 15 zn (obsah shellu v5 realne srostl do okoli) - pri budouci potrebe editace teto oblasti hranice posunout.
4. Pomocne soubory rederivace v D:/Projekty/STRATEGIE/tmp_rederivace/ - Marti muze smazat.

