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
  bez rucniho spusteni appka nabehne, smycka se nespusti a jen si to zaloguje.
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

