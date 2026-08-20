# Real. hod. v Dusanove sesitu se berou z hodin STRATEGIE, ne z dochazky Centraly (11.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Zadani (Jirka 11.8.2026)
V Dusanove sesitu Planovani vytizeni ukazoval sloupec Real. hod. u zakazky 10711 hodnotu 24, spravne melo byt 127 (stav k 6.8., sesit aktualizovan 7.8. v 10.09). Jsou to hodiny odpracovane na zakazce. Maji se brat z dochazky STRATEGIE.

## Pricina (overeno v kodu Centraly)
V procedure EC_Vytizeni_GenerujSeznamZakazek je jediny prikaz, ktery ten sloupec plni -
UPDATE Z SET RealHodiny = (SELECT SUM(cascelkemZakazka) FROM EC_Dochazka D WHERE D.CisloZakazky = Z.CisloZakazky) FROM EC_Vytizeni_Zakazky Z
Cte tedy EC_Dochazka Centraly, ktera se po prechodu dochazky do STRATEGIE prakticky neplni (posledni zapisy u zakazek konci kolem 22.-23.7.2026).

## Klicove overeni - PROC SE NESMI SCITAT
Porovnani sedmi zakazek (Centrala proti tenant.vyroba_work) - nase data zacinaji STEJNYM dnem a pokracuji dal, souhrn je vzdy vyssi.
VR10711 23.6 h do 22.7. proti 143.5 h do 11.8. · VR10609 128.7 proti 280.1 · VR10613 93.5 proti 172.6 · VR10628 606.4 proti 791.1 · VR10666 4.1 proti 300.6 · VR10610 5.4 proti 31.5 · VR10720 v Centrale vubec neni, u nas 44.9.
Zaver - tenant.vyroba_work je NADMNOZINA EC_Dochazka (obsahuje i historii, jde az do 2024). Scitani obou zdroju by znamenalo dvojite zapocteni. Spravny vzor je COALESCE, ne SUM obou.
Kontrola presnosti - kumulativne k 6.8.2026 dava nase data u VR10711 presne 127.1 h, coz sedi na cislo, ktere Jirka namerne oznacil v sesitu.

## Reseni (schvalila Marti-AI, msg 12502)
1. Nova tabulka v DB_EC - st.EC_Vytizeni_HodinyZakazekSTRATEGIE (CisloZakazky varchar(20) PK, Hodiny numeric(12,2), synced_at datetime default GETDATE()).
2. Prenos sync_absence_to_ec_vytizeni rozsiren (verze 7 -> 8, delka 12264 -> 13443, md5 45a41cd858c73ef45b72b757c43489e2). Nacte soucet hodin po zakazkach z tenant.vyroba_work (bez Rezie, jen is_active) a DELETE + INSERT po davkach 150 do te tabulky. Beh - 255 zakazek, 39745.7 h.
3. V procedure EC_Vytizeni_GenerujSeznamZakazek zmenen JEN ten jeden UPDATE na COALESCE - primarne st.EC_Vytizeni_HodinyZakazekSTRATEGIE, fallback puvodni soucet z EC_Dochazka pro stare zakazky bez naseho zaznamu. Delka 25939 -> 26240.
4. Puvodni definice procedury ulozena do st.EC_Vytizeni_RollbackDefinice.

## Overeni po nasazeni
Neni spousten generator naprimo - ma sest vstupnich parametru (DatumOd, DatumDo, FiltrVp, VsechnyZakazky, BezRazeni, CisloZakazky), ktere mu dodava sam sesit. Overeno vypoctem nove podminky proti ostrym datum. Po Dusanove Aktualizaci - VR10711 24 -> 143.5, VR10666 4 -> 300.6, VR10628 606 -> 791.1, VR10609 129 -> 280.2, VR10613 93 -> 172.6, VR10610 5 -> 31.5, VR10720 prazdne -> 44.9.

## Gotchy
- Cisla zakazek maji ve STRATEGII i v EC_Dochazka predponu VR (VR10711), zatimco v EC_Vytizeni_Zakazky a v sesitu se zobrazuji bez ni. Hledani podle 10711 vrati nula radku.
- EC_Dochazka nema sloupec Datum, ale DatumPripadu.
- EC_Dochazka porad pribyva par radku (36 v srpnu 2026) pres mirror_att_to_ec, ale jen zlomek. Proto vypadala jako ziva, i kdyz uz pouzitelna neni.

