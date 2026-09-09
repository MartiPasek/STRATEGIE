# Mobil: v každém skriptovém bloku jsou rozbalené jiné pomocné funkce (back chybí) — tichý pád po úspěšném zápisu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobilní appka: v každém skriptovém bloku jsou rozbalené JINÉ pomocné funkce

**Nález naostro 9. 9. 2026 (C24 / Kristý), stálo to půl hodiny hledání.**

Stránka `mobile.html` se skládá z dílků do **několika `<script>` bloků**. Každý blok si na
začátku rozbalí z `window.__M2W` do lokálních proměnných **jen ty pomocníky, které v něm
někdo dosud potřeboval** — ne všechny. Kdo přidá do dílku novou obrazovku a použije
pomocníka, který v tom bloku rozbalený není, dostane `ReferenceError` **až za běhu, při kliknutí**.

## Konkrétně (stav 9. 9. 2026)

| blok | rozbaleno |
|---|---|
| blok s `60_dochazka.js` (rozbaluje se v `52_vyroba.js`) | `api, appCell, el, esc, go, topbar` — **`back` NE** |
| následující blok (patka `60_dochazka.js`) | `_tapFeedback, api, back, el, esc, go, renderNav, topbar, vyInitial` |

## Jak se to projevilo (a proč se to tak blbě hledá)

Nová obrazovka `cesta_vyber` volala holé `back()`. Pád nastal **až po úspěšném zápisu**
(`checkin` 200 + `announce` 200) a spolkl ho `.catch` v tom samém řetězu:

- tlačítko vypadalo, **jako by nebylo klikací** — nic se nestalo, žádná hláška,
- `getEventListeners` přitom ukazoval `["click"]` a `elementFromPoint` vracel samo tlačítko,
- obrazovka se nevrátila zpět → **neproběhl `dochLoad()`** → člověk viděl staré hodiny
  a myslel si, že „se hodiny nepřepočítaly“ (přepočítané byly, jen nepřekreslené),
- protože to vypadalo mrtvě, člověk ťukal znovu → **13 nulových úseků** v `att_entry`.

## Pravidla, která z toho plynou

1. **Než v dílku použiješ pomocníka, ověř, že je v TOM bloku rozbalený**
   (`grep` na `=window.__M2W.` v hlavičce bloku). Když si nejsi jistá, piš
   **`window.__M2W.<jmeno>()`** — funguje vždy a nic nestojí.
2. **`.catch` nesmí být němý.** Vždy aspoň `console.error('[mobile2] <obrazovka>:', e)`.
   Němý catch tenhle pád schoval; s logem by byl vidět na první pokus.
3. **Chybu hlas viditelně v obrazovce** (`.errbar`), ne `alert`em — alert jde v prohlížeči
   umlčet („nezobrazovat další dialogy“) a pak je chování k nerozeznání od mrtvého tlačítka.
4. **Appka NEMÁ v CSS `:disabled`** (`02_styles.html`) — zakázané tlačítko vypadá stejně
   jako aktivní. „Nezešedlo to“ tedy NENÍ důkaz, že se obsluha nespustila; kdo chce
   vizuální zpětnou vazbu, musí si nastavit `style.opacity` sám.

## Postup, který k nálezu vedl (použij ho příště)

V konzoli u nefunkčního tlačítka: `elementFromPoint` na jeho střed (leží na něm něco?),
`getEventListeners` (má vůbec posluchače?), a **záložka Network** (odešel dotaz a s jakým
stavem?). Když dotaz odešel a vrátil 200, chyba je **za** zápisem, ne před ním.

