# Oprava bugu _JEDNATELE_CISLA (jednatelska cisla) v mzdovych skriptech

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Predexistujici produkcni bug (nalezen 31.7.2026 pri migraci Faze E davka 2): funkce mzdy_vyplatnice_detail, mzdy_vyplatnice_slozka_detail a inline blok v mzdy_generuj odkazovaly na nedefinovane jmeno _JEDNATELE_CISLA (konstanty _STRAVENKA_KC/_STRAVENKA_MS/_JEDNATELE_CISLA byly smazany commitem 9ce2af8c) - u vyplatnice_slozka_detail to zpusobovalo 500 error pri rozpisu slozky 432 pro NE-jednatele.

SPRAVNA identita jednatelu (overeno v tenant.att_employee 4.8.2026 + potvrzeno Marti i Kristy 5.8.2026):
- Marti Pasek EC = cislo 2 (aktivni)
- Marti Pasek ES = cislo 41 (aktivni, HPP)
- Branislav Mozer EC = cislo 47 (aktivni)
=> _JEDNATELE_CISLA = {2, 41, 47}

OPRAVA CHYBNE VERZE TETO ZNALOSTI (5.8.2026, C24/Kristy): puvodni zapis z 31.7. tvrdil _JEDNATELE_CISLA = {2, 15, 47} s odduvodnenim "Marti potvrdil ES=15, cislo 41 byl chybny odhad z DB". To bylo OBRACENE. Marti 5.8.2026 potvrdil Kristy, ze jeho tehdejsi poznamka (15) byla omyl. Data to dokladaji: cislo 15 = neaktivni zaznam bez uvazku (do mzdy nepatri); cislo 41 = aktivni ES Pasek. Puvodni DB odhad 41 byl tedy SPRAVNY, rucni override na 15 byl chyba.

DOPAD chybne 15 (31.7.-4.8.2026): v zivych skriptech mzdy_generuj + obe vyplatnice funkce -> Marti v ES (cislo 41) nedostaval plne stravne a jeho ES odmena 693 se spatne preklapela na slozku 432; cislo 15 v setu nic nedelalo (neaktivni). Zadna mzda se v tomto okne se spatnym setem NEgenerovala (cervenec k 5.8. jeste nebyl generovan), takze zadna data nebyla poskozena.

OPRAVENO 4.8.2026 (C24/Kristy): set srovnan na {2, 41, 47} ve trech skriptech pres UPDATE g2007.python.zdroj (autonomni kanal) - mzdy_generuj (v3->v4), mzdy_vyplatnice_detail (v4->v5), mzdy_vyplatnice_slozka_detail (v3->v4). mzdy_predzprac_rows mel {2,41,47} spravne uz predtim. Overeno ctenim.

POUCENI (opravene): "kdo je jednatel" je pravni/firemni fakt - over ho proti DATUM (aktivni zaznam v tenant.att_employee: is_active + existujici engagement/firma) I u cloveka a KRIZOVE zkontroluj oboji. V tomto pripade byl prvni DB odhad (41) spravny a rucni "oprava" (15) chybna - slepe nespolehat ani na jedno, sedet musi oboji.

ZBYVA: cesta @@MZDY (router.py _mzdy_full_run) ma spravny set {2,41,47}, ale nedefinovane konstanty (smazany 9ce2af8c 31.7.) -> NameError, jednatelsky blok by spadl. Neni produkcni cesta (generuje se pres UI). Rozhodnuti: vyradit @@MZDY vetev nebo aditivne vratit konstanty.

