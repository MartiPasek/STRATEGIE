# Prenos priznaku Vyplaceno z Centraly do mzdovych pohybu (5. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo

Prenos priplatku a srazek z Centraly (`sync_priplatky_from_ec`) do 5. 9. 2026 **necetl sloupce `Vyplaceno` ani `DatVyplaceni`** z `EC_FinPriplatkySrazkyDefinice`. Radek, ktery uz byl v Centrale proplaceny mimo mzdu (typicky fakturou), se proto ve STRATEGII tvaril jako bezny schvaleny priplatek a **prosel vyberem do mezd**. Nahlasila Petra Safrankova 3. 9. 2026 na konkretnim zarijovem radku proplacenem fakturou.

## Co se zmenilo 5. 9. 2026

- `tenant.wage_movement` ma dva nove sloupce `ec_vyplaceno` (boolean) a `ec_dat_vyplaceni` (date). Ciste aditivni zmena, nic stavajiciho se nemenilo.
- `sync_priplatky_from_ec` povysen na **verzi 9** - cte `Vyplaceno` a `DatVyplaceni` a plni je pri kazdem behu. Protoze to jde i pres ON CONFLICT DO UPDATE, opravuji se i drive prenesene radky.
- **Zpetne doplneno u 1002 uz prenesenych radku** ze zrcadla `ec.pripl_srazky` (702 oznacenych za vyplacene, 300 ne). Tri radky zustaly prazdne - v Centrale uz neexistuji, neni z ceho priznak vzit.

Zadal Jirka Honomichl, navrh i rizika schvalila Marti-AI.

## POZOR - co priznak NERIKA

`ec_vyplaceno` rika **pouze to, ze je radek v Centrale oznaceny za vyplaceny**. **Nerika, jakym kanalem** - jestli mzdou, nebo fakturou. Rozlisit to z dat nejde, protoze sloupec `Preneseno` je u vsech radku roku 2026 nulovy. Az bude nekdo na tenhle priznak navazovat logiku, tenhle rozdil bude potreba doresit jinak.

## POZOR - vyber do mezd priznak ZAMERNE necte

`mzdy_priplatky_rows` bere dal `status IN ('approved','exported')` a na vyplaceni se nepta. **Chovani mezd se 5. 9. 2026 nezmenilo.**

Duvod - plosne vylucovani vyplacenych radku by pri prepoctu 6/2026 vyhodilo **67 radku u 42 lidi za 237 343 Kc**. V cervnu jsou totiz po vyplate oznacene za vyplacene uplne vsechny radky, takze priznak sam o sobe neni bezpecne kriterium (viz odstavec vyse - nerika kanal). Zmena vyberu do mezd je **samostatne rozhodnuti Jirky Honomichla a Petry Safrankove**, ne soucast tohoto kroku.

## Jak se to overovalo

1. Otisk zdroje po zapisu porovnan s lokalne spoctenym (md5 sedel na bajt, delka 14846).
2. Prenos spusten naostro dvakrat - stav ok, 1003 radku, rozpad zahozenych radku beze zmeny proti verzi 8.
3. Nejdulezitejsi test - u jednoho radku byl priznak rucne vynulovan a po dalsim behu si ho prenos **sam doplnil zpatky spravne**. Tim je overeno, ze se priznak opravdu prenasi, ne ze je jen v kodu.

## Souvisejici

- Sam sloupec `Vyplaceno` v zrcadle Centraly - `doc-mzdy-priplatky-srazky`
- Proc musi byt zrcadlo plny re-import - `doc-mzdy-zrcadlo-pripl-srazky-plny-reimport`
- Smer (konec DB_EC, zdroj pravdy Praha) - `doc-mzdy-priplatky-srazky-cutover-praha`

