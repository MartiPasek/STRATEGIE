# Nová obrazovka v mobilu se registruje na ČTYŘECH místech, ne na třech (13. 9. 2026 páté místo: mapa spodní lišty)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Zapsal Claude-28 (zadal Jiří Honomichl) 13. 9. 2026, schválila Marti-AI (msg 15357 a 15366).
Ověřeno naostro téhož dne při zakládání obrazovky `moje_dochazka_b`.

## Proč to vzniklo

> **Není to nový objev — je to sjednocení.** Čtyři místa popsala už znalost
> `doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026` (6. 9. 2026, oddíl
> „Smazání obrazovky = Čtyři místa, ne jedno"). O tři dny později ale vznikl zápis, který
> tvrdil tři místa — a **nic to nenahlásilo**. 13. 9. 2026 se na to přišlo znovu, tentokrát
> až naostro. **Od 13. 9. 2026 je závazným seznamem těch míst tenhle dokument** — pro
> zakládání i pro rušení obrazovky; ostatní dva na něj odkazují a seznam již neopakují.

Znalost `doc-dochazka-pochuzky-ui-predani-kotvy-a-postup` (obrazovka `cesta_vyber`, C24, 9. 9. 2026)
uvádí, že se obrazovka registruje na **třech** místech. Ve skutečnosti jsou **čtyři** — chybí
**navázání vykreslovací funkce na obal** (`__setImpl`) na konci dílku.

**Co se stane, když to čtvrté místo chybí:** obrazovka **tiše neexistuje**. Dlaždice se tváří
funkčně, po klepnutí se nestane nic a jediná stopa je hláška v konzoli prohlížeče
(`[mobile2] volano pred inicializaci fragmentu`) — tu na telefonu nikdo neuvidí.
Žádná chybová hláška, žádný pád, jen mrtvé tlačítko.

## Čtyři místa registrace (plus samotná vykreslovací funkce)

Pro obrazovku s identifikátorem `<id>`:

1. **`10_core.js`** — založení obalu: `window.__M2W.<id> = mkWrap();`
   `mkWrap()` vrací funkci, která si implementaci doplní teprve později. Existuje proto, že
   **každý dílek je vlastní uzavřený blok** a funkce z něj není odjinud vidět —
   viz `doc-system-strategie-mobil-dilky-nejsou-jedna-closure`.
2. **dílek s obrazovkou** (např. `60_dochazka.js`) — samotná vykreslovací funkce
   `function <id>(){ ... }`. Vzor: `window.__M2W.app.innerHTML = topbar("Nadpis", true);`
   a obsah se přidává do `window.__M2W.app`.
3. **týž dílek, úplně na konci** — `window.__M2W.<id>.__setImpl(<id>);` v řadě ostatních
   `__setImpl`. **Tohle je to místo, které se zapomíná a které v původním návodu chybělo.**
4. **`72_migrace_sw_isds.js`** — převzetí obalu do místního jména: `<id>=window.__M2W.<id>,`
5. **`73_pref_poptavka.js`** — zařazení do mapy obrazovek: `<id>:<id>,` uvnitř `var SCREENS={...}`.

6. **`73_pref_poptavka.js` podruhé — mapa `SCREEN_TAB`** (`<id>:"dochazka",`): určuje, která
   ikona spodní lišty se u té obrazovky rozsvítí. Není to registrace v užším smyslu (bez ní
   obrazovka funguje), ale **při RUŠENÍ obrazovky se na to zapomíná** a v mapě zůstane mrtvý
   záznam. *(Doplnil Claude-28 13. 9. 2026 při rušení obrazovek `doch_dnesek` a `doch_historie`
   — zbyly právě tady, když byla ostatní čtyři místa uklizená. Zadal Jiří Honomichl, schválila
   Marti-AI. Souvisí: `doc-system-strategie-mobil-spodni-lista-sviti-podle-obrazovky-8-9-2026`.)*

Mapu čte vykreslovací smyčka v `74_claude27_render_init.js` jako
`window.__M2W.SCREENS[stack[posledni]]()`. Když v mapě identifikátor není, spadne to na `home` —
tedy další způsob, jak obrazovka zmizí bez hlášky.

## Jak si ověřit, že je to opravdu hotové

V prohlížeči na živém `/mobile` (ne na kopii z disku):

- `!!window.__M2W.SCREENS.<id>` musí být `true` — obrazovka je v mapě,
- po klepnutí na dlaždici musí `window.__M2W.stack` končit tím `<id>`,
- `window.__M2W.back()` musí zásobník zase zkrátit.

Teprve pak je obrazovka živá. Samotné „dlaždice je vidět" nedokazuje nic.

## Dlaždice je samostatná věc

`appCell("<ikona>","<popisek>",0,function(){ go("<id>"); })` a přidání do příslušné mřížky.
Když dlaždice vede na `openInApp("/nejaka-adresa")`, nejde o obrazovku appky, ale o webovou
stránku otevřenou uvnitř appky — ta se registruje jinak a název v její hlavičce drží mapa cest
v `30_contacts_settings.js`.

## Jak zapsat

Dílky žijí v databázi (`g2007.soubor`), po úpravě je potřeba publikace `mobile.html`.
Postup a pasti: `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
Dílky `60_dochazka.js`, `10_core.js`, `72_migrace_sw_isds.js` a `73_pref_poptavka.js` jsou
sdílené a horké — ohlas se přes `@@WORK` a piš s pojistkou na otisk souboru, jinak přepíšeš
cizí práci.

