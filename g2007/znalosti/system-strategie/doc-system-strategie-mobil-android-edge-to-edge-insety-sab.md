# Android 15/16: carka gest prekryvala spodni listu mobilu - obal predava zony strance pres --sab (2.9.2026, vydano 1.86), opt-out atribut je na targetSdk 36 mrtvy

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Android 15/16: čárka gest překrývala spodní lištu mobilu — obal předává systémové zóny stránce (`--sab`)

**2. 9. 2026, Claude-28 / Jiří Honomichl, schválila Marti-AI msg 14272 a 14275.** Vzniklo při řešení Jirkova podnětu „prázdný pruh pod lištou na iPhonu" (iOS část: [[doc-system-strategie-ios-1-86-spodni-pruh-build-na-macu]]).

## Příznak a koho se týká

Od **Androidu 15** kreslí systém obsah appky, která cílí na SDK 35+, **povinně až pod stavovou lištu a pod čárku gest** (edge-to-edge). Náš obal (`APP/Mobile`, `targetSdk = 36`) žádné odsazení neřešil a WebView o zónách neví — `env(safe-area-inset-*)` v něm vrací **0**. Výsledek (ověřeno v emulátoru Pixel 6 / Android 16, appka 1.79 a 1.85, ukázkový účet): **čárka gest ležela přes popisky spodní lišty** (překrývala „Úkoly"), **stavová lišta přes horní okraj obsahu** (hodiny přes červený pruh ukázkového režimu).

Dopad jmenovitě (`fw.mobile_device`, aktivní za 30 dní k 2. 9. 2026): **Android 16 — 13 lidí** (Havlát, Nepodalová, Kasal, Peřina, Erhard, Honal, M. Pašek, Hladíková, Voříšek, Zeman, Beneš, Šafránková, Novotná), **Android 15 — 3 lidé** (Veverka, Šik, Diviš). **Android 14 a starší — 17 lidí, netýká se** (systém tam kreslí lišty sám). Na Windows v prohlížeči ani na iPhonu se tohle neděje (jiný mechanismus, viz odkaz výše).

## Co NEFUNGUJE — neopakovat

**Atribut tématu `android:windowOptOutEdgeToEdgeEnforcement=true`** vypadá jako minimální oprava, ale **na Androidu 16 je pro appky s targetSdk 36 vypnutý**. Ověřeno dvakrát: (1) zkušební sestavení — atribut je v balíčku (`aapt2 dump resources`, `0x0101069a=true` v `Theme.STRATEGIEMobile`, `HybridActivity` téma používá) a čárka popisky překrývá dál; (2) dokumentace `developer.android.com/about/versions/16/behavior-changes-16`: *„For apps targeting Android 16 (API level 36), windowOptOutEdgeToEdgeEnforcement is deprecated and disabled, and your app can't opt-out."* Pomohl by jen na Androidu 15 (3 lidé), třinácti na Androidu 16 ne. Změna byla vrácena, v repu není.

## Řešení (commit `3c99b4af`, 2. 9. 2026)

**Obal — `HybridActivity.kt`, jen pro `Build.VERSION.SDK_INT >= 35`** (Android ≤ 14 jde beze změny větví `else`, protože tam to ověřit nejde — jediný obraz v emulátoru je android-36):
- WebView je v `FrameLayout` s pozadím **#0e0f11** (= `--bg` stránky). `ViewCompat.setOnApplyWindowInsetsListener` na kontejneru: **nahoře/po stranách** `setPadding(left, top, right, 0)` z `systemBars() or displayCutout()` → obsah začíná pod stavovou lištou, vzhled jako na Androidu 14; světlé ikony stavové lišty přes `WindowCompat.getInsetsController(...).isAppearanceLightStatusBars = false`.
- **Dole** se výška zóny (`insets.bottom / density`) předá stránce přes `evaluateJavascript` jako CSS proměnná **`--sab`** (`pushSafeBottom()`), a to **při každé změně insetů** (otočení, skrytí lišt) **i v `onPageFinished`** — obnovení stránky proměnnou smaže. Proč ne nativní padding dole: kontejner by pod lištou ukázal pás v barvě pozadí = přesně ten „prázdný pruh", který Jirkovi vadí na iPhonu.

**Stránka `/mobile` (g2007.soubor) — 8 míst:** spodní lišta (`02_styles.html`: `.bottomnav`, `#navwrap > .bnavstatic:last-child`, `.homebg`; `74_claude27_render_init.js`: `renderNav`, `bnav.style.paddingBottom`) a čtyři celoobrazovkové překryvy (`10_core.js` spodní panel, `51_skupiny_sdileny.js` sekce Firma, `60_dochazka.js` `#dpCtl`, `70_tail.js` podpisový panel). Všude místo `env(safe-area-inset-bottom,0)` nově **`max(env(safe-area-inset-bottom,0px), var(--sab,0px))`**. Na iOS a v prohlížeči je `--sab` nenastavená → 0 → chování beze změny (ověřeno v Chromu: padding 0, lišta až dolů). `_syncNavH()` měří `offsetHeight` včetně paddingu, `--navh` se dopočítá samo. Jediné místo s `env(safe-area-inset-top)` (docházkový překryv v `60_dochazka.js`) zůstalo — horní zónu řeší kontejner obalu (překryv je uvnitř WebView) a na iOS SwiftUI.

⚠️ **V `max()` musí být záložní hodnota `env()` s jednotkou (`0px`)** — holé `0` je v matematické funkci neplatné a celé pravidlo by se zahodilo.

## Ověřeno (2. 9. 2026, emulátor Android 16, gesta)

Pixely snímku: nahoře 0–126 px barva #0e0f11 (zóna stavové lišty), obsah od 132 px; dole lišta #121519 sahá až k okraji (2400 px), tlačítka končí 63 px nad okrajem = přesně inset, čárka leží ve volném spodku lišty. Otočení na šířku: kontejner se přestaví (výřez kamery vlevo odsazen, lišta nad čárkou). Web na Windows beze změny. **Android 15 a Android ≤ 14 v emulátoru neověřeno** (není obraz) — proto podmínka SDK ≥ 35. Předání `--sab` po obnovení stránky je zajištěno kódem (`onPageFinished`), zvenku se v appce reload vyvolat nedá (WebView není ladicí) — ověřeno jen na startu appky, který touž cestou prochází.

## Vydání — Android 1.86 (kód 86) nahráno 2. 9. 2026

`gradlew bundlePlayRelease` (auto-bump `version.properties` 85 → **86 / 1.86**, ověřeno v merged manifestu i archivu), podpis náš klíč **CC:AC**, poznámky k vydání ve `scripts/play_api_upload.py` přepsány na tuto verzi, upload `python scripts/play_api_upload.py aab --confirm` → **produkční track, odesláno ke kontrole automaticky** (commit bez `changesNotSentForReview`), ověřeno čtením zpět z androidpublisher API. Debug sestavení (`assembleInternalDebug`) verzi nezvyšuje — hodí se na zkoušky v emulátoru. Dokud Google 1.86 neschválí a lidé si ji nestáhnou, 16 lidí vidí čárku přes popisky dál (stránka to bez nového obalu neopraví, `--sab` nemá kdo nastavit).

Souvisí: [[doc-system-strategie-mobil-navh-spodni-lista]] · [[doc-system-strategie-verzovani-ios-android-nezavisla-cisla]] · [[doc-system-strategie-vydavani-mobilni-appky-jen-obchody]]

