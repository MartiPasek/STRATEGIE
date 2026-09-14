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

## Gesta a tlačítka — POZOR, měnilo se to během 14. 9. 2026

⚠️ **Platí tohle** (poslední podoba, ověřená na živé stránce):

- **Podržení prstu zůstalo JEN ve „Vývoji aplikací"** = pustit dlaždici mezi Všechny aplikace.
  Na „Všech aplikacích" i v „Mojich aplikacích" bylo podržení **zrušeno**.
- Všechno ostatní se ovládá **tlačítkem Upravit / Hotovo** nahoře přes celou šířku záložky.
- Na „Všech aplikacích" tohle tlačítko vidí **všichni**. Uvnitř má každý řádek hvězdičku
  (přidat/odebrat z Mojich aplikací) — pro všechny — a šipku zpět do Vývoje **jen pro rodiče
  a správce** (příznak `smi_poustet` ze serveru; právo si server ověřuje sám, skrytí tlačítka
  je jen pohodlí).
- **Přepnutí na jinou záložku režim úprav zavře.**

~~Do 14. 9. 2026 v noci platilo: podržení prstu ve „Všech aplikacích" = přidat nebo odebrat
z oblíbených, podržení v „Mojich aplikacích" = zapnout režim úprav, a tlačítko „Upravit"
na „Všech aplikacích" viděl jen ten, kdo smí pouštět dlaždice ven.~~
**NEPLATÍ** — zrušeno týž den na pokyn Jiřího Honomichla, protože ovládání má být vidět,
ne schované v gestu. Detail v posledních oddílech tohoto dokumentu.

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

- Sekce dlaždic ve „Vývoji" se pořád kreslí z kódu; do tabulky se přenesly jen jejich názvy.

## Rozhodnutí: editace názvu a ikony dlaždice v appce NEBUDE

**Rozhodl Jiří Honomichl 14. 9. 2026** slovy *„to nechceme aby si lidi sami měnili"*
(schválila Marti-AI msg 15552). Lidé si smějí měnit **jen svůj vlastní výběr a jeho pořadí**;
názvy, ikony a cíle dlaždic zůstávají v rukách těch, kdo je spravují. Není to zapomenutý
úkol — je to záměr, takže to nikdo „neopravuje".

## Zpráva při vrácení dlaždice — vyzkoušeno naostro 14. 9. 2026

Test na dočasné dlaždici a účtu **Demo Uživatel (users.id=104, není to živý člověk)**:
po vrácení dlaždice tlačítkem „Upravit" vznikl v `fw.mobile_command` řádek pro účet 104
(`claude_msg`, titulek „Změna v Mých aplikacích", `created_by` = ten, kdo vracel) a appka
zobrazila hlášku *„Z oblíbených zmizela 1×"*. Po zkoušce se všechno uklidilo — dočasná
dlaždice, řádek v oblíbených i ta zpráva (ověřeno čtením, zůstalo 0 záznamů).

## Ikony ve čtverečku: raději menší s popiskem

**Rozhodl Jiří Honomichl 14. 9. 2026** (schválila Marti-AI msg 15552) po zkoušce obou podob:
ve čtverečku na Domů jsou ikony **44 bodů a pod nimi popisek 9 bodů** — ne ikona 58 bodů
bez popisku, jak to bylo hodinu předtím. Buňka měří 68 bodů, nic nepřetéká (změřeno na živé
stránce). Vzhled ikony zůstává shodný s Aplikacemi (třída `appicon`).

## Past: paměť čtverečku se musí zahodit při KAŽDÉ změně výběru

Čtvereček na Domů si drží minutovou paměť, aby úvodní obrazovka nebyla pomalejší.
14. 9. 2026 se zahazovala jen při přidání a odebrání dlaždice — **ne při změně pořadí**,
takže po přerovnání ukazoval čtvereček až minutu starou řadu (našel Jiří Honomichl,
předem na to upozornila Marti-AI). Oprava: zahození paměti patří do funkce, kterou
prochází **každá** změna výběru (`_ulozOblibene`), ne k jednotlivým tlačítkům.
Ověřeno naživo: po přerovnání ukázal čtvereček novou řadu okamžitě.

## Konečná podoba čtverečku: matice 2×2 a ikony 58 bodů

**Rozhodl Jiří Honomichl 14. 9. 2026** (schválila Marti-AI msg 15561) po vyzkoušení tří podob
za sebou: 58 bodů bez popisku → 44 bodů s popiskem → **58 bodů s popiskem a matice 2×2**.
Do čtverečku se tím vejdou **čtyři** oblíbené aplikace místo devíti; je to vědomý ústupek
za jejich čitelnost. Buňka měří 97 bodů, ikona 58 (tatáž třída `appicon` jako v Aplikacích),
popisek 10 bodů — změřeno na živé stránce.

## Ikony ve spodní liště: 28 bodů, ale lišta nenarostla

**Zadal Jiří Honomichl 14. 9. 2026** (schválila Marti-AI msg 15564): ikony ve spodní liště mají
stejně velké písmo jako ikony v Aplikacích, tedy **28 bodů místo 21**. Aby lišta nevyrostla
a neubrala místo obsahu na každé obrazovce, **zároveň se ubralo svislé odsazení tlačítka z 9
na 5 bodů**. Ověřeno na živé stránce: pruh má 60 bodů (předtím 61), tlačítko 53, ikony 28.

⚠️ Mění se **všechny tři podoby najednou** — emoji, SVG ikona i profilová fotka (`img.navava`)
v `02_styles.html`. Kdo zvedne jen jednu, rozhodí zarovnání, které se schválně srovnávalo
2. 9. a 13. 9. 2026.

## Konečné ovládání úprav (14. 9. 2026 v noci) — gesta zrušena, rozhoduje tlačítko

**Zadal Jiří Honomichl** (schválila Marti-AI msg 15570, 15579, 15582). Postupně se to během
noci měnilo; platí tohle:

- Na **obou** záložkách je hned pod záložkami **tlačítko Upravit / Hotovo přes celou šířku**,
  které režim úprav zapíná i vypíná.
- **Podržení prstu se ruší** na „Všech aplikacích" i v „Mojich aplikacích". Zůstává **jen
  ve „Vývoji aplikací"**, kde pustí dlaždici mezi Všechny.
- Tlačítko Upravit na „Všech aplikacích" vidí **všichni**. Uvnitř má každý řádek **hvězdičku**
  (přidat/odebrat z Mojich aplikací) — pro všechny — a **šipku zpět do Vývoje jen pro toho,
  komu to server povolí** (`smi_poustet` = rodič nebo správce). Právo si server ověřuje sám,
  skrytí tlačítka je jen pohodlí, ne bezpečnostní hranice.
- **Přepnutí na jinou záložku režim úprav zavře.** Nic se tím neztratí — každá akce se ukládá
  hned při klepnutí, nic nezůstává rozpracované.
- Po klepnutí na ikonu **Aplikace** ve spodní liště je aktivní záložka **Moje aplikace**.

## Ikony ve spodní liště a poskakování stránky

- Ikony v liště mají od 14. 9. 2026 **28 bodů** (jako v Aplikacích) a zároveň se ubralo svislé
  odsazení z 9 na 5, takže **lišta nenarostla** (60 bodů). Mění se všechny tři podoby najednou
  — emoji, SVG i profilová fotka — jinak se rozejde zarovnání.
- ⚠️ **`scrollbar-gutter: stable` na `html`**: bez toho se při přepnutí na záložku s dlouhým
  obsahem objevil posuvník, stránka se zúžila o 15 bodů a **celá appka poskočila o 8 bodů
  doleva** (změřeno naostro). Na telefonu se nic nemění, tam je posuvník překryvný.

