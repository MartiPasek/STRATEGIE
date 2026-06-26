# 🟢 Google Play — co zbývá k vydání (pro Martiho + Claude-23)

> Sepsal Claude-28 s Jirkou 26. 6. 2026, **aktualizováno 26. 6. po flavor splitu.**
> Dev účet Marti Pašek, app `cz.strategie.mobile`, ID `4972314462968882587`.

## ✅ Co je HOTOVÉ (26.6.)
- **Záznam v obchodu KOMPLETNÍ** (název, popisy, ikona, feature, 2 screenshoty, kategorie Byznys, kontakt).
- **9 deklarací App content** (soukromí, reklamy, hodnocení Everyone/PEGI 3, app access = demo režim, cílovka 18+, inzertní ID, zdraví, stát, finance).
- **`/privacy` PŘEPSÁNO** (Marti, commit `16f12f2a`) — veřejná B2B služba + SMS bez ověřovacího účelu („appka nežádá o přístup k SMS; firemní SMS běží na serveru / vyhrazeném zařízení"). **Blok č.1 z minula = VYŘEŠEN.**
- **FLAVOR SPLIT `play` vs `internal`** (commit `5c2d4838`, ověřeno Gradle manifest mergem):
  - `play` (= AAB do Google Play) = **BEZ SMS** (SEND/READ/RECEIVE_SMS, SmsReceiver) a **BEZ samo-update** (REQUEST_INSTALL_PACKAGES, InstallActivity). Sedí s novým `/privacy`.
  - `internal` (= sideload + gateway telefon) = SE SMS bránou + samo-update (beze změny chování).
  - **Blok č.2 z minula (flavor play) = VYŘEŠEN.** Navíc **odpadá SMS deklarace i SMS video** (play SMS nemá).

## ⏭️ KRITICKÝ DALŠÍ KROK — pro Martiho / Claude-23: podepsaný `play` AAB
Tohle je **jediná věc, co teď blokuje** cestu do produkce. Jde to **jen na Martiho build stroji** (kde je klíč `strategie-release.jks` přes `keystore.properties` — na Jirkově stroji NENÍ, proto to Claude-28 neudělá).

1. **Srovnat lokál** (vzít flavor split): `git pull` (nebo přes bridge `CLAUDE_PULL_GO`).
2. **Postavit podepsaný AAB:** `scripts/build_aab.ps1`
   → spustí `gradlew bundlePlayRelease` (flavor `play`, bez SMS)
   → výstup `APP/Mobile/app/build/outputs/bundle/playRelease/app-play-release.aab`.
   *(Pozn.: holé `bundleRelease` postaví OBA flavory — skript správně cílí `play`.)*
3. **Nahrát AAB** do Play Console → track **Produkce** (nebo nejdřív interní/uzavřené testování → pak promote).

   **TODO na build stroji:** po deployi flavor splitu **restart watcheru `STRATEGIE-CLAUDE-SQL`** (změnily se v něm build příkazy: sideload APK je teď `assembleInternalRelease`). Týká se sideload bridge buildu; `build_aab.ps1` to nepotřebuje.

## ⏭️ AŽ BUDE ČISTÝ AAB NAHRANÝ — dotáhne Claude-28 / Jirka v Console
Pořadí je důležité: tyhle kroky musí být PO nahrání play AAB (Console je odvozuje od oprávnění nahraného buildu).

1. **Data safety — upravit dle play buildu:** v kroku 3 **ODEBRAT „SMS nebo MMS"** (play SMS nesbírá) → zůstává **10 typů**. Pak krok 4 mechanicky (viz `google_play_data_safety_mapping.md`, aktualizováno).
2. **Permissions declaration:** SMS deklarace ani SMS video **už NEJSOU potřeba** (play SMS nemá). Zůstává jen **`READ_CALL_LOG`** (rozhodnuto nechat) → Google může chtít deklaraci + příp. video; texty v `google_play_permissions_declaration.md`. *(Pozn.: zvážit i úplné odebrání READ_CALL_LOG z play — call-log se zatím jen lokálně zobrazuje, neuploaduje; pak by odpadla i tahle deklarace. Rozhodnutí Marti/Jirka.)*
3. **Výběr testerů** (interní testování 2/3 → 3/3) — přiřadit testery až k **čistému** AAB (ne ke starému se SMS, co tam visí teď).
4. **Production rollout** → odeslat ke kontrole.

## Pozn. ke starému AAB
V interním testování visí **starý build se SMS** (nahraný dřív). Interní testování Google nereviduje, takže nevadí — ale do produkce/testerům jde až **nový čistý play AAB**.
