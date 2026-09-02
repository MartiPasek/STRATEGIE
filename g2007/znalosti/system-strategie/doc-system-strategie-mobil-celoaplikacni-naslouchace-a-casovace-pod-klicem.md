# Mobil: celoaplikacni naslouchace a casovace registruj pod klicem pres __M2W.onGlobal / __M2W.everyMs (jinak se pri opakovanem spusteni dilku zdvoji)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil: celoaplikační naslouchače a časovače registruj pod klíčem

**Ověřeno čtením živého obsahu 2. 9. 2026** (Claude-28 / Jirka Honomichl) — dílek
`apps/api/static/mobile_parts/10_core.js` v `g2007.soubor`, ne z popisu druhé ruky.
Pomocníky postavilo téhož dne jiné okno C-28, schválila Marti-AI.

## Pravidlo

Celoaplikační **naslouchač události** nebo **opakovaný časovač** v mobilu registruj přes:

- `window.__M2W.onGlobal(klic, cil, udalost, fn, opt)` — místo `cil.addEventListener(...)`
- `window.__M2W.everyMs(klic, fn, ms)` — místo `setInterval(fn, ms)`

⛔ **Nikdy holé `addEventListener` / `setInterval`** pro věci, které mají žít po celou dobu
běhu aplikace.

## Proč

Dílek mobilu se může spustit **víckrát** — appka umí od 2. 9. 2026 vyměnit obsah za běhu.
Holý naslouchač se při druhém spuštění **přidá k tomu prvnímu**: od té chvíle jeden dotyk
vyvolá obsluhu dvakrát a časovač tiká dvojmo. **Nic to nenahlásí** — žádná chyba v konzoli,
žádný záznam. Je to tentýž druh vady jako
[[doc-system-strategie-ios-gesto-zpet-dve-naraz]], kde v appce běžela dvě gesta naráz.

## Jak to funguje (přečteno v kódu)

Společný registr je `window.__M2W._reg`.

- **`onGlobal`** při volání se **stejným klíčem nejdřív odregistruje předchozí** naslouchač
  (`removeEventListener` na uloženou trojici cíl/událost/funkce) a teprve pak zaregistruje nový.
- **`everyMs`** drží časovač pod klíčem `"t-" + klic`, předchozí zruší `clearInterval`
  a vrací `id` toho nového.
- Obojí je **fail-safe**: když registrace selže, spadne to zpět na holé
  `addEventListener` / `setInterval`, takže se nic nerozbije.
- **První spuštění se chová úplně stejně jako předtím.** Konvence nic nemění, dokud se
  dílek nespustí podruhé — proto ji jde zavádět postupně.

**Klíč volí autor.** Má být stabilní (nesmí se měnit mezi spuštěními) a jedinečný pro daný
účel — dvě různé věci pod stejným klíčem by se navzájem odregistrovaly.

## Vedlejší, ale užitečné: `__M2W._inflight`

Funkce `api()` nově **počítá probíhající dotazy** v `window.__M2W._inflight` a u jiné metody
než `GET` si značí čas posledního zápisu do `window.__M2W._lastWrite`. Na chování `api()`
se jinak nic nemění — vrací se tatáž odpověď, jen se okolo počítá. Hodí se, když potřebuješ
vědět, že zrovna něco běží (třeba než uděláš něco rušivého).

## Kde se to k 2. 9. 2026 už používá

Definice v `10_core.js`; použito v `30_contacts_settings.js` (`onGlobal`),
`70_tail.js` (`everyMs`) a `74_claude27_render_init.js` (`_inflight`).

## Souvisí

[[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]] ·
[[doc-system-strategie-mobil-fragmenty-scope-a-nativni-dialogy]] ·
[[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

