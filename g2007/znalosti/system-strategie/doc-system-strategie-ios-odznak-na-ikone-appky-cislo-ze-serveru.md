# Odznak na ikone iOS appky: server posila cislo (dokoncene) — pricina nezhasinani NALEZENA a OPRAVENA 24.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Odznak na ikone iOS appky — cislo posila server

Zapsal Claude-28 (Jirka Honomichl) **24.8.2026**, schvalila Marti-AI (msg 13543 a 13571).
Navazuje na `doc-system-strategie-mobil-ios-notifikace-apns`.

> ✅ **VYRESENO 24.8.2026 vecer.** Priblizna 24.8.2026 dopoledne tu stalo „server hotovy,
> priblizna na strane telefonu, dalsi patrani ze serveru nema smysl — nechat na Mac s Xcode".
> To uz neplati — pricina na strane appky byla ten den vecer nalezena a opravena
> (viz kapitola „VYRESENO" dole). Historie patrani nize zustava jako zaznam, jak se na to
> prislo, ne jako navod pro pristi hledani stejne chyby.

## Jak to bylo do 23.8.2026

Odznak si pocitala **vyhradne appka** (`PushNotifications.swift`), a to **jen ve dvou okamzicich**:
pri prechodu do popredi (`applicationDidBecomeActive`) a pri tuknuti na notifikaci. Nastavila ho
na pocet prikazu, ktere server vrati na `/app/{app_key}/commands/pending`.

**Server u notifikace zadne cislo neposilal** — v `_payload()` nebyl klic `badge` vubec.

**Dusledek:** kdo notifikaci jen odklikne a appku neotevre, kouka na **stare cislo**. Jirkovi
23.8. visela na ikone `1`, i kdyz uz nic necekalo — a nezmizela ani po otevreni appky.

## Co je nasazeno (serverova cast)

**`dca1dc23`** — `_payload(cmd, odznak=None)` prida do `aps` klic `badge`. Cislo pocita funkce
`_pocet_cekajicich(s, app_key, user_id)` = `count(*)` nad `fw.mobile_command` pro `status='pending'`,
tedy **TOTEZ, co appce vraci `/commands/pending`** (kdyby se to rozeslo, odznak by ukazoval jine
cislo nez seznam v appce). V `push_tick` se pocita **jednou na dvojici (app_key, uzivatel)** za
kolo, ne na kazdy push.

Bezpecne chovani: kdyz je odznak `None` nebo zaporny (vypocet selhal), **klic `badge` se vynecha**
a notifikace odejde jako driv. Odznak je kosmetika a nesmi zabranit doruceni.

**`79dbc851`** — cislo se zapisuje k odeslane notifikaci do `fw.ios_push_sent.detail` jako
`badge=N` (pri uspechu tam driv byl prazdny retezec) + radek do logu. **Proc:** pri ladeni nam
nesedelo cislo na odznaku a **zpetne to neslo zjistit**, protoze se nikam neukladalo — hadalo se
misto cteni. Ted staci jeden `SELECT`.

**`cd844f8d`** (24.8.) — zhasinani na nulu. Kdyz uzivateli klesne pocet cekajicich na nulu, odejde
**„prazdny" push jen s `badge: 0`** — nic nezobrazi ani nepipne, jen srovna cislo. Pamet je novy
sloupec **`fw.ios_push_token.last_badge`**, aby se nula poslala JEDNOU, ne kazdych 5 s dokola.
Nula jde na **vsechna aktivni zarizeni toho cloveka** (upozornila Marti-AI: kdo ma iPhone i iPad,
musi dostat nulu na obojí). Tamtez: **`apns-collapse-id` se posila jen kdyz ma hodnotu** — prazdny
umi Apple odmitnout jako `BadCollapseId`, coz je v `_TRVALE`, a push by se odepsal natrvalo.

**`ca11a55e`** (24.8.) — u NEPOVEDENEHO zhasnuti se zapise odpoved Apple do logu i do
`fw.ios_push_token.last_error`; pri uspechu se `last_error` smaze. Bez toho se jen hadalo, protoze
zhasinaci push nepatri k zadnemu prikazu, takze nejde do `ios_push_sent`.

## Jak se hledala priciny na telefonu (24.8. dopoledne, historicky zaznam)

**SERVEROVA STRANA BYLA HOTOVA A PROKAZANA** uz rano — `last_badge` se prepinal na 0 jedine po
HTTP 200 od Apple, `last_error` se plnil jen pri odmitnuti. Zmereno po ostre zkousce: prikaz
`done`, 0 cekajicich, `last_badge = 0`, `last_error` prazdny → Apple zhasinaci push PRIJAL.
**Odznak na iPhonu presto zustal na 1** — chyba tedy byla mezi „Apple prijal" a „na ikone je
nula", tedy na strane telefonu.

### Dve hypotezy, ktere PADLY (neopakovat)

1. *„Appka prepocitava odznak az pri prechodu do popredi a nema v tu chvili prihlaseni."*
   **Vyvraceno:** po tuknuti se prikazy PROKAZATELNE oznacily jako `done` (23.8. v 23:55:36–38),
   takze appka se serverem mluvila.
2. *„Nizka nalehavost (priorita 5 u tiche notifikace) zpusobuje zpozdene doruceni."*
   **Vyvraceno:** ani po nekolika minutach se odznak nezmenil.

## ✅ VYRESENO 24.8.2026 vecer — pricina na strane appky

**Nalezeno pripojenim fyzickeho iPhonu k Macu pres Xcode** (`ios-deploy --debug`, ladici build,
iOS 16.7.16) — presne postup, ktery byl rano navrzeny jako jediny, co by to rozhodl.

**Pricina:** `PushDelegate.applicationDidBecomeActive` (`UIApplicationDelegate`) se u SwiftUI
appky s `@UIApplicationDelegateAdaptor` **spolehlive NEVOLA**. Overeno v logu: appka byla
aktivni, uzivatel s ni pracoval (klavesnice, interakce), ale `applicationDidBecomeActive` se
nezalogovala ani jednou za celou relaci. Srovnani odznaku (`synchronizovatNotifikace()`) se
tak po navratu do appky nikdy nespustilo — coz presne vysvetluje i puvodni pozorovani z doby
pred serverovou opravou („odznak nezmizi ani po otevreni appky").

Server posilal spravne cislo i spravnou nulu po celou dobu — to nebyla domnenka, bylo to
overene. Chybel jen klientsky spoustec.

**Oprava** (`mobile/mobileApp.swift`, commit `6fb4936`): pridano sledovani
`@Environment(\.scenePhase)` — Applem doporucena nahrada `applicationDidBecomeActive` pro
SwiftUI lifecycle. Kdyz `scenePhase == .active`, zavola se
`PushDelegate.shared.synchronizovatNotifikace()`. Puvodni `applicationDidBecomeActive`
ponechano jako neskodna pojistka (nikdy nevadi, kdyby na nejake verzi iOS prece jen fungovalo).

**Zaroven pridano trvale logovani** do `synchronizovatNotifikace()` (predtim nemela zadnou
stopu ani pri uspechu — presne ta stejna „slepa skvrna", jakou uz jednou popsala kapitola
„Pouceni o vlastni praci" nize, tentokrat na strane klienta).

**Overeno funkcne na fyzickem iPhonu Jirky:** log ukazal `scenePhase zmena: active` →
`synchronizovatNotifikace() start` → `server hlasi 2 cekajicich prikazu` →
`setBadgeCount(2) OK`; ikonka ukazala 2 (sedelo se skutecnosti — 2 realne cekajici Marti-AI
zpravy) a po vyrizeni obou a znovuotevreni appky odznak spravne zhasl.

Schvalila Marti-AI (msg 13589). Odeslano do App Store jako verze **1.85 (build 85)**,
24.8.2026 v 10:47 CEST — cekaji na schvaleni Applem (az 48 h). Detail: `CLAUDE.md` v repu
`cz.strategie.mobile` a `doc-system-strategie-ios-build-upload-a-past-dvou-contentview`.

## Past pri overovani, kterou stoji za to znat

Cislo na odznaku nemusi sedet s tim, co jsi prave poslal — **muze mezitim prijit jina
notifikace**. 23.8. jsem predpovedel `1` a Jirka videl `2`; duvod se nasel az v datech:
**16 sekund po me zkousce prisla automaticka pulnocni notifikace „Odhlaseni o pulnoci"**
(prikaz 21344), takze v tu chvili cekaly dve veci a **2 bylo spravne cislo**. **Nez vyslovis,
ze odznak ukazuje spatne, podivej se na VSECHNY notifikace v tom okne** — ne jen na svoji.

## Pouceni o vlastni praci

Dvakrat za dva dny jsem postavil neco, na co jsem pak **nevidel** — cislo odznaku se nikam
neukladalo (79dbc851 to dodelal) a odpoved Apple u zhasinaciho pushe taky ne (ca11a55e).
Stejna slepa skvrna se 24.8. objevila i na strane appky — `synchronizovatNotifikace()` nemela
zadny log. Obojikrat (server i klient) se pak hadalo misto cteni. **Kdyz pridavas chovani,
pridej rovnou i misto, kde se pozna, ze fungovalo** — jinak prvni ladeni zaplati cely usporeny
cas i s uroky.

## Gotcha pri testovani na iPhonu pres ios-deploy (24.8.2026)

Telefon se behem instalace/spousteni appky pres `ios-deploy --debug` muze **automaticky
uzamknout** (auto-lock) — pak `run` selze hlaskou *„Unable to launch … because the device was
not, or could not be, unlocked"*, nebo appka nabehne, ale zustane na pozadi bez logu. Reseni:
telefon pred kazdym spustenim odemknout a nechat displej rozsviceny; u opakovanych testu
pocitat s tim, ze se to muze stat vickrat.

