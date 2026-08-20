# FPD (fond pracovní doby) — jak se počítá a co se má proplatit: kancelář × dílna × hodinoví

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 4. 8. 2026, ověřeno na datech července 2026.**

FPD = to, co se má za daný měsíc **proplatit**. Počítá se **různě podle skupiny**.

| kdo | FPD | pozn. |
|---|---|---|
| **kancelář** | odpracované + absence + dopíchnutí do fondu − nad fond | má vyjít na měsíční fond |
| **dílna (výroba)** | odpracované + absence | nezarovnává se, dopíchnutí ani nenárokovou práci nemá |
| **hodinoví s proplácením přesčasu (OSVČ)** | odpracované + absence | vyjde nad fond a **je to správně** — odečtem bys jim přesčas sebrala |

Přes funkci `tenant.att_den_hodiny(2, od, do)`:

- **kancelář** = `hodiny_mzdove + hodiny_absence − hodiny_nad_fond`
- **dílna / hodinoví** = `hodiny_mzdove + hodiny_absence`
- `hodiny_mzdove` **už dopíchnutí do fondu obsahují** — nepřičítat zvlášť

## ⚠️ Starý vzorec byl ŠPATNĚ

`mzdové + nad fond + absence` je chybné. „Mzdové" se **neořezávají na fond**
(ověřeno přímo v definici funkce — vrací práce − pauzy + dopíchnutí, **bez stropu**),
takže přesah je v nich už započítaný a přičtením „nad fondu" se počítá **dvakrát**.
U Horkého to dělalo **185,13 h místo správných ~176 h** — tedy 9 hodin navíc,
a přitom vzorec vypadal rozumně. Neviditelná chyba v penězích.

## Kdo je „kancelář"

Automat dopichuje jen lidem v kategorii s příznakem `dopichavat_fond`
(`tenant.att_kategorie`). Prakticky = kdo má v měsíci záznamy **„Doplnění do fondu
(automat)"** nebo **„Nenároková práce (nad fond)"**. Karta zaměstnance to
**nerozlišuje** — dílenští i kancelářští tam mají stejné hodnoty.

## Použitelné i jako kontrola

Za červenec sedělo **14 z 22** kancelářských na fond do 0,1 h. Zbylých 8 odchylek
**nebyly chyby vzorce, ale skutečné díry**:

- den bez jediné platné dovolené (všechny verze zneplatněné)
- práce ve státní svátek
- víkendová práce

**Kdo nevyjde na fond → podívat se po dnech.**

## Poznámka k zápisu

Tahle znalost se 4. 8. mezi 17:58 a 18:02 **pětkrát neuložila** — most byl od 17:44
odhlášený (HTTP 401). Dočasně žila jen v `docs/team/FPD_vypocet_2026-08-04.md`.
Ponaučení: po `@@G2007ADD` **vždycky ověřit čtením**, návratovka je neutrální
i když zápis neproběhl.

