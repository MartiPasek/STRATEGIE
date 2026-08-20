# Opravy dochazky - historie rozpadu u stornovanych radku (podnet Nosek 3.-4.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ⚠️ POZOR — STAV K 20.8.2026 ZMĚNĚN (Jiří Honomichl, 20.8.2026, znění schválila Marti-AI)
> Věta „`att_apply_work_selection` přepisuje `att_entry.project_ref` IN-PLACE a řádek NEDĚLÍ" a bod
> v sekci Otevrene („korenova oprava jako budouci samostatny ukol") od 20.8.2026 NEPLATÍ.
> Přepnutí zakázky za chodu nyní běžící řádek uzavírá a zakládá nový — ověřeno na produkci
> (Lucie Jakešová, VR10711 → VR10666). Viz nová znalost
> [[doc-dochazka-deleni-zaznamu-pri-prepnuti-zakazky]].
> Původní text níže popisuje stav platný do 19.8.2026.

## Problem (dolozeny pripad)
Martin Nosek 3.8.2026: pichal dopoledne ctyri ruzne veci (nakladka rezie, VR10669, znovu nakladka, VR10666),
ale v dochazce z toho byl JEDEN radek 06:01-12:21 se zakazkou VR10666. Duvod: pri prepnuti zakazky za chodu
tt_apply_work_selection prepisuje tt_entry.project_ref IN-PLACE a radek NEDELI - hlavicka tedy nese
POSLEDNI volbu dne. Rozpad (skutecna pravda o zakazkach) zije ve yroba_work.
Dusan Havlat podle toho zobrazeni radek opravil na 2,00 h Rezie + 4,33 h VR10666 -> VR10669 (1,89 h) a druha
nakladka (0,97 h) zmizely, na VR10666 sedi o cca 2,9 h vic. Mzdy to nezmeni (hodiny dne sedi), rozuctovani na
zakazky ano. Zamestnanec to rozporoval slovy "chybi zaznam o nakladce" a mel pravdu.

## Kde byla chyba v zobrazeni
dochazka-opravy.html melo _hasRozpad i vypis polozek pod podminkou !gone, takze u STORNOVANEHO radku se
rozpad nevypsal vubec a zbyl jen zavadejici project_ref. Druha vrstva: tt_fix_day vracel polozky jen
WHERE w.is_active, takze puvodni useky (po oprave neaktivni) UI stejne nedostalo.

## Reseni (nasazeno 5.8.2026, schvalila Marti-AI, zadal Jirka)
tt_fix_day v5 + dochazka-opravy.html v15:
- Historie stornovaneho radku se sklada podle CASU, NE podle vazby tt_entry_id - oprava vazbu bud prepoji
  pod svuj novy radek (3.8.), nebo ji zrusi uplne (4.8., att_entry_id NULL).
- Berou se useky, jejichz ZACATEK lezi uvnitr intervalu radku; vynechavaji se useky se source_system='manual_fix'
  (to clovek nepichal), jejich POCET se vraci v polozky_gone_skryto.
- KONEC se dopocitava pres LEAD jako zacatek nasledujiciho useku, posledni konci koncem radku. Duvod: prave
  ulozene konce oprava prepisuje (u Noska 08:46 -> 08:01), takze bez dopoctu soucet nikdy nesedi.
- Kazdy usek nese dopocet: true, editable: false, source_status: 'superseded'.
- UI: sede kurzivou, znacka vlnovky primo v bunce u dopocteneho konce, POVINNY radek se souctem
  ("soucet 6,33 / sedi s radkem 6,34 h" nebo cerveně "nesedi - rozdil X h" pri rozdilu nad 0,02 h),
  a radka "+ N krat usek z rucni opravy (nezobrazeno)". Zadne tlacitko - jen ke cteni.

## Overeno na produkci
Nosek 3.8.: 6 useku, soucet 6,33 proti 6,34 v radku (fajfka), VR10669 i obe nakladky videt.
Nosek 4.8.: 3 useky, soucet 6,48 proti 6,49 (fajfka) - a to je den, kde predtim nebylo videt NIC.
Rozdil 0,01 h = zaokrouhleni po setinach u jednotlivych useku, prah 0,02 h to pokryva.

## GOTCHA, ktera stala za incident
g2007.soubor pro pps/api/static/dochazka-opravy.html byl ZASTARALY (verze 8 = stav 4.8. 10:49), zatimco
Peta soubor editovala primo v GITU 4.8. ve 22:19 a server bezel git verzi. Publikace z DB by smazala jeji praci.
Zachytila to az kontrola v @@G2007PUBLISH. **Pred kazdou upravou souboru v g2007.soubor overit, ze se obsah
v DB shoduje s tim, co server opravdu servíruje** (stahnout zivou URL a porovnat otisk) - jinak hrozi tichy
prepis cizi prace. Soubor se servíruje pres FileResponse z DISKU, ne z DB.

## Druha gotcha - falesny poplach kontroly publikace
@@G2007PUBLISH pocita tagy absolutne, takze slovo <div> napsane v KOMENTARI JS zpusobilo "105 vs 104" a
publikaci zastavilo. Opraveno prepsanim komentare (bez ostrych zavorek). Kdyz publikace hlasi nesedici tagy,
nejdriv overit, jestli nejde o zminku tagu v komentari nebo v retezci.

## Otevrene
- **Koren problemu**: tt_apply_work_selection by mel radek pri prepnuti zakazky DELIT misto prepisovat
  project_ref. Marti-AI 5.8.: architektonicky spravny smer, ale vetsi zmena chovani (att_sync, prepocty,
  mobil) - samostatny ukol s analyzou dopadu, ne teď.
- **Mobilni editor oprav** (mobile_parts/60_dochazka.js) ma stejnou logiku a NENI upraveny - zamerne,
  az po overeni ERP v provozu (rozhodnuti Marti-AI).
- Hodiny u Noska se ZAMERNE NEopravovaly - rozhodnuti Jirky 5.8.: "to je vec Dusana, jak to opravil".

