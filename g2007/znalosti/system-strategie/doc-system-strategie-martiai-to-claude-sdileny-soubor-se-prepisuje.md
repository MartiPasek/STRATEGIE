# Odpověď Marti-AI: soubor je sdílený a přepisuje se — poznej ji podle obsahu, ne podle pozice

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


**Co se stalo (Kristý + C24, 8. 9. 2026).** Málem jsem si přečetla jako svou odpověď zprávu, která patřila jiné instanci. Nic mě na tom neupozornilo — vypadala jako čerstvá a byla v souboru poslední.

**Jak to doopravdy funguje** (ověřeno ve `scripts/claude_sql_runner.py`, funkce `_poll_martiai_msgs`):

- `MARTIAI_TO_CLAUDE.txt` je **jeden společný soubor pro celý stroj**. NENÍ per lane — na rozdíl od `CLAUDE<N>_OUT.txt` ho sdílí všechna okna Coworku, která na stroji běží.
- Watcher do něj při každém kole zapíše to, co zrovna přišlo, a tím **přepíše celý předchozí obsah**. Nedrží historii ani pevný počet zpráv — kolik jich v tom kole dorazilo, tolik jich tam je.
- Značka o přečtení `.martiai_msg_seen` je **taky společná**. Každá zpráva se proto stáhne **jen jednou**. Kdo se podívá o kolo později, svou odpověď už v souboru nenajde.
- Zprávy **nemají adresáta**. V hlavičce je jen čas a číslo zprávy — nic, podle čeho by šlo poznat, komu patří.

**Pravidlo pro práci.** Svou odpověď poznávej **podle obsahu**, ne podle toho, že je v souboru poslední. Osvědčené: napiš si do dotazu vlastní značku (třeba jméno okna nebo krátký kód) a v odpovědi ji hledej — Marti-AI ji obvykle zopakuje.

**Když je přepsaná, není ztracená.** Celá historie je v `MARTIAI_TO_CLAUDE_LOG.txt` — ten se jen přidává, nic v něm nemizí. Dohledáš podle času a čísla zprávy.

**Příbuzná past.** Stejného druhu je `doc-system-strategie-most-out-full-nema-hlavicku-a-pri-chybe-se-neprepise` — plný výstup mostu se při chybě vůbec nepřepíše, takže se dá přečíst cizí odpověď. Společný jmenovatel: **sdílený soubor bez adresáta a bez značky času nesmí sloužit jako důkaz, že je odpověď moje.**

