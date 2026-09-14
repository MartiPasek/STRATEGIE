# Mobil: ikona v nadpisu obrazovky ma na vsech obrazovkach stejnou velikost (topbar oddeluje ikonu, 14. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobil: ikona v nadpisu obrazovky má na všech obrazovkách stejnou velikost (14. 9. 2026)

**Zadal Jiří Honomichl 14. 9. 2026, schválila Marti-AI (msg 15600). Provedl Claude-28.**

## Co se změnilo a proč

Text nadpisu byl na všech obrazovkách stejný už dřív (21 bodů) — **lišila se jen ikona**.
Emoji se totiž kreslí ve velikosti písma (21), zatímco obrazovka Aplikace dostala SVG mřížku
28 bodů a jejím nadpisem vybočovala (33 bodů proti 28 u ostatních).

Nově funkce **`topbar()` v dílku `10_core.js`** oddělí úvodní ikonu nadpisu do vlastního
prvku `<span class="titleIk">` a styl `.topbar .title .titleIk` jí dá **pevných 28 bodů**.
Text zůstává 21 bodů a dál se escapuje. Výsledek ověřený na živé stránce: nadpisy mají
shodně 31 bodů a ikona 28 na všech obrazovkách (emoji i SVG).

## Jak se ikona rozpoznává — a kdy se NErozpozná

Za ikonu se považuje **jen úvodní „slovo" nadpisu, které nezačíná písmenem, číslicí ani
závorkou, a po kterém následuje mezera**. Jinak se nadpis vykreslí přesně jako dřív
(celý přes `esc()`). To je schválně opatrné — `topbar()` používají **všechny** obrazovky
a chybné rozpoznání by rozhodilo nadpisy v celé aplikaci.

⚠️ **Text nadpisu se pořád escapuje.** Do `topbar()` se nedá poslat HTML a nesmí se to
zavádět — kdo potřebuje vlastní značku v nadpisu (například SVG), vloží ji po vykreslení
do `h1.title` ve své obrazovce a použije **tutéž třídu `titleIk`**, aby výška seděla
(tak to dělá obrazovka Aplikace).

## Co se tím nezměnilo

- Obrazovka **Domů** nadpis přes `topbar()` nestaví — má vlastní skrytý nadpis a velký
  titulek „STRATEGIE Mobil". Té se změna netýká.
- Nadpisy **bez ikony** (například „Nastavení") zůstávají jen s textem, výška 28 bodů.

## Jak se ověřovalo

Před změnou i po ní se na živé stránce změřily nadpisy na pěti až osmi obrazovkách
(Aplikace, Kontakty, Moje osobní údaje, Kdo kde dnes, Zadat úkol, Dokumentace, Skupiny,
Výuka, Nastavení): velikost ikony, velikost textu, výška nadpisu a jestli se někde
nadpis neztratil nebo nevypsal jako holý kód. Konzole bez chyb.

