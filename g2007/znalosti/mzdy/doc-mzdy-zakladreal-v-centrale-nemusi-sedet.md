# Past: `ZakladReal` v Centrále se nedopočítává — u Svobody 89 000 místo 95 000 (26. 8. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# `ZakladReal` v Centrále nemusí sedět se `Zaklad`

**Našly Peťa a Šárka, doložil Claude‑26, 26. 8. 2026.**

## Co se stalo

Při přepínání mezd na Podmínky vycházel u **Jana Svobody (ES 9017)** rozdíl: kopie Centrály říkala **89 000**, Podmínky **95 000**. Peťa se Šárkou ho ale na obrazovce Centrály **neviděly** — a měly pravdu.

V `EC_FinZamPodminky` jsou totiž dva sloupce a aktuální řádek (platnost od 26. 8. 2025, zapsala SNovotna) má:

- `Zaklad` = **95 000** ← tohle je v Centrále vidět
- `ZakladReal` = **89 000** ← zůstalo z předchozí verze

Přitom má **plný úvazek 40 h**, takže se ta dvě čísla mají rovnat. `ZakladReal` se prostě nedopočítal.

## Proč to k nám přišlo špatně

Import do `tenant.helios_wage_snapshot` bere **schválně sloupce `...Real`** (`ZakladReal`, `OsOhodReal`…), protože u zkrácených úvazků jsou jediné správné — sloupce bez „Real" jsou přepočet na 40 h a u part‑time by přeplácely (rozhodnutí Marti/Kristýna 29. 6. 2026, mapování `_WAGE_EC_COLS`).

Jenže když se `...Real` v Centrále nedopočítá, přenese se tichý nesmysl. Nikdo si toho nevšimne, protože na obrazovce svítí správné číslo.

## Závěr

- **Přepnutím zdroje pravdy na Podmínky se to vyřešilo** — Šárka tam má 95 000 správně (narovnala 24. 8. 2026).
- **Kdo bude někdy dělat porovnání proti Centrále, ať srovnává i `Zaklad`, ne jen `ZakladReal`.** Rozdíl mezi těmi dvěma sloupci u člověka s plným úvazkem je sám o sobě signál chyby.
- Svoboda je OSVČ a výplatnici nemá, takže se to do mezd nepromítlo. U zaměstnance by to znamenalo špatnou výplatu.

Souvisí: [[doc-mzdy-zdroj-pravdy-podminky-misto-centraly]]

