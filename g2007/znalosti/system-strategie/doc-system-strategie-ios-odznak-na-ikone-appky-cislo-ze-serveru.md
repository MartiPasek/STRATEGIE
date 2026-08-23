# iOS odznak na ikone appky: cislo posila server, a proc se timhle NEDOSTANE na nulu (24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Odznak na ikone iOS appky — cislo posila server

Zapsal Claude-28 (Jirka Honomichl) **24.8.2026**, schvalila Marti-AI (msg 13543).
Navazuje na `doc-system-strategie-mobil-ios-notifikace-apns`.

## Jak to bylo do 23.8.2026

Odznak si pocitala **vyhradne appka** (`PushNotifications.swift`), a to **jen ve dvou
okamzicich**: pri prechodu do popredi (`applicationDidBecomeActive`) a pri tuknuti na
notifikaci. Nastavila ho na pocet prikazu, ktere server vrati na `/app/{app_key}/commands/pending`.

**Server u notifikace zadne cislo neposilal** — v `_payload()` nebyl klic `badge` vubec.

**Dusledek:** kdo notifikaci jen odklikne a appku neotevre, kouka na **stare cislo**. Jirkovi
23.8. visela na ikone `1`, i kdyz uz nic necekalo — a nezmizela ani po otevreni appky.

## Co je nasazeno

**`dca1dc23`** — `_payload(cmd, odznak=None)` prida do `aps` klic `badge`. Cislo pocita nova
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

## ⚠️ NEDODELEK — takhle se odznak NEDOSTANE NA NULU

**Kazda odesilana notifikace se sama pocita jako cekajici**, takze nejnizsi cislo, jake kdy
odejde, je **1**. Odznak je tedy nove **pravdivy, ale neumi zhasnout**.

**Reseni** (neudelano, odlozeno Jirkou na 24.8. rano): kdyz uzivateli klesne pocet cekajicich
na nulu, poslat mu **"prazdny" push jen s `badge: 0`** — nic nezobrazi, jen srovna cislo.
Chce to **pamatovat si posledni poslane cislo** (jinak by se nula posilala porad dokola);
`fw.ios_push_token` na to dnes sloupec nema.

⚠️ **Sahá to do `_push_loop`** — tedy do MIST, ktera meni pripravena oprava smycky
(`OPRAVA_ios_push_smycka.md`). **Ma se to proto delat AZ SPOLU S NI, ne zvlast**, jinak si
dve session prepisou praci. Zmeny vyse (`_neodeslane`, `_payload`, `push_tick`) se s ni
zamerne nepotkavaly — to bylo pred nasazenim overeno.

## ⚠️ Co NENI vysvetlene

**Proc puvodni uvizla jednicka nesla dolu ani po otevreni appky, NEVIME.** Meli jsme dve
hypotezy a **obe padly pri zkousce**:
1. „na serveru porad neco ceka" — nectvrdilo se, `pending` bylo 0
2. „prepocet bezi driv, nez ma appka prihlaseni" — vyvraceno: po tuknuti se prikazy
   PROKAZATELNE oznacily jako `done` (23:55:36–38), takze appka se serverem mluvila

**Dnesni reseni to OBCHAZI, neleci.** Kdo na to sahne priste, at s tim pocita.

## Past pri overovani, kterou stoji za to znat

Cislo na odznaku nemusi sedet s tim, co jsi prave poslal — **muze mezitim prijit jina
notifikace**. 23.8. jsem predpovedel `1` a Jirka videl `2`; duvod se nasel az v datech:
**16 sekund po me zkousce prisla automaticka pulnocni notifikace „Odhlaseni o pulnoci"**
(prikaz 21344), takze v tu chvili cekaly dve veci a **2 bylo spravne cislo**.
**Nez vyslovis, ze odznak ukazuje spatne, podivej se na VSECHNY notifikace v tom okne** —
ne jen na svoji.

