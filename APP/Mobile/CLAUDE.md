# STRATEGIE Mobile — Android companion appka

Kontext pro práci nad touto podsložkou (`D:\Projekty\STRATEGIE\APP\Mobile`).
Když Cowork pustíš nad touhle složkou, načte se jen tenhle malý soubor =
malý prompt, fokus na appku. Plný kontext projektu = pustit Cowork nad
`D:\Projekty\STRATEGIE`.

## Co to je

Nativní Android appka (Kotlin + Jetpack Compose). **Pomocník na telefonu**,
ne náhrada PWA. PWA (`strategie-ai.com`) zůstává nosný produkční systém.
Appka jen: nastavení + odkazy na PWA, a postupně služba na pozadí
(dial poller, sync kontaktů, call-log → CRM). Komunikace JEN přes HTTPS API.
Vize: `../../docs/native_app_vize.md` (3.6.2026).

## Stav

- **v0 (hotovo):** `MainActivity.kt` — obrazovka Nastavení (URL serveru +
  token, uloženo v SharedPreferences `strategie_prefs`) + tlačítka
  „Otevřít Chat" (`<url>/`) a „Otevřít ERP" (`<url>/erp`) přes browser Intent.
  Manifest: `INTERNET`. Žádné extra závislosti.

## Plán (další fáze)

- **v1** BootReceiver + Foreground Service + WorkManager (běh po rebootu)
- **v2** dial poller — pollne `phone_dial_request` na serveru → vytočí
  (nahradí PWA poller, funguje i když je PWA zavřená)
- **v3** sync kontaktů (caller-ID, náhrada DAVx5, jeden login)
- **v4** call-log → CRM (zmeškané / protokoly hovorů zákazníků)

## Konvence / fakta

- package / applicationId: `cz.strategie.mobile`
- téma Compose: `STRATEGIEMobileTheme` (`@style/Theme.STRATEGIEMobile`)
- minSdk 26, targetSdk/compileSdk 36, Compose BOM 2026.02.01, Material3,
  Kotlin DSL, version catalog `gradle/libs.versions.toml`
- distribuce: interní (sideload APK), ne Play Store — kvůli `READ_CALL_LOG` (v4)
- jeden git repo (součást STRATEGIE), build artefakty ignoruje `.gitignore`
  vytvořený Android Studiem
- server API: `https://strategie-ai.com`; auth později přes token
  (CardDAV/device token z Phase 38 backendu)

## Build / běh

- Android Studio → Gradle sync → ▶ Run na připojeném mobilu (USB ladění).
- APK pro sideload: Build → Build APK(s), nebo `./gradlew assembleDebug`
  (výstup `app/build/outputs/apk/debug/`).
