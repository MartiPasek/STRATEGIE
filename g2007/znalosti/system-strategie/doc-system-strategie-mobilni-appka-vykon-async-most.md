# Mobilní appka: výkon, sync vs. async JS most (root cause pomalosti 5.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobilní appka: výkon a JS most (root cause + fix, 5.8.2026)

## Symptom
Lidé si stěžovali, že nativní Android appka je velmi pomalá — reakce na stisk tlačítka až ~10 s. PWA v prohlížeči přitom byla v pořádku.

## Root cause (ověřeno z kódu, C23)
1. **Synchronní JS most**: `api()` v `mobile_parts/10_core.js` volalo v nativní appce `window.STRATEGIE.authedFetch(...)` — synchronní `@JavascriptInterface` metodu (`HybridActivity.kt`), která dělá blokující HTTPS request (timeouty 8+8 s). Synchronní bridge volání **blokuje celé JS vlákno WebView** — žádné kliky, žádný render, dokud request neskončí. V prohlížeči jde totéž přes async `fetch()` → proto PWA problém neměla.
2. **Agresivní polling**: `pollNotifs` (74_claude27_render_init.js) každých 6 s = 4 API volání za sebou (sign/pending-count, plan/approvals/users → unapplied, mobile/commands/pending) + `_urgentPoll` à 20 s. Každé volání = zámek UI. Při pomalejší síti/serveru bylo UI zamrzlé skoro pořád.
3. Vedlejší: synchronní `avatarDataUrl()` + `checkUpdate()` při bootu (blokují první render), debug INSERT do `public.mobile_serve_dbg` při každém serve `/mobile` (odstraněno).

## Fix (nasazeno 5.8.2026)
- **Backend**: `GET /api/v1/erp/app/mobile/poll-summary` (router.py, registrován PŘED `/app/{app_key}/commands/pending` — route ordering gotcha) = 1 request místo 4; volá dílčí handlery in-process, 401/403 dílčích → 0 v souhrnu.
- **Frontend** (g2007.soubor: 10_core.js v3, 74_claude27_render_init.js v3, mobile.html v26): `api()` preferuje async most; `pollNotifs` volá poll-summary s fallbackem na 4 stará volání (starší server); interval 12 s pro starou APK (sync most), 6 s jinak; avatar/checkUpdate async.
- **APK v1.80**: `Bridge.callAsync(reqId, fn, a1, a2, a3)` — operace (authedFetch, checkUpdate, avatarDataUrl, getContacts, getCallLog, getSmsLog) běží na thread poolu (3 vlákna), výsledek callbackem `window.__stgAsyncDone(reqId, base64)`. JS feature-detect (`canAsync`) → stará APK automaticky fallback na sync.

## Pravidla do budoucna
- **NIKDY nedělat síťové/pomalé I/O v synchronní `@JavascriptInterface` metodě** — vždy `callAsync` vzor (pozadí + callback). Platí i pro čtení kontaktů/SMS logu s per-záznam PhoneLookup/foto.
- Nové polly v /mobile NEpřidávat jako samostatné endpointy — rozšířit `poll-summary` (server) + `_pollApply` (JS).
- APK v1.80 = první R8-minifikovaná verze v terénu (R8 zapnul Jirka 27.7.); keep pravidla pro JS most v `app/proguard-rules.pro` — každou novou `@JavascriptInterface` metodu kryje `-keepclassmembers` anotační pravidlo, třídu `Bridge` kryje `-keep`. Nemazat.
- Gotcha bridge: `device_stage_files` odmítá `.kt`/`.kts` (HTTP 400) — kopie na `.txt`; `device_commit_files` `.kt` zapíše normálně.
- mobile_parts na disku dev stroje = STALE projekce; zdroj pravdy `g2007.soubor` (číst `SELECT encode(convert_to(obsah,'UTF8'),'base64')`, `length(obsah)` = znaky, ne bajty).

