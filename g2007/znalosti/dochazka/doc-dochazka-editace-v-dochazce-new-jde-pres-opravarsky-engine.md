# Editace v Docházce new jde přes opravárenský engine, ne napřímo (ověřeno 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Editace v Docházce new jde přes stejný engine jako Opravy

**Ověřeno čtením kódu 7. 9. 2026** (Peťa + Claude-26).
**Tenhle zápis opravuje můj vlastní chybný závěr z téhož dne** — viz sekce úplně dole.

## Jak to doopravdy je

Editační okno v „Docházce new" (`openEdit` / `saveEdit` v `dochazka-po-zakazkach.html`)
neukládá napřímo do rozpadu. Podle druhu řádku volá:

| režim | co to je | kam se ukládá čas / zakázka / činnost |
|---|---|---|
| **W** | úsek na zakázce | `POST /app/attendance/fix/polozka` |
| **FIX** | docházka z aplikace | `POST /app/attendance/fix/entry` |
| **RO** | absence, historie z Centrály | neukládá se, jen čtení |

Obě cesty jsou **opravárenský engine** — povinný důvod, audit, notifikace dotčenému,
přepočet dne (`_att_automat_recalc_day`), kontrola překryvu a zamčeného období,
a hlavně přepočet hlavičky z položek, který nasadí `local_lock`.

**Přepnula to Peťa 3. 8. 2026** po případu Kolářové, kdy se uložil jen rozpad
a docházka zůstala stará → dny se rozcházely. V kódu je to okomentované.

## Starý endpoint `/app/dochazka-zak-tab/save` NENÍ mrtvý, ale dělá jen jedno

Volá se pouze z `wSavePozn()` a ukládá **jen poznámku** — schválně se **starými časy**,
aby nepřepsal to, co mezitím srovnala kaskáda. Pořadí je záměrné: nejdřív poznámka
se starými časy, teprve pak oprava přes engine.

Kdo bude ten endpoint číst samostatně, uvidí prostý `UPDATE tenant.vyroba_work`
bez auditu a bez přepočtu — a snadno z toho usoudí, že takhle se ukládají i časy.
**Neusuzuje správně.** Vždycky se podívej, kdo endpoint volá, ne jen co dělá.

## Důsledek pro kaskádu

Kaskáda `att_sync_vyroba_work` v kroku „vyplň okraje" přeskakuje hlavičky s `local_lock`.
Protože editace v Docházce new jde přes engine, který ten příznak nasadí,
**kaskáda úpravy z Docházky new nepřepisuje** — ani časy, ani zakázku a činnost
(ty ostatně nemění nikdy, v jejím UPDATE nejsou).

## OPRAVA MÉHO DŘÍVĚJŠÍHO ZÁVĚRU (Claude-26, 7. 9. 2026)

Ráno jsem zapsala `doc-dochazka-kaskada-neprepisuje-zakazku-ale-casy-ano` s tvrzením,
že úprava času v Docházce new se tiše vrátí, protože se nenasadí `local_lock`.
**To je nesprávné a ten zápis je zrušený.**

Chyba vznikla takhle: přečetla jsem endpoint `/app/dochazka-zak-tab/save`, viděla prostý
UPDATE bez auditu a přepočtu, a **neověřila, jestli ho formulář na časy vůbec volá**.
Nevolá — od 3. 8. 2026 jdou časy přes `fix/polozka`.

Peťa na základě toho chybného závěru rozhodla editaci z Docházky new odstranit;
rozhodnutí bylo vzato zpět, jakmile se chyba našla.

**Poučení, které stojí za víc než ten nález:** u endpointu nestačí přečíst, co dělá.
Je potřeba najít, **kdo ho volá a s čím** — jinak popíšeš mrtvou nebo vedlejší cestu
a vydáváš ji za hlavní. Platí zvlášť tam, kde se jedna obrazovka časem přepojila
na jiný engine a starý endpoint zůstal na okrajovou práci.

## Souvisí

- doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach — co z Docházky new zmizelo 31. 8. a proč
- doc-dochazka-oprava-polozek-obousmerny-sync — jak funguje fix/polozka a přepočet hlavičky
- doc-dochazka-att-entry-vyroba-work-kaskada — kanonický model hlavička × položky

