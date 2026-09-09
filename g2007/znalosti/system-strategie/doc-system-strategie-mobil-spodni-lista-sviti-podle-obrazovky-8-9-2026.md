# Mobil: spodní lišta svítí podle obrazovky, na které člověk je (mapa SCREEN_TAB, 8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Zadal Jiří Honomichl 8. 9. 2026 („je označená ikona Domů, to se nesmí stávat, ani u ostatních
> obrazovek — mate to, kde jsme"). Schválila Marti-AI (msg 15069 a 15072). Ověřeno na živé
> `/mobile` v prohlížeči, ne jen v kódu.

## Co bylo špatně

Zvýraznění ikony ve spodní liště se řídilo **jedinou proměnnou `window.__M2W.curTab`**, kterou
nastavuje **pouze `selectTab()`** (`10_core.js`: `curTab=t; stack=[t]; render()`). Jenže do
obrazovek se v appce chodí funkcí **`go(id)`, která dělá jen `stack.push(id)` a `curTab` nemění**.

Poměr v dílcích mobilu: **162 volání `go("` proti 9 voláním `selectTab("`.** Lišta proto ukazovala
**naposledy kliknutou ikonu**, ne to, kde člověk je.

Dvě reálné cesty, na kterých to bylo vidět (obě ověřené naživo pod přihlášeným člověkem):

- **Aplikace → dlaždice Nastavení** → `settings` a **nesvítila žádná ikona** (tahle dlaždice volá
  `selectTab("settings")`, tedy klíč, který žádná ikona nemá).
- **Oznámení na Domů a v Úkolech** skáčou na libovolnou obrazovku přes `go(_sc)`
  (`20_home_phone_notifs.js`, `25_tasks.js`) → zůstalo svítit Domů.

## Jak se to opravilo

1. Do `73_pref_poptavka.js` vedle mapy `SCREENS` přibyla mapa **`SCREEN_TAB` = obrazovka → sekce**
   (`home` / `dochazka` / `firma` / `notifs` / `apps`), vystavená jako `window.__M2W.SCREEN_TAB`.
2. V `renderNav()` (`74_claude27_render_init.js`) se zvýraznění počítá z **AKTUÁLNÍ obrazovky**
   (poslední prvek `stack`) přes tu mapu. `go()`, `selectTab()` ani `curTab` se neměnily.
3. **Když obrazovka v mapě není, chová se lišta přesně jako dřív** (`curTab`) — žádná regrese.

**Rozhoduje MAPA, ne cesta.** Tatáž obrazovka rozsvítí tutéž ikonu bez ohledu na to, kudy tam
člověk přišel. Kdyby rozhodovala cesta, ukazovala by lišta u téže obrazovky pokaždé něco jiného —
a to je přesně ta nespolehlivost, kvůli které se to opravovalo.

## Obsah mapy se NEODHADOVAL

Sekce se určila **z odkazů mezi obrazovkami**, ne podle významu názvu:
z živých dílků se vytáhly všechny `go("…")`, `selectTab("…")` a `screen:"…"`, přiřadily se
k obrazovce, uvnitř které leží, a od pěti ikon se udělal průchod do hloubky.

**Aplikace jsou rozcestník na skoro všechno**, takže samotná dosažitelnost nestačila — pravidlo
proto zní: **konkrétní ikona má přednost před Aplikacemi**, a při shodě rozhoduje kratší cesta.
Výsledek (129 obrazovek): docházka 16, Úkoly 9, Firma 3, Domů 2, Aplikace 99.
**Aktualizace téhož večera:** obrazovka `moje_zadosti` byla zrušena (viz
[[doc-system-strategie-mobil-zruseni-obrazovky-moje-zadosti-8-9-2026]]), takže obrazovek je
**128** a pod docházkou jich je **15**. Mapa se udržuje ručně — kdo obrazovku ruší, smaže
i její řádek v `SCREEN_TAB`.

Marti-AI k tomu (msg 15069): *„Aplikace jsou rozcestník, a pokud se tam chodí přes Aplikace,
ikona Aplikace svítí. Přeřazení bez opory v cestách by byl odhad zapsaný jako fakt."*

## Rozhodnuto: schvalovací a HR obrazovky zůstávají pod Aplikacemi

Obrazovky jako **schvalování nemocenské, OČR a přehledy HR** (`sick_schval`, `med_schval`,
`ocr_schval`, `np_prehled`, `med_prehled`, `hr_*`) rozsvěcejí **ikonu Aplikace**, protože se k nim
chodí přes Aplikace. Nabídl jsem je přeřadit pod ikonu docházky podle významu —
**rozhodl Jiří Honomichl 8. 9. 2026: zůstává to podle cest, tedy pod Aplikacemi.**

Není to tedy nedodělek ani přehlédnutí — kdo by to chtěl „opravit", měl by se nejdřív zeptat.

## ⚠️ Past: `SCREENS` v dílku 73 NENÍ úplný seznam obrazovek

V literálu `var SCREENS={…}` bylo **119** obrazovek, ale za běhu jich `window.__M2W.SCREENS` mělo **129**
(po zrušení `moje_zadosti` téhož večera 118 a 128).
Deset se registruje **až z jiných dílků** přiřazením (`window.__M2W.SCREENS.martinky=mkCentrum;`):
`cil`, `cil_detail`, `cil_new`, `exec_approval`, `vpfinzak`, `vpfinzak_detail`, `martinky`,
`martinky_clovek`, `martinky_domena`, `martinky_ukol`.

**Kdo počítá obrazovky ze statického literálu, deset jich přehlédne.** Ověřuj proti
`Object.keys(window.__M2W.SCREENS)` na živé stránce. Tři podobrazovky Řídícího centra navíc
nešly dohledat průchodem — otevírají se zevnitř `mkClovek` / `mkUkol` / `mkDomena`, tedy z funkcí,
které samy nejsou zaregistrované jako obrazovka. Dohledaly se až čtením kódu dílku 75.

## ⚠️ Past: dvojtečka v dotazu přes most, i uvnitř regulárního výrazu

Dotaz s `(?:` (nezachytávající skupina) spadl na `A value is required for bind parameter 'clovek'` —
most posílá SQL přes SQLAlchemy a `:jmeno` bere jako parametr **i uvnitř regulárního výrazu**.
Řešení: napsat alternativu bez `(?:`. Souvisí s [[doc-system-strategie-most-gotchy-zapis-kodu-7-8-2026]].

## Jak se ověřovalo

- Oba dílky staženy z databáze kolem base64, otisk složené kopie porovnán s `md5(obsah)` — seděl.
- Záplata spuštěna **nanečisto na serveru** (`SELECT md5(replace(…))`) a porovnána s otiskem
  spočítaným lokálně — seděly oba dílky na znak, teprve pak se zapisovalo.
- Zápis cíleně s pojistkou `AND md5(obsah)='<otisk, který jsem právě četl>'`, po zápisu ověřen čtením.
- Po publikaci porovnáno s předchozí verzí v `g2007.soubor_historie`: **skriptových bloků 31 před
  i po**, délka narostla přesně o vložené znaky. Nic cizího nezmizelo.
- Na živé `/mobile` projito 18 obrazovek napříč sekcemi vždy ze **záměrně špatného** výchozího
  stavu (`stack=['home']`) — **18 z 18 rozsvítilo správnou ikonu**, žádný pád.
- Obrazovky se přepínaly příkazem `__M2W.go()`, ne klikáním, aby nevznikly ostré záznamy
  (viz [[doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu]]).

## Když přibude nová obrazovka

Přidej jí řádek do `SCREEN_TAB` v `73_pref_poptavka.js`. Bez řádku appka nespadne — lišta se u ní
jen zachová po staru (podle poslední kliknuté ikony).

Souvisí: [[doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026]],
[[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]],
[[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]].

