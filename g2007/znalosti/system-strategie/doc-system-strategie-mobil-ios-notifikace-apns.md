# iOS notifikace (APNs): jak jsou udelane, co iOS z Androidu prevzit UMI a gotchy

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc (19. 8. 2026, Jirka + Claude)

Android ma foregroundovou sluzbu `DialPollService`, ktera se a 4-20 s pta
`/app/{app_key}/commands/pending` a na kazdy novy prikaz vyrobi notifikaci. **iOS trvaly
polling na pozadi nedovoli** - ekvivalent te sluzby na iPhonu existovat nemuze. Jedina cesta,
jak dostat prikaz z `fw.mobile_command` do notifikacni listy zavrene appky, je push z APNs.

## DULEZITE - upresnuje znalost `...ios-companion-bez-js-mostu-a-kopie-mimo-xcode-target`

Tam stoji "kdyz zmena stoji na JS mostu, do iOS nepatri". Plati, ale **neplati obracene**:
skok na obrazovku z notifikace Android nedela pres most `window.STRATEGIE`, nybrz volanim
`window.__M2W.go('<screen>')` (`HybridActivity.goScreen`, commit `4b40fd2e`). `__M2W` je
funkce **samotneho webu**, takze ji WKWebView zavola `evaluateJavaScript` uplne stejne.
**Rozhodujici otazka tedy neni "je to z Androidu?", ale "stoji to na JS mostu, nebo na webu?"**

## Jak je to udelane

- **Klient** `APP/iOS/mobile/PushNotifications.swift` (271 radku): povoleni az po nacteni webu,
  token -> `POST /api/v1/erp/app/ios/push/register` s identitou z cookie ve `WKHTTPCookieStore`
  (iOS nema JS most ani vlastni token a nepotrebuje je), zobrazeni i v popredi (`willPresent`),
  tuknuti -> `window.__M2W.go()`, u `open_url` nacteni adresy ve WebView.
- **Server** `modules/erp/api/ios_push.py`: tabulky `fw.ios_push_token` a `fw.ios_push_sent`,
  odesilaci smycka a 5 s **jen na primaru** (na sekundaru by uzivatel dostal kazdou notifikaci
  dvakrat), endpointy `/app/ios/push/{register,unregister,status,test,key}`.
- **Chovani je zamerne stejne jako Android** `notifyCommand`: cinkne KAZDY pending prikaz bez
  filtru podle `command_type`, kazdy jen jednou (Android drzi `shownCommandIds` v pameti sluzby,
  server ekvivalentne tabulku `ios_push_sent`), `claude_ok` tise (Android kanal `CH_OK`
  IMPORTANCE_LOW = APNs `interruption-level: passive` + priorita 5), payload nese `screen`
  a `label`, `url` jen u `open_url`.
- Zruseni notifikace u vyrizeneho prikazu (Android `cancelCommandNotif`) dela iOS klient sam
  pri navratu do popredi - server na to nepotrebuje silent push, ten APNs agresivne skrti.

## Gotchy

- **APNs prijima notifikace VYHRADNE pres HTTP/2** -> `httpx` potrebuje balik `h2`, ktery se sam
  netahne; provider token je JWT ES256 -> `pyjwt[crypto]`. Obe pridany do `pyproject.toml`,
  ale **`scripts/deploy_current.ps1` dela jen `git pull` + restart, `poetry install` NE** ->
  bez rucniho spusteni appka nabehne, ale notifikace se NEODESLOU. (Od 24.8.2026 smycka bezi porad a zkousi to dal - jen jí odesilani pada na chybejici knihovne; driv se vubec nespustila. Prakticka rada je stejna: poetry install je potreba.)
- **Prechodne chyby** (429, 5xx, vypadek site, `ExpiredProviderToken`) se ZAMERNE nezapisuji do
  `ios_push_sent` - jinak by notifikace po jednom zaskobrtnuti nedorazila uz nikdy. Trvale
  (410 `Unregistered`, `BadDeviceToken`) prikaz odepisou a mrtvy token vypnou.
- **Prostredi (sandbox/produkce) se z tokenu poznat neda** -> zkousi se obe, vysledek se u tokenu
  pamatuje jen jako poradi pro priste (telefon prejde z TestFlightu na App Store build).
- Pro **simulator** Xcode `aps-environment` zamerne odstranuje -> tam se appka u APNs nikdy
  nezaregistruje; neni to chyba konfigurace.
- Klic `.p8` vyda Apple JEN JEDNOU a je Team Scoped (plati pro cely tym). **Do repa nesmi** -
  sdilene repo je verejne. Patri do `fw.app_secret`, odkud ho cte `_z_trezoru`; nahrat jde pres
  `POST /app/ios/push/key` (jen rodice a IT), protoze z firemni site na PostgreSQL cesta nevede.

## Overeno 19. 8. 2026

Klic overen proti skutecnemu APNs (push na zamerne vadny token vratil z produkce i sandboxu
`BadDeviceToken`, tedy Apple podpis PRIJAL). Notifikace vyzkousena na fyzickem iPhonu - dorazila
a tuknuti otevrelo appku. Testy `tests/test_ios_push.py` 6/6. Verze 1.84 (build 84) odeslana
ke schvaleni Applem.
## OSTRE NASAZENI 23. 8. 2026 - co je hotove a kde to viselo

**Serverova cast je od 23. 8. 2026 na produkci** (commit `c3bddc90`, 19:10 UTC). Na GitHubu se
sloucit nedala (ucet nema pravo zapisu), obsah PR #5 vlozil primy commit do `main`; overeno, ze
vsech 14 souboru ma shodny blob SHA s hlavickou PR `f97b00dd`. PR #5 byl 19:42 UTC **zavren**
s vysvetlenim.

**Klic je v trezoru** (21:45): `fw.app_secret` -> `apns_key_p8` (257 znaku), `apns_key_id`
= `2YZ86LSQ25`, `apns_enabled` = `1`. Nahran pres `POST /app/ios/push/key`.

**Notifikace ostre overena na fyzickem iPhonu 23. 8. ve 22:04** - `POST /app/ios/push/test`
vratil `{"ok":true,"odeslano":1,"chyb":0}`, ve `fw.ios_push_sent` je radek `command_id` 21328,
`ok = true`, token konci `eed85538`, appka 1.84, prostredi `production`. Jirka notifikaci videl.

### Tri veci, ktere nasazeni zdrzely - vsechny stoji za zapamatovani

**1. Chybejici knihovna `h2`.** Prvni ostry test vratil
`Using http2=True, but the 'h2' package is not installed`. Neslo o chybu kodu ani klice -
`deploy_current.ps1` dela jen `git pull` + restart, **`poetry install` NE**, a PR pridava `h2`
a `pyjwt[crypto]`. Doresil commit `16cbf64c` (Marti-AI). **Po kazdem nasazeni, ktere pridava
zavislost, je nutny `poetry lock` + `poetry install` rucne.**

**2. Vlastnictvi tabulek.** `ensure_tables()` dela `CREATE INDEX IF NOT EXISTS` pri KAZDEM
pozadavku a tabulku `fw.ios_push_token` vlastnila role `Marti-AI` -> `must be owner of table`,
`/status` vracel HTTP 500 a ve 21:17 padala i skutecna registrace iPhonu. **Doplnit chybejici
index NESTACILO**, PostgreSQL kontroluje vlastnictvi driv nez `IF NOT EXISTS`. Vyreseno prevodem
vlastnika obou tabulek i sekvence na roli `fw_owners`. Detail a obecne pravidlo:
`doc-system-strategie-ddl-za-behu-vyzaduje-vlastnictvi-tabulky`.

**3. Odesilaci smycka - dnes vyresene restartem, ale pricina v kode trva.**
`ios_push_sched_start()` se pta na konfiguraci **jen jednou, pri startu**. API nastartovalo
21:10:12, klic prisel az 21:45 -> smycka zalogovala "vypnuto" a **uz se nikdy nezeptala**.
Rucni `/test` fungoval (cte konfiguraci pri kazdem volani), automaticke odesilani ne.
Dva restarty pres most (22:09, 22:52) vratily `rc: 0`, ale PID pythonu se nezmenil - viz
`doc-system-strategie-restart-api-pres-most-hlasi-uspech-ale-nerestartuje`.
**Vyresil to az deploy commitu `3d3faa67` ve 23:00**, ktery API skutecne restartoval - v tu dobu
uz klic v trezoru byl, takze smycka nabehla spravne.

**✅ OVERENO FUNKCNE 23. 8. ve 23:31:** do `fw.mobile_command` zalozen prikaz 21336 a **nikdo
nevolal `/test`**; smycka ho sama odeslala **za 4,6 sekundy** (`fw.ios_push_sent`, `ok = true`).
`/status` na primaru hlasi `smycka_bezi: true`, na sekundaru `false` - presne jak ma byt.
⚠️ **Cteni `/status` je proto zavisle na tom, ktera instance odpovi** - load balancer mezi nimi
prepina i behem nekolika vterin. Jeden dotaz nic nedokazuje; bud se ptat vickrat a sledovat `dir`
z `/api/v1/api-info`, nebo overovat funkcne (zalozit prikaz a merit, za jak dlouho odejde).

### Pripravena oprava (schvalila Marti-AI msg 13510, zadal Jirka)

Meni jen `modules/erp/api/ios_push.py`: smycka se spusti VZDY a v cekacim rezimu si a 60 s overi
konfiguraci (misto tiseho konce) · `/app/ios/push/key` ji po ulozeni klice nastartuje bez restartu ·
`/status` nove vraci pole `duvod`, proc smycka nebezi · guard na sekundar primo v modulu.
**✅ NASAZENO 24. 8. 2026 commitem `cd844f8d`** (zadal Jirka, schvalila Marti-AI msg 13555).
Podklad `OPRAVA_ios_push_smycka.md` uz mezitim neexistoval (byl jen na plose Macu), takze
oprava byla napsana znovu podle tohoto popisu. Tamtez pribylo zhasinani odznaku na nulu
a `/status` vraci i `zalozni_server`. Detail:
`doc-system-strategie-ios-notifikace-smycka-cekaci-rezim`.

### Past pri testovani, na kterou se da naletet

**Testovaci prikaz ve `fw.mobile_command` si vyzvedne i Android** pollingem a oznaci ho `done`.
Smycka pritom vybira jen `status = 'pending'`, takze **starsi prikaz neni dukazem niceho** -
vypada to, jako by smycka nefungovala. Vzdy zakladat cerstvy prikaz a merit hned; a pocitat s tim,
ze push cinkne i na Androidu.

