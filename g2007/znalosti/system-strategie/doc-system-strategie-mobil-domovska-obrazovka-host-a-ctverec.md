# Mobil, domovska obrazovka: prihlasovaci volby dole a nadpis nahore, fotka je ctverec misto kruhu (9. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Zadal Jirka Honomichl 9. 9. 2026, schvalila Marti-AI (msg 15252). Provedl Claude-28.**
Zdroj: `g2007.soubor`, kod `apps/api/static/mobile_parts/20_home_phone_notifs.js`.

## 1. Nepřihlaseny host: nadpis nahoru, prihlasovaci volby dolu

**Bylo:** kdyz appku spustil nekdo neprihlaseny, nadpis **STRATEGIE Mobil** i radek o odezve
visely nekde uprostred obrazovky a hned pod nimi karta s volbami (ukazka, heslo, odkaz, zajem).

**Proc:** `.homebg` je flex sloupec s `justify-content:flex-end`, tedy obsah se tlaci dolu.
Rozlozeni drzel **portret** pres `margin:auto` - jenze hostovi se portret schovava
(prazdny krouzek by vypadal jako chyba), takze zbytek se sesypal k sobe doprostred.

**Ted:** ve vetvi pro hosta dostane horni blok `#homeTop` **`margin-bottom:auto`**.
Automaticky spodni okraj pohlti volne misto -> nadpis a odezva vyjedou nahoru,
uvitaci karta zustane dole nad spodni listou. **Prihlaseneho uzivatele se to nedotkne.**

## 2. Fotka na plose je ctverec, ne kruh

`#homePortret` (220x220) mel `border-radius:50%`. Nove **`border-radius:14px`** - tedy ctverec
s jemne zaoblenymi rohy jako maji ostatni karty v appce. Uplne ostry roh by se s UI bil;
kdyby ho nekdo chtel, je to zmena jednoho cisla na `0`.

## Overeni

Na zive `/mobile`: ctverec videt na plose. Rozlozeni pro hosta se overilo **nakreslenim tehoz
stavu ve vlastnim okne prohlizece** (schovat portret, nastavit `margin-bottom:auto`, vlozit
kartu stejne velikosti) - nadpis skoncil 18 bodu od vrsku, spodek karty 797 z 889 bodu okna.

⚠️ **Nedelej to prihlasenim demo uctu** - `demo-login` prepise session v prohlizeci a odhlasi
cloveka, ktery ma treba rozdelanou smenu. Nahled ve vlastnim okne nic takoveho nedela.

