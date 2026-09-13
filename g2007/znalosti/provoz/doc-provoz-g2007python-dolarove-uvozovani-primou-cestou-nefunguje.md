# Zápis do g2007.python: dolarové uvozování projde přes banner, ale přímá cesta padá na KeyError

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Zápis do `g2007.python`: dolarové uvozování projde přes banner, ale NE přímou cestou

**Ověřeno naostro 10. 9. 2026 (C24 / Kristý), stálo to dva neúspěšné pokusy.**

Chirurgická záměna kódu v `g2007.python` se běžně píše s dolarovým uvozováním, protože
řeší apostrofy i víceřádkovost:

```
UPDATE g2007.python SET zdroj = replace(zdroj, $old$…$old$, $new$…$new$) WHERE kod=…
```

**Jenže most má na zápisy do `g2007.python` dvě různé cesty a chovají se jinak:**

| cesta | dolarové uvozování |
|---|---|
| přes **schvalovací banner** (`fw.claude_write_request`) | ✅ projde — 9. i 10. 9. tak prošly tři záplaty |
| **přímá „G2007 KONSTRUKTIVNI (přímo, bez banneru)"** | ⛔ **spadne** |

Chyba vypadá takhle a **není to chyba SQL**:

```
g2007.python KeyError: '$old$'
```

Přímá cesta si dolarový obal vyloží jako **proměnnou** a hledá ji ve slovníku.
Selhalo to se značkami `$ho2$` i `$ba$`, takže **nejde o jméno značky** ani o číslice v ní.

## Co dělat místo toho

1. Ověř, že vkládané texty **neobsahují apostrof** (`'`), a taky `$` a `%`.
2. Pošli je jako **obyčejné jednoduše uvozené řetězce**. Víceřádkový řetězec je v SQL v pořádku.
3. Když apostrof v textu je, rozděl záměnu na víc kroků tak, aby se apostrofu vyhnula,
   nebo pošli zápis cestou, která jde přes banner.

## Pořád platí

- **`:slovo` kdekoli v příkazu** (i v komentáři) = bind parametr → pád. Před odesláním
  projeď `(?<!:):(\w+)`, musí vyjít prázdný. 10. 9. na tom spadla záplata kvůli `:disabled`
  napsanému ve vlastním komentáři.
- Do `WHERE` **vždy** `md5(zdroj) = '<otisk, který jsi četl>'` **a** kontrolu, že každá kotva
  je ve zdroji **právě jednou**. Opožděně schválený nebo zopakovaný zápis pak projde
  na 0 řádků místo aby přepsal cizí opravu.
- Po zápisu **porovnej `md5(zdroj)`** s otiskem spočítaným lokálně před odesláním.

