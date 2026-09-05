# Řádek „Korekce Landmark" na výplatnici četl zastaralé zrcadlo mzdových karet — opraveno 4. 9. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Řádek 4320 „Korekce Landmark" ukazoval nesmysl u lidí se změnou poměru

**Našla Peťa při kontrole srpnových mezd 4. 9. 2026, opravil C26 týž den.**

## Co to je za řádek

Složka **4320 „Korekce Landmark (srážka os. ohodnocení)" NENÍ mzdová složka.** Do Heliosu se
neposílá a v mzdových datech neexistuje — je to **informativní řádek, který si dopočítává naše
obrazovka výplatnice** (`mzdy_vyplatnice_detail` v `g2007.python`), aby bylo vidět, o kolik
Landmark ukrojil z osobního ohodnocení.

Počítá se jako rozdíl: `předzpracování 432 (co jsme poslali do Heliosu) − osobní ohodnocení`.

## Chyba

Druhý člen si bral z **`tenant.helios_wage_snapshot`** — zrcadla mzdových karet Heliosu,
což je **snímek z 11. 6. 2026**. Že se nemá používat, je zapsané v
[[doc-mzdy-vstupy-ze-strategie]]; tady to zůstalo.

U koho se od června nic nezměnilo, obě čísla seděla a řádek vycházel správně. **U koho se
změnil poměr, se porovnávalo nové číslo se starým.** Bernardová (EC 475, od 1. 8. úvazek
32 → 40 h, osobní ohodnocení 10 681 → 7 500) měla na pásce **−900 místo −4 353**.

⚠️ **Mzda byla celou dobu správně** — základ, osobní ohodnocení i obě náhrady seděly do
koruny. Chyba byla jen v zobrazení.

## Oprava

`_v` se čte z **Podmínek** (`tenant.wage_component.amount_real`, složky mapované na Helios 432,
`krati_dochazkou = false`, aktuální verze poměru) — tedy ze stejného zdroje, ze kterého počítá
mzda. Zápis přes most, ověřeno na živé pásce: Bernardová **−4 353**, Zeman i Duspivová beze změny.

## Zbývá

Ve stejném skriptu se `helios_wage_snapshot` čte ještě jednou — u prémie jednatele (složka 693
přehozená na 432 u ne-jednatelů). Ta část opravená **není**, má stejnou vadu a týká se lidí,
kterým se změní poměr a zároveň mají tuhle prémii.

## Poučení

Když někde nesedí číslo na obrazovce, **zjisti nejdřív, jestli tu složku vůbec posíláme my.**
4. 9. jsem půl hodiny hledal chybu v Landmark proceduře, přitom ta počítala správně
(46 z 48 lidí na korunu při nezávislém přepočtu) a rozbité bylo zobrazení.

## Souvisí

[[doc-mzdy-landmark-kontrola-jak-a-na-cem-se-splest]] · [[doc-mzdy-vstupy-ze-strategie]] ·
[[doc-mzdy-landmark-podklad-vypocet]]

