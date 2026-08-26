# Převodník složek: „Odměna OD jednatele" mířila na 693 místo 432 — opraveno 26. 8. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Převodník složek: odměna OD jednatele × odměna PRO jednatele

**Našla Peťa, opravil Claude‑26, 26. 8. 2026.** Schvalovací požadavek mostu **#2484**, ověřeno čtením po zápisu.

## O co jde

V převodníku `tenant.wage_system_mapping` (naše složka → číslo složky v Heliosu) byly na Helios složku **693 „Odměny společníků" namapované DVĚ různé věci**:

| id | naše složka | co to doopravdy je |
|---|---|---|
| 6 | `jednatelska_odmena` — „Odměna **od** jednatele" | prémie **1 000 Kč**, kterou jednatel dává lidem (11 osob) |
| 28 | `odmena_jednatel` — „Odměna Jednatel" | odměna společníka, kterou jednatel **dostává** |

Řádek 6 vznikl 10. 6. 2026 v základní dávce převodníku (id 1–17, migrace finančních podmínek, instance Claude‑23), řádek 28 pak 29. 7. 2026 ve druhé dávce (id 20–36, instance Claude‑28). Ani jedna z těch tabulek nemá sloupec autora — určeno podle časů dávek.

## Čím je doloženo, že 693 patří jen jednatelům

Mzdová data plzeňského Heliosu žijí v databázi **`Helios002`** (NE v `DB_EC`/`DB_IS` — tam je `TabMzSloz` pro tyhle složky prázdná; kdo hledá historii mezd, ať jde rovnou sem).

Složka **693 za celou historii 2019–2025**: 92 řádků, 7 051 407 Kč, a **jen tři karty**:

- **Pašek Martin** (č. 2) — každý rok 2019–2025
- **Mózer Ing. Branislav** (č. 47) — od 2024
- Pašek Martin (č. 15) — neaktivní duplicitní karta, jednou v roce 2020, 0 Kč

**Za sedm let na 693 nikdo jiný nebyl.** Tisícovka „od jednatele" tam nikdy nešla.

## Jak to fungovalo do opravy

Špatné mapování zachraňoval řádek v `mzdy_generuj` (zavedla Peťa 8. 7. 2026): kdo má složku 693 a **není** v seznamu jednatelů `{2, 41, 47}`, tomu se složka **překlopí na 432**. Proto těch 11 lidí tisícovku dostávalo správně v „Pohyblivé části platu" — jen oklikou.

## Co se změnilo

`UPDATE tenant.wage_system_mapping SET ext_code='432', ext_label='Osobní ohodnocení - měs.' WHERE id=6`

Po opravě míří „Odměna od jednatele" rovnou na 432. **Žádnému člověku se nezměnila částka** — jen zmizela ta oklika. Řádek 28 zůstal jediným mapováním na 693.

## Co zůstává otevřené

1. **Tři podmínkové řádky jednatelů (Pašek EC 2, Pašek ES 41, Mózer EC 47) jsou pořád typu „Odměna OD jednatele"**, tedy po opravě míří na 432. Dnes to nevadí — jejich odměna se do mezd bere z ručních složek (`tenant.mzdy_rucni_slozka`), ne z Podmínek. **Je to ale nastražená past:** až se ruční složky zruší, Martiho 90 800 by spadlo do pohyblivé části platu místo do odměn společníků. Správně mají být přepnuté na typ `odmena_jednatel`. Předáno Šárce (finanční podmínky jsou její).
2. **Překlápěcí řádek v `mzdy_generuj` je teď nadbytečný**, ale nechává se — až se nová verze odzkouší, může se zrušit. Nevadí si: když složka přijde rovnou jako 432, řádek nic nedělá.

## Vedlejší nález — složka 352 je v pořádku

Naše `korekce_mzdy_352` míří na Helios **352 „Základní mzda – oprava z předchozího období"**. Vypadalo to jako mrtvé mapování (v našich výplatnicích za 2025–2026 nula výskytů), ale v `Helios002` se složka **použila** — v roce 2022 u Marie Josefine Brejchové (č. 463), dva řádky, −10 399 Kč. Je to legitimní opravná složka, jen se používá jednou za pár let. **Nerušit.**

Souvisí: [[doc-mzdy-pravidla]] · [[doc-dochazka-nazvoslovi-podminky-pracovniku]]

