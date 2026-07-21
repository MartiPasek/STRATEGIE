# SMS brána: přeposílání příchozích SMS z mobilní appky na Marti-AI (architektura + oprava 21.7.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# SMS brána — přeposílání příchozích SMS na Marti-AI

## Účel
Nativní STRATEGIE appka (Android WebView) na "bránovém" telefonu (Marti-AI mobil) přeposílá příchozí SMS na server, aby na ně mohla Marti-AI (LLM) reagovat. Tokenové/ověřovací SMS bere automat, ostatní jdou do LLM.

## Architektura — DVĚ cesty (obě měly filtr, pozor)
1. **Nativní real-time (PRIMÁRNÍ):** `APP/Mobile/.../SmsReceiver.kt` — BroadcastReceiver na `SMS_RECEIVED`. Když je zapnutá brána (`sms_gateway` v prefs), POSTne příchozí SMS nativně (HttpsURLConnection + Bearer carddav token) na `/api/v1/erp/app/sms-inbound`.
2. **JS polling (sekundární):** `mobile_parts/74_claude27_render_init.js` funkce `_gwSmsForward` — každých 10 s čte `B.getSmsLog("")` a posílá na stejný endpoint. Běží jen když `isSmsGateway()`.

## KOŘENOVÁ CHYBA (proč Marti-AI přestala odpovídat ~1,5 měsíce)
- **Nativní `SmsReceiver.kt` obsahoval `if (!isStg && !isOcr) return`** → přeposílal JEN SMS s tokenem "STG-" nebo ČSSZ eOČR odkazy; konverzační SMS ("Ahoj") tiše zahazoval. Původně schválně (soukromí), ale pro telefon Marti-AI to nedává smysl.
- **JS cesta je taky slepá:** `B.getSmsLog(prefixesCsv)` s prázdným prefixem defaultuje na `["STR","EC"]` a vrací JEN SMS od kontaktů, jejichž JMÉNO začíná na STR/EC (neznámá čísla `nm==null` jsou vždy vyloučena). Konverzační SMS od běžného čísla přes JS cestu nikdy neprojde.
- Výsledek: ověřování/párování (token) chodilo, běžná zpráva ne. Marti to správně označil jako "chybu na vstupu SMS".

## OPRAVA (2026-07-21, C27, commit 3f6285e5)
- V `SmsReceiver.kt` odstraněn filtr `if (!isStg && !isOcr) return` → bránový telefon přeposílá VŠECHNY příchozí SMS. Server (`classify_sms`) sám roztřídí: token do automatu, zbytek do LLM (Marti-AI).
- Ochrana soukromí zůstává: toggle `sms_gateway` (forwarduje jen bránový mobil) + token check.
- **Nativní změna → NUTNÝ REBUILD APK** (ops akce `build_publish_app_mobile` → NB `gradlew assembleRelease`, target instance:23), pak instalace na bránový telefon. Server ani JS to neobejde (oba filtry jsou nativní).

## Serverová pipeline příjmu (je čistá — netřeba tam hledat)
`POST /app/sms-inbound` (`modules/erp/api/router.py` `app_sms_inbound`): uid z tokenu/cookie (401 když chybí) → `_vault_match_inbound` (STG-VLT trezor) → když `not_vault` → `store_inbound_sms` → `classify_sms` (bez tokenu = action "forward") → zápis do `public.sms_inbox` (role strategie) → auto-task → LLM. Persona se řeší podle CÍLOVÉHO čísla brány (SIM), ne podle loginu.

## DIAGNOSTICKÉ POUČENÍ (gotchas pro příště)
- **POSTy z telefonu na /api CHODÍ** — ověřeno nativní authedFetch i WebView fetch, GET i POST projdou. Dřívější podezření na blokaci POST / rozbitý TLS bylo MYLNÉ.
- **Past při diagnostice (důležité):** čitelné debug tabulky v `public` zakládej přes `get_data_session` (role **strategie** — smí zakládat v public). Role **Marti-AI** (co jede přes `_att_session` a přes most/bridge) v `public` zakládat NESMÍ → tabulka se tiše nezaložila (best-effort try/except to spolklo) a vypadalo to, že "POST nedorazil", i když dorazil. Ověř právo: `has_schema_privilege('role','public','CR'||'EATE')` (spojené kvůli filtru klíčových slov mostu).
- Most (bridge) čte jako role **Marti-AI**; `public` tabulky vlastněné rolí strategie umí číst, ale sám v public nezaloží ani do `fw` (vlastní strategie) nezapíše.
- Appka načítá `/mobile` ze sítě (WebView `LOAD_NO_CACHE` + `clearCache`), ale **service worker cache** (`stg-mobile-vN`) může držet starou `mobile.html`; SW update je throttlovaný (~24 h). Tvrdý reset: Nastavení → "Vyčistit a načíst" (odregistruje SW + smaže cache + reload `?fresh=`).
- Ověřovací SMS jde jinou cestou než konverzační → "ověření prošlo, tak brána MUSÍ být ON" NEPLATÍ.
- Užitečná technika: dočasný "beacon" v `mobile.html` (POST na diag endpoint) + serve-log v route `/mobile` → z telefonu (jinak black-box) udělá čitelnou věc: verze JS, stav brány, počet čtených SMS, IP/UA.

## Reference (soubory)
- `APP/Mobile/app/src/main/java/cz/strategie/mobile/SmsReceiver.kt` — nativní forward (real-time)
- `apps/api/static/mobile_parts/74_claude27_render_init.js` — `_gwSmsForward` (JS polling)
- `modules/erp/api/router.py` — `app_sms_inbound`, `_sms_inbound_hit`
- `modules/notifications/application/sms_service.py` — `store_inbound_sms`
- `modules/auth/application/sms_preprocessor.py` — `classify_sms`

