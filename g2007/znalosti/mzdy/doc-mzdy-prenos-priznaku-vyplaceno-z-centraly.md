# Prenos priznaku Vyplaceno z Centraly do mzdovych pohybu (5. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> ## ZMENA 8. 9. 2026 - cast textu nize UZ NEPLATI
>
> Oddil **"POZOR - vyber do mezd priznak ZAMERNE necte"** platil jen do 8. 9. 2026.
> **Dnes uz vyber do mezd priznak cte a vyplacene radky do mzdy NEPUSTI**
> (`mzdy_priplatky_rows` verze 4, podminka `coalesce(wm.ec_vyplaceno,false) = false`).
> Zadala Petra Safrankova 8. 9. 2026, rozhodl Jirka Honomichl.
> Puvodni text oddilu je nize schvalne ponechany a oznaceny.
> **Detail, zmereny dopad a co zustava otevrene** - `doc-mzdy-vyplacene-radky-nejdou-do-mezd-8-9-2026`.
>
> Zbytek dokumentu plati beze zmeny.

## Co se stalo

Prenos priplatku a srazek z Centraly (`sync_priplatky_from_ec`) do 5. 9. 2026 **necetl sloupce `Vyplaceno` ani `DatVyplaceni`** z `EC_FinPriplatkySrazkyDefinice`. Radek, ktery uz byl v Centrale proplaceny mimo mzdu (typicky fakturou), se proto ve STRATEGII tvaril jako bezny schvaleny priplatek a **prosel vyberem do mezd**. Nahlasila Petra Safrankova 3. 9. 2026 na konkretnim zarijovem radku proplacenem fakturou.

## Co se zmenilo 5. 9. 2026

- `tenant.wage_movement` ma dva nove sloupce `ec_vyplaceno` (boolean) a `ec_dat_vyplaceni` (date). Ciste aditivni zmena, nic stavajiciho se nemenilo.
- `sync_priplatky_from_ec` povysen na **verzi 9** - cte `Vyplaceno` a `DatVyplaceni` a plni je pri kazdem behu. Protoze to jde i pres ON CONFLICT DO UPDATE, opravuji se i drive prenesene radky.
- **Zpetne doplneno u 1002 uz prenesenych radku** ze zrcadla `ec.pripl_srazky` (702 oznacenych za vyplacene, 300 ne). Tri radky zustaly prazdne - v Centrale uz neexistuji, neni z ceho priznak vzit.

Zadal Jirka Honomichl, navrh i rizika schvalila Marti-AI.

**Doplneno 8. 9. 2026** - ty tri radky bez priznaku uz v `tenant.wage_movement` nejsou, na pisemnou zadost Petry Safrankove byly smazany (Hrdinka 4/2026 -267 Kc, Hellmayer 6/2026 -3 600 Kc, Namjak 6/2026 1 Kc). `EC_PRIPL` ma nove 1003 radku a zadny bez priznaku.

## POZOR - co priznak NERIKA

`ec_vyplaceno` rika **pouze to, ze je radek v Centrale oznaceny za vyplaceny**. **Nerika, jakym kanalem** - jestli mzdou, nebo fakturou. Rozlisit to z dat nejde, protoze sloupec `Preneseno` je u vsech radku roku 2026 nulovy. Az bude nekdo na tenhle priznak navazovat logiku, tenhle rozdil bude potreba doresit jinak.

**Plati dal i po 8. 9. 2026** - zmena vyberu do mezd tenhle rozdil neresi, jen vedome prijima jeho dusledek.

## NEPLATI od 8. 9. 2026 - puvodni oddil "vyber do mezd priznak ZAMERNE necte"

> Nasledujici dva odstavce jsou **puvodni zneni z 5. 9. 2026** a **uz neplati**.
> Ponechany schvalne, aby bylo videt, co se zmenilo a proc.

~~`mzdy_priplatky_rows` bere dal `status IN ('approved','exported')` a na vyplaceni se nepta. **Chovani mezd se 5. 9. 2026 nezmenilo.**~~

~~Duvod - plosne vylucovani vyplacenych radku by pri prepoctu 6/2026 vyhodilo **67 radku u 42 lidi za 237 343 Kc**. V cervnu jsou totiz po vyplate oznacene za vyplacene uplne vsechny radky, takze priznak sam o sobe neni bezpecne kriterium (viz odstavec vyse - nerika kanal). Zmena vyberu do mezd je **samostatne rozhodnuti Jirky Honomichla a Petry Safrankove**, ne soucast tohoto kroku.~~

**Jak to dopadlo** - to samostatne rozhodnuti padlo 8. 9. 2026. Petra Safrankova pisemne zadala plosne vylouceni, Jirka Honomichl o cervnovem dopadu vedel (byl jim vyslovne uveden) a rozhodl udelat to podle ni. Cislo 67 radku / 42 lidi / 237 343 Kc plati dal jako **vedome prijate riziko pri pripadnem prepoctu cervna**, ne jako duvod to nedelat.

## Jak se to overovalo

1. Otisk zdroje po zapisu porovnan s lokalne spoctenym (md5 sedel na bajt, delka 14846).
2. Prenos spusten naostro dvakrat - stav ok, 1003 radku, rozpad zahozenych radku beze zmeny proti verzi 8.
3. Nejdulezitejsi test - u jednoho radku byl priznak rucne vynulovan a po dalsim behu si ho prenos **sam doplnil zpatky spravne**. Tim je overeno, ze se priznak opravdu prenasi, ne ze je jen v kodu.

## Souvisejici

- Vyber do mezd priznak od 8. 9. 2026 cte - `doc-mzdy-vyplacene-radky-nejdou-do-mezd-8-9-2026`
- Sam sloupec `Vyplaceno` v zrcadle Centraly - `doc-mzdy-priplatky-srazky`
- Proc musi byt zrcadlo plny re-import - `doc-mzdy-zrcadlo-pripl-srazky-plny-reimport`
- Smer (konec DB_EC, zdroj pravdy Praha) - `doc-mzdy-priplatky-srazky-cutover-praha`

