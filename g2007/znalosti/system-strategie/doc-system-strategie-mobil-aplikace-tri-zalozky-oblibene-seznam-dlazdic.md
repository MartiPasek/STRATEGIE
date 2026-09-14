# Mobil, obrazovka Aplikace: tri zalozky (Moje / Vsechny / Vyvoj), vlastni vyber oblibenych a seznam dlazdic v databazi (13.-14. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Mobil, obrazovka Aplikace: tři záložky, vlastní výběr oblíbených a seznam dlaždic v databázi (13.–14. 9. 2026)

**Zadal Jiří Honomichl 13.–14. 9. 2026, schválila Marti-AI (msg 15486, 15495, 15504, 15514, 15525, 15528, 15537, 15540, 15549). Provedl Claude-28.**

## Co se změnilo

Obrazovka **Aplikace** se rozdělila na **tři záložky** — jsou to tři fáze života aplikace:

| záložka | kdo ji vidí | co je v ní |
|---|---|---|
| **Moje aplikace** | všichni | vlastní výběr každého člověka, v jeho vlastním pořadí |
| **Všechny aplikace** | všichni | aplikace, které jsou hotové a puštěné ven |
| **Vývoj aplikací** | **jen rodič nebo správce** | všechno, co ještě není vyzkoušené a doladěné |

Vzhled záložek je převzatý 1 : 1 z obrazovky **Firma** (dílek `51_skupiny_sdileny.js`) — podtržení
místo vyplněných tlačítek. Výchozí po otevření je **Všechny aplikace**, aby člověk nekoukal na prázdno.

⚠️ **Záložka Vývoj se lidem bez práva vůbec NESTAVÍ** — není jen skrytá. Skrytá buňka by šla
odkrýt hledáním aplikací (`_filtruj` přepisuje `display` všem buňkám). Ověřeno na živé stránce:
běžný člověk má ve stránce jen dlaždice ze „Všech aplikací", žádné hledání a žádnou sekci.

## Kde to žije

| věc | místo |
|---|---|
| seznam dlaždic + stav vývoj/všechny | `public.mobile_app_dlazdice` (kod, nazev, ikona, sekce, poradi, akce_typ, akce_cil, zalozka, aktivni) |
| vlastní výběr člověka | `public.mobile_app_oblibene` (user_id, app_kod, poradi) |
| čtení výběru / uložení výběru | `g2007.python` **mobile_oblibene**, **mobile_oblibene_uloz** |
| čtení puštěných dlaždic + právo pouštět | `g2007.python` **mobile_dlazdice** |
| puštění ven / vrácení do vývoje | `g2007.python` **mobile_dlazdice_pust**, **mobile_dlazdice_vrat** |
| obrazovka | `g2007.soubor` `apps/api/static/mobile_parts/35_apps_vedeni.js` |
| čtvereček na Domů | `g2007.soubor` `apps/api/static/mobile_parts/20_home_phone_notifs.js` |

Volá se přes `/api/v1/erp/app/erp_registry/run` s `args ["__uid__", …]` — do jádra se nesahalo.
**Právo se ověřuje na serveru** (`users.is_admin` nebo `is_marti_parent`), telefonu se nevěří;
člověk čte a mění výhradně svůj vlastní výběr, protože přihlášení bere jádro samo.

## Tři různá gesta — neslévat je

- **Podržení prstu ve „Vývoji aplikací"** = pustit dlaždici mezi Všechny aplikace.
- **Podržení prstu ve „Všech aplikacích"** = přidat/odebrat z Mojich aplikací (⭐ na dlaždici).
- **Podržení prstu v „Mojich aplikacích"** = zapnout režim úprav (šipky ▲▼ a křížek).
- **Tlačítko „Upravit"** na Všech aplikacích (vidí ho jen ten, kdo smí pouštět) = vrátit dlaždici
  zpět do Vývoje. Vědomě to NENÍ podržení prstu, aby se gesta nesrazila.

## Vrácení do Vývoje sahá i do dat ostatních lidí

`mobile_dlazdice_vrat` dlaždici zároveň **smaže z oblíbených všem**, kdo si ji přidali — jinak by
jim v Mojich aplikacích visel mrtvý odkaz. **Každý dotčený člověk o tom dostane zprávu do appky**
(`fw.mobile_command`, stejnou cestou jako notifikace u oprav docházky ve funkci `att_fix_notify`);
tomu, kdo vrácení provedl, se zpráva neposílá. Návratovka říká, kolika lidem zpráva šla.

## Čtvereček s fotkou na obrazovce Domů

Klepnutí na čtvereček (`homePortret`) fotku prolne na **mřížku 3 × 3 s ikonami z Mojich aplikací**
(max devět, ikony ve stejné velikosti jako v Aplikacích — používá se tatáž třída `appicon`).
Když člověk do dvou vteřin na žádnou ikonu neklepne, fotka se vrátí; klepnutí na ikonu odpočet
zruší a aplikaci otevře. Popisky pod ikonami se do čtverce nevešly, proto tam nejsou (vědomý ústupek).
Výběr se načítá až při prvním klepnutí a drží se minutu v paměti; při změně výběru se paměť zahazuje
(`window.__M2W._domuMojeApp = null`).

## Pasti, na které se dnes narazilo

1. ⛔ **Seznam puštěných dlaždic NEVYPISUJ do znalostí.** Mění se přímo v appce (kdokoli s právem
   ho mění podržením prstu), takže jakýkoli výčet je za den nepravdivý. Čti ho z tabulky.
2. ⚠️ **Proměnná naplněná dřív, než je deklarovaná níž přes `var`, se tiše vynuluje.**
   14. 9. kvůli tomu spadlo vykreslování celé záložky „Všechny aplikace" (`TypeError: Cannot set
   properties of null`) a **14 minut ji měli všichni lidé prázdnou**. Deklaruj proměnnou tam,
   kde ji plníš.
3. ⚠️ **Po nasazení drží prohlížeč i appka starou stránku.** Kdo ověřuje hned po publikaci, měří
   starý kód a vidí „nefunguje to". Otevři `/mobile?fresh=<cokoli>`, teprve to je skutečný stav.
4. ⚠️ **Dlaždice s obrázkem místo emoji** (Web, STRATEGIE, Tvoje Marti) se bez pevného rámečku
   roztáhnou přes půl řádku. Ikonu vkládej do prvku s pevnou velikostí, u obrázku nastav
   `objectFit: contain` — nebo rovnou použij třídu `appicon`.
5. ⚠️ **Kód dlaždice se odvozuje z názvu** (bez diakritiky, malými písmeny, ostatní znaky na
   podtržítko) a je klíčem do oblíbených. **Při přejmenování dlaždice se kód nesmí měnit**,
   jinak lidem výběr vyprchá.

## Dopad jmenovitě

Rodič nebo správce jsou k 14. 9. 2026 **tři lidé — Marti Pašek (1), Kristýna Marešová (11)
a Jiří Honomichl (20)**; jen oni vidí záložku Vývoj a smí pouštět aplikace ven. Ostatních
34 přihlašitelných lidí vidí v Aplikacích jen to, co je puštěné. Jirka byl na tenhle dopad
výslovně upozorněn a rozhodl takto; „Moje aplikace" si lidé plní sami.

## Co zůstalo otevřené

- Odeslání zprávy při vrácení dlaždice **nebylo vyzkoušené naostro** (znamenalo by to někomu
  doopravdy sebrat dlaždici); ověří se při prvním skutečném vrácení.
- Cesta zpět má jen tlačítko „Upravit"; **editace názvu a ikony dlaždice v appce zatím není**.
- Sekce dlaždic ve „Vývoji" se pořád kreslí z kódu; do tabulky se přenesly jen jejich názvy.

