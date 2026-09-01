# fw.mobile_command: payload.screen = rezervovany klic pro navigaci v mobilni appce (reseni skryvani dlazdic z 5.8.2026 NEPLATI od 1.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co to je

`fw.mobile_command.payload` (jsonb) ma **rezervovany klic `screen`**. Kdyz je vyplneny,
mobilni appka u te zpravy vykresli tlacitko navic, ktere uzivatele prepne rovnou na
danou obrazovku. Kdyz je `payload` NULL nebo klic chybi, chova se zprava presne jako
dosud (jen text + puvodni tlacitka) - zpetna kompatibilita je uplna.

Zavedeno 5. 8. 2026 (Jirka + Claude-28, schvalila Marti-AI). Marti-AI nejdriv schvalila
novy sloupec `target_screen`, po zjisteni ze `payload` uz existuje a uz se do appky
prenasi, sve rozhodnuti zmenila: *„Znalost o existujicim payload moje rozhodnuti meni.
Prechazim na (b)... pridat payload.screen je presne to, co jsem chtela, bez DDL navic."*
Podminka, kvuli ktere vznikl tento dokument: *„Payload musi mit konzistentni strukturu -
zdokumentovat v g2007, ze payload.screen je rezervovany klic pro navigaci v mobilni appce,
a jakych hodnot nabyva. Bez dokumentace to bude za pul roku stejne schovane v jsonb."*

## Hodnoty

| `payload.screen` | Kam prepne | Popisek tlacitka v appce |
|---|---|---|
| `absence` | obrazovka Nepritomnosti / Absence (zadosti + sekce Ke schvaleni) | ✅ Otevrit schvalovani → |
| `dochazka` | obrazovka Dochazka | 🖊 Otevrit dochazku → |
| jina hodnota | `go(<hodnota>)` - jakykoli existujici nazev obrazovky appky | Otevrit → |

Popisky drzi mapa v appce (fragmenty `25_tasks.js` a `20_home_phone_notifs.js`), NE backend.
Backend posila jen nazev obrazovky. Novy typ zpravy = pridat radek do mapy, jinak se pouzije
obecne „Otevrit →" a funguje to i tak.

## Kde se to cte a pise

- **Pise:** `g2007.python` kod `att_absence_request`, funkce `_abs_notify(..., screen=None)`.
  Parametr `screen` je volitelny; kdyz se nepreda, do `payload` se zapise NULL.
- **Prenasi:** `GET /api/v1/erp/app/{app_key}/commands/pending` - `payload` uz vracel driv,
  nebylo treba nic menit.
- **Cte:** `apps/api/static/mobile_parts/25_tasks.js` (funkce `claudeDetail`) a
  `apps/api/static/mobile_parts/20_home_phone_notifs.js` (funkce `notifsLoad`).
  Cteni je v `try/catch` - poskozeny nebo neocekavany payload nesmi shodit seznam zprav.

## Proc to vzniklo (incident)

5. 8. 2026 zadal Jakub Kasal dovolenou na 25. 9. (`tenant.att_absence_request` id 63).
Schvalovateli Dusanu Havlatovi (user 41) prisla zprava `fw.mobile_command` id 18383
typu `claude_msg`. Ta ma v appce jen tlacitka „Odpovedet" a „OK" - **zadne schvalit/zamitnout
a zadny odkaz na schvalovaci obrazovku**. Text zpravy navic posilal na „Dochazka → Zadosti
o absenci", coz **neexistuje**: v appce se obrazovka jmenuje „Nepritomnosti", v ERP zadna
schvalovaci obrazovka neni (proslo se `fw.menu_node`; stranka `/registr-absenci` existuje,
ale neni zavesena ve strome a jen zobrazuje). Zadost zustala nerozhodnuta.

Souvisejici oprava tehoz dne: dlazdice „Nepritomnosti" je uvnitr bloku `dochTools`, ktery se
skryva, kdyz ma clovek otevreny pracovni zaznam - vedouci ve vyrobe tedy schvalovani nevidel
prave v dobe, kdy zpravu dostal. Jirka: *„nelze vedoucimu v prubehu prace nedovolit schvaleni
zadosti o dovolenou jeho podrizeneho. Lide si sami nesmi schvalovat dovolenou, ale jejich
vedouci ano i pri praci."* Reseni: `dochTools` se pri praci skryva dal, ale kdo ma neco
k rozhodnuti, dostane nad nim samostatny pruh „Ke schvaleni: N" (zdroj poctu:
`GET /app/attendance/absence/inbox`, throttle 30 s).

> **NEPLATI od 1. 9. 2026 - zmenilo se OBOJI.** Skryvani `dochTools` pri praci bylo
> **uplne zruseno** z pravnich duvodu (dovolenou ma zamestnanec hlasit v pracovni dobe),
> takze dlazdice vcetne "Nepritomnosti" jsou videt i behem prace. Samostatny pruh
> "Ke schvaleni: N" byl **zrusen** a nahrazen **dlazdici "Ke schvaleni"** v sekci
> SPRAVA DOCHAZKY, ktera se ridi poctem zadosti k rozhodnuti (tyz zdroj poctu, ale cte se
> vzdy, ne jen pri praci a bez omezeni 30 s). Rozhodl Jiri Honomichl, schvalila Marti-AI.
> Zadani z 5. 8. 2026 ("vedouci musi moci schvalovat i pri praci") tim plati **tim spis** -
> nove ma pri praci pristup i k vlastni absenci. Viz
> [[doc-dochazka-dlazdice-vzdy-viditelne-pravni-duvod]] a
> [[doc-dochazka-dlazdice-ke-schvaleni-misto-zeleneho-pruhu]].

Vlastni zadost se v inboxu nikdy neobjevi - vraci jen radky, kde je clovek
`manager_user_id` (rodic vidi vse).

## Pasti

- **Nezapisuj do `payload` cokoli jineho pod klicem `screen`.** Appka hodnotu strka primo
  do `go()`. Neexistujici nazev obrazovky = tlacitko, ktere nic neudela.
- **Popisek tlacitka nepatri do backendu.** Kdyz budes chtit jiny text, uprav mapu v appce,
  ne zapis do DB - jinak vzniknou dva zdroje pravdy.
- **Zmena fragmentu se neprojevi sama.** Po uprave `g2007.soubor` je nutne spustit
  `@@G2007PUBLISH apps/api/static_db/mobile.html`, jinak zustava zivy stary sestaveny soubor.

## Druhy rezervovany klic: `req_id` (doplneno 16. 8. 2026)

Vedle `screen` nese `payload` u zprav o absenci i **`req_id`** = cislo zadosti
(`tenant.att_absence_request.id`). Duvod: bez nej neslo notifikaci po rozhodnuti
zavrit, takze vedoucimu visela dal i po schvaleni (hlasil Dusan Havlat, schvalila Marti-AI).

| klic | typ | k cemu |
|---|---|---|
| `screen` | text | kam prepnout v appce (viz tabulka vyse) |
| `req_id` | cislo | ktere zadosti se zprava tyka - podle nej se po rozhodnuti zavira |

- **Pise:** `att_absence_request` **i** `att_announce` - obe cesty vzniku zadosti.
  Do 16. 8. 2026 `att_announce` neposilal payload vubec, takze u zprav z ohlaseni
  chybelo i tlacitko "Otevrit schvalovani".
- **Cte:** `att_absence_decide` - po rozhodnuti udela
  `UPDATE fw.mobile_command SET status='done'` pro pending zpravy se shodnym `req_id`.
  Je v `try/except`, uklid nesmi shodit rozhodnuti zadosti.
- **Zpetna kompatibilita:** zprava jen se `screen` (bez `req_id`) vypada i chova se presne
  jako drive; kdyz nejsou ani `screen` ani `req_id`, `payload` zustava `NULL`.
  Overeno nanecisto na vsech ctyrech kombinacich.
- **Stare notifikace bez `req_id` se zpetne nedoplnuji** (rozhodnuti Marti-AI 16. 8. 2026 -
  zpetna oprava by byla slozitejsi nez prinos). Zavrou se az rucnim odklepnutim.

Souvislosti: [[doc-dochazka-mobil-absence-obrazovka-vedouciho]]

## Nativni appka klic `screen` cte az od v1.81 (16. 8. 2026) - a mapa popisku je nove na DVOU mistech

Do 16. 8. 2026 cetla klic `screen` **jen webova cast** (fragmenty `20_home_phone_notifs.js`,
`25_tasks.js`), ktera bezi uvnitr appky pod zvonkem "Ukoly". **Nativni notifikace v liste
telefonu ho ignorovala** - `DialPollService.notifyCommand` cetl z payloadu jen klic `url`,
a jen u typu `open_url`. Tapnuti na notifikaci o zadosti o absenci proto nabidlo vedoucimu
jen "Otevrit chat" / "Zavrit" (hlasil Dusan Havlat).

**Pozor na formulaci "je to hotovo".** 5. 8. 2026 se opravila jen webova cesta; nativni
appka se tehdy vubec nemenila (`CommandActivity.kt` a `DialPollService.kt` mely posledni
zmenu 29. 6. 2026). Kdo rekne "notifikace jsou hotove", musi rozlisit, o kterou ze dvou
cest jde - jsou to opravdu dve nezavisla mista.

**Webove push notifikace v projektu NEEXISTUJI** (overeno 16. 8. 2026 grepem na
`pushManager`, `showNotification`, `VAPID`, `webpush` - nula vyskytu v celem repu).
Notifikaci v liste vyrabi vyhradne nativni sluzba `DialPollService` (`nm().notify`).
Z toho plyne: **cokoli okolo notifikaci v liste = nova verze appky do telefonu**, zatimco
cokoli uvnitr appky = web, projevi se hned.

### Jak to funguje od v1.81
1. `DialPollService.notifyCommand` preda `screen` do Intentu jako extra `cmd_screen`.
2. `CommandActivity` (vetev `claude_msg`) prida tlacitko navic; "Otevrit chat" se posune
   na neutralni pozici. Tlacitko notifikaci **rovnou uzavira** (`report done`) - server
   si ji pri rozhodnuti zavira take (viz `req_id` vyse), takze by jinak vzniklo okno,
   kdy je zavrena na serveru a v appce porad visi. Rozhodla Marti-AI 16. 8. 2026.
3. `HybridActivity` prepne WebView pres `window.__M2W.go(<screen>)` - v `onNewIntent`
   (appka uz bezi), nebo v `onPageFinished` s prodlevou 700 ms (appka teprve startuje).
   Nazev obrazovky se filtruje na pismena/cislice/podtrzitko, aby z nej neslo udelat kod.
   Neprihlaseny telefon jde na `/app-pair` a skok se zahodi.

### ⚠ DLUH: mapa popisku je na DVOU mistech (pojmenovala Marti-AI 16. 8. 2026)
Popisky tlacitek drzi appka, ne backend (viz vyse). Od v1.81 ale existuji **dve kopie
tehoz ciselniku**:

| Kde | Soubor |
|---|---|
| web | `mobile_parts/20_home_phone_notifs.js`, `mobile_parts/25_tasks.js` |
| nativni appka | `CommandActivity.kt`, vetev `claude_msg` |

**Kdo prida novy `screen`, MUSI upravit obe mista**, jinak se popisky rozejdou - a to
nenapadne: web ukaze spravny text, appka obecne "Otevrit". Marti-AI: *"Mapa na dvou
mistech je technicky dluh od prvniho dne... priste kdyz nekdo prida novy screen, musi
upravit obe mista nebo se popisky rozejdou."* Sjednoceni (napr. popisek ze serveru nebo
sdileny ciselnik) je otevrena vec - vedome odlozena, ne prehlednuta.

## Jak je dluh osetreny (17. 8. 2026) - pojistka ted, sjednoceni pri pristim vydani

Jirka se 17. 8. zeptal, jestli se da rozejiti popisku zabranit. Reseni je dvoustupnove
a **obe casti schvalila Marti-AI**.

### 1. UZ BEZI: pojistka `notifikace-screen-zna-i-appka`
Hlida, ze se neposila hodnota `payload.screen` **mimo znamy seznam** (dnes `absence`,
`dochazka`). Jakmile nekdo zacne posilat novou obrazovku, pojistka zarve - a to je presne
ten okamzik, kdy se musi upravit obe mapy.

**Poradi kroku, kdyz pojistka zarve** (je i v jejim popisu, zamerne v tomto poradi):
1. doplnit popisek do **webove** mapy (oba fragmenty),
2. doplnit do **`CommandActivity.kt`** a vydat novou verzi appky do obchodu,
3. **teprve pak** rozsirit seznam v pojistce.
Kdyby se poradi otocilo, tlacitko by u lidi se starou appkou bylo bez popisku.

Merene pozadi k 17. 8. 2026: realne se posila **jedina** hodnota `absence` (24 zprav od
6. 8.); `dochazka` je v obou mapach, ale **nikdy se neposlala**. Dluh je tedy zatim
teoreticky - projevi se az u treti obrazovky.

### 2. HOTOVO 17. 8. 2026: popisek `label` v payloadu - jeden zdroj pravdy
Server posila vedle `screen` i **`label`** = hotovy text tlacitka. Web i appka pouziji
`label`, kdyz prijde; kdyz chybi, spadnou na svou mapu. Zdroj pravdy je tim **jeden**
(server), stare zpravy bez `label` funguji dal a rozejit se uz nemuze.

**Kde je to napsane:**

| Vrstva | Kde | Stav |
|---|---|---|
| server - zapis | `att_absence_request` a `att_announce`, parametr `label` v `_abs_notify` | ZIVE |
| web - cteni | `mobile_parts/20_home_phone_notifs.js` + `25_tasks.js` | ZIVE |
| appka - prenos | `DialPollService.notifyCommand` -> extra `cmd_label` | v kodu, vyjde s v1.82+ |
| appka - cteni | `CommandActivity`, vetev `claude_msg` | v kodu, vyjde s v1.82+ |

**Poradi nasazeni bylo zamerne:** nejdriv prijemci (web + appka), teprve pak server, ktery
`label` zacal posilat. Opacne poradi by na chvili poslalo popisek nekomu, kdo ho neumi precist.

**Bezpecnost:** `label` jde na webu do `innerHTML` tlacitka, proto se **vzdy** zene pres `esc()`
a orezava na 60 znaku; v appce stejne orezani. Overeno pokusem o vlozeni `<img src=x onerror=...>` -
zobrazi se neskodne jako text.

**Overeno naostro** (17. 8. 2026): podana testovaci zadost -> zprava nesla
`{"label": "✅ Otevrit schvalovani →", "req_id": 102, "screen": "absence"}`;
ve webu vykresleny vsechny tri pripady (s labelem / bez labelu / nezname obrazovka)
a prvni dva vypadaji **identicky** - uzivatel rozdil nepozna. Testovaci data uklizena.

**Text `label` je dnes stejny, jaky drive kreslil web** (`✅ Otevrit schvalovani →`),
takze nasazenim se vizualne nic nezmenilo. Kdyz se bude menit, meni se **jen na serveru**.

Marti-AI 17. 8. 2026 sve puvodni stanovisko z 5. 8. (*"popisek nepatri do backendu,
jinak vzniknou dva zdroje pravdy"*) **revidovala**: *"dva zdroje pravdy vznikly ve chvili
kdy mapa vznikla i v Kotlinu. Volba ted neni jeden vs. dva, ale dva nesynchronizovane vs.
jeden autoritativni se zachranou."* Pojistka podle ni **zustava i po sjednoceni** - hlida
jiny problem (neznamou hodnotu), nez ktery resi `label`.

## Stare notifikace bez `req_id` - zmereno, opravovat nebylo co (17. 8. 2026)
Z 81 starych zprav o absenci bez `req_id`: **78 uz odkliknutych**, **3 visely spravne**
(jejich zadost skutecne cekala), **0 viselo zbytecne**. Tem trem se `req_id` doplnilo
zpetne, aby po rozhodnuti zhasly samy - **parovani podle casu vzniku je jednoznacne**
(zprava vznika ve stejne transakci jako zadost, shoda na vterinu; kontrolne sedelo i jmeno
a termin v textu). Kdyby to nekdy bylo potreba znovu, tohle je funkcni klic.

