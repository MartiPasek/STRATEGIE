# iOS odznak na ikone appky: server je hotovy a prokazany, zbytek je na strane telefonu (24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Odznak na ikone iOS appky — cislo posila server

Zapsal Claude-28 (Jirka Honomichl) **24.8.2026**, schvalila Marti-AI (msg 13543 a 13571).
Navazuje na `doc-system-strategie-mobil-ios-notifikace-apns`.

> ⚠️ **CTI NEJDRIV POSLEDNI KAPITOLU „Stav k 24.8.2026 — kde to konci".**
> Serverova strana je HOTOVA a PROKAZANA; odznak presto nezhasne a **dalsi patrani ze serveru
> NEMA SMYSL**. Kdo na to sahne, at nezacina od nuly — dnes uz padly dve hypotezy.

## Jak to bylo do 23.8.2026

Odznak si pocitala **vyhradne appka** (`PushNotifications.swift`), a to **jen ve dvou
okamzicich**: pri prechodu do popredi (`applicationDidBecomeActive`) a pri tuknuti na
notifikaci. Nastavila ho na pocet prikazu, ktere server vrati na `/app/{app_key}/commands/pending`.

**Server u notifikace zadne cislo neposilal** — v `_payload()` nebyl klic `badge` vubec.

**Dusledek:** kdo notifikaci jen odklikne a appku neotevre, kouka na **stare cislo**. Jirkovi
23.8. visela na ikone `1`, i kdyz uz nic necekalo — a nezmizela ani po otevreni appky.

## Co je nasazeno

**`dca1dc23`** — `_payload(cmd, odznak=None)` prida do `aps` klic `badge`. Cislo pocita
funkce `_pocet_cekajicich(s, app_key, user_id)` = `count(*)` nad `fw.mobile_command` pro
`status='pending'`, tedy **TOTEZ, co appce vraci `/commands/pending`** (kdyby se to rozeslo,
odznak by ukazoval jine cislo nez seznam v appce). V `push_tick` se pocita **jednou na dvojici
(app_key, uzivatel)** za kolo, ne na kazdy push.

Bezpecne chovani: kdyz je odznak `None` nebo zaporny (vypocet selhal), **klic `badge` se
vynecha** a notifikace odejde jako driv. Odznak je kosmetika a nesmi zabranit doruceni.

**`79dbc851`** — cislo se zapisuje k odeslane notifikaci do `fw.ios_push_sent.detail` jako
`badge=N` (pri uspechu tam driv byl prazdny retezec) + radek do logu.
**Proc:** pri ladeni nam nesedelo cislo na odznaku a **zpetne to neslo zjistit**, protoze se
nikam neukladalo — hadalo se misto cteni. Ted staci jeden `SELECT`.

**`cd844f8d`** (24.8.) — zhasinani na nulu. Kdyz uzivateli klesne pocet cekajicich na nulu,
odejde **„prazdny" push jen s `badge: 0`** — nic nezobrazi ani nepipne, jen srovna cislo.
Pamet je novy sloupec **`fw.ios_push_token.last_badge`**, aby se nula poslala JEDNOU, ne
kazdych 5 s dokola. Nula jde na **vsechna aktivni zarizeni toho cloveka** (upozornila
Marti-AI: kdo ma iPhone i iPad, musi dostat nulu na obojí).
Tamtez: **`apns-collapse-id` se posila jen kdyz ma hodnotu** — prazdny umi Apple odmitnout
jako `BadCollapseId`, coz je v `_TRVALE`, a push by se odepsal natrvalo.

**`ca11a55e`** (24.8.) — u NEPOVEDENEHO zhasnuti se zapise odpoved Apple do logu i do
`fw.ios_push_token.last_error`; pri uspechu se `last_error` smaze. Bez toho se jen hadalo,
protoze zhasinaci push nepatri k zadnemu prikazu, takze nejde do `ios_push_sent`.

## Stav k 24.8.2026 — kde to konci

**SERVEROVA STRANA JE HOTOVA A PROKAZANA.** Nejde o domnenku, plyne to z kodu:
`last_badge` se prepne na 0 **jedine po HTTP 200 od Apple**, a `last_error` se plni **jen pri
odmitnuti**. Zmereno po ostre zkousce: prikaz `done`, 0 cekajicich, `last_badge = 0`,
`last_error` prazdny → **Apple zhasinaci push PRIJAL**.

**Odznak na iPhonu presto zustal na 1.** Chyba je tedy **mezi „Apple prijal" a „na ikone je
nula"**, tedy na strane telefonu — a **ze serveru se to zjistit NEDA**.

### Dve hypotezy, ktere PADLY (neopakovat)

1. *„Appka prepocitava odznak az pri prechodu do popredi a nema v tu chvili prihlaseni."*
   **Vyvraceno:** po tuknuti se prikazy PROKAZATELNE oznacily jako `done` (23.8. v 23:55:36–38),
   takze appka se serverem mluvila.
2. *„Nizka nalehavost (priorita 5 u tiche notifikace) zpusobuje zpozdene doruceni."*
   **Vyvraceno:** ani po nekolika minutach se odznak nezmenil.

### Zbyvajici PODEZRENI (schvalne ne zavery)

- jak presne je oznaceny push bez viditelneho obsahu — `apns-push-type: alert` u payloadu,
  ktery nema `alert` ani `sound`, jen `badge`;
- jestli si appka cislo neprepisuje zpatky.

### Co by to rozhodlo

**Protokol zarizeni pres Xcode** (iPhone pripojeny k Macu) — videt, co appka s tim
upozornenim udelala. Ze serveru to nejde.

**Rozhodl Jirka 24.8.2026: nechat na Mac s Xcode, nehonit dohady.**
Funkcne nic neblokuje — notifikace chodi a doruci se; odznak je jedina kosmeticka vada.

## Past pri overovani, kterou stoji za to znat

Cislo na odznaku nemusi sedet s tim, co jsi prave poslal — **muze mezitim prijit jina
notifikace**. 23.8. jsem predpovedel `1` a Jirka videl `2`; duvod se nasel az v datech:
**16 sekund po me zkousce prisla automaticka pulnocni notifikace „Odhlaseni o pulnoci"**
(prikaz 21344), takze v tu chvili cekaly dve veci a **2 bylo spravne cislo**.
**Nez vyslovis, ze odznak ukazuje spatne, podivej se na VSECHNY notifikace v tom okne** —
ne jen na svoji.

## Pouceni o vlastni praci

Dvakrat za dva dny jsem postavil neco, na co jsem pak **nevidel** — cislo odznaku se nikam
neukladalo (79dbc851 to dodelal) a odpoved Apple u zhasinaciho pushe taky ne (ca11a55e).
Obojikrat se pak hadalo misto cteni. **Kdyz pridavas chovani, pridej rovnou i misto, kde se
pozna, ze fungovalo** — jinak prvni ladeni zaplati cely usporeny cas i s uroky.

