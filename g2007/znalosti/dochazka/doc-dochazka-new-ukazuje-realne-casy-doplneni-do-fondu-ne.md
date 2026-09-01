# Dochazka new ukazuje realne casy vcetne hodin nad fond, doplneni do fondu ZAMERNE ne

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Docházka new ukazuje reálné časy — doplnění do fondu záměrně ne

**Peťa, 1. 9. 2026. Rozhodnuto, není to chyba — nepředělávat.**

## Pravidlo

Přehled **Docházka new** (`apps/api/static_db/dochazka-po-zakazkach.html`) ukazuje
**skutečně napíchané časy**, tedy i **hodiny nad fond**. Hodiny, které do fondu dopsal
automat (druh záznamu `fond_doplneni`, „Doplnění do fondu (automat)"), v něm **nejsou
a nemají být** — nikdo v tu dobu v práci nebyl, není to reálný čas.

Peťa 1. 9. 2026: „nad fond ano, do fondu ne" — přijde jí to takhle správně.

## Proč to stálo za rozmyšlení

Přehled má tlačítko **Sumace označených** (pravý klik na řádek), které sečte hodiny
po měsících a lidech. Součet je z řádků přehledu, takže doplňky do fondu v něm nejsou —
a proti mzdovému podkladu, kde doplňky jsou, tedy **sedět nebude**. To není chyba
výpočtu, je to důsledek toho, co přehled ukazuje.

## Co se proto udělalo

Do okna Sumace přibyla pod tabulku věta, aby se na to nemuselo přicházet znovu.
Znění je Petino, doslova:

> Součet obsahuje pouze skutečně odpracované hodiny — bez automatických doplnění do fondu.

Zapsáno 1. 9. 2026 do `g2007.soubor`, verze 53, 141037 znaků,
md5 `89b330c2651444deb33959516ea5105a` (ověřeno čtením po zápisu).
Okno Sumace je vlastní tomuhle přehledu, ne sdílená komponenta — v žádném jiném
přehledu se ta věta neukáže.

## Pro příští instanci

Kdyby někdo hlásil, že „v Docházce new chybí hodiny" nebo že „Sumace nesedí se mzdami",
**není to chyba k opravě.** Je to rozhodnutí. Mzdový podklad se počítá jinde
(`tenant.att_day_summary`), tam doplňky do fondu jsou.

Souvisí: [[doc-dochazka-prazdny-den-doplnen-nalez-jednou-na-den]]

