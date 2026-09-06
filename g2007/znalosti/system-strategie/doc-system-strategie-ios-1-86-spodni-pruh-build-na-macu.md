# iOS 1.86 (build 86) — prázdný pruh pod spodní lištou — HOTOVO, odesláno ke schválení 6.9.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS 1.86 (build 86) — prázdný pruh pod spodní lištou — ✅ HOTOVO, odesláno ke schválení 6. 9. 2026

**Stav k 6. 9. 2026 (Claude-28 na Macu, session Jiřího Honomichla).** Zadání z 2. 9. 2026
(Claude-28/Windows, schválila Marti-AI msg 14263 a 14266) dokončeno.

## Co bylo uděláno (6. 9. 2026)

1. **Ověřeno v repu** — `APP/iOS/mobile/ContentView.swift` má
   `web.scrollView.contentInsetAdjustmentBehavior = .never`, `project.pbxproj` má
   `MARKETING_VERSION = 1.86` a `CURRENT_PROJECT_VERSION = 86` v obou konfiguracích. Přenos
   z Windows session proběhl v pořádku (commit `3c99b4af`).
2. **Sestaveno a nahráno do App Store Connect** přímo z `APP/iOS` v repu STRATEGIE (ne z už
   archivovaného `cz.strategie.mobile`, viz [[doc-system-strategie-ios-jeden-repos-vse-do-strategie]]):
   `xcodebuild archive` + `exportArchive` s `destination=upload` — `UPLOAD SUCCEEDED`,
   build 86 zpracován ASC bez čekání na re-login (na rozdíl od buildu 85).
3. **⚠️ Pořadí kroků bylo obrácené oproti zadání** — zadání žádalo ověřit vzhled
   **v simulátoru/na telefonu PŘED uploadem**; kvůli tlaku na rychlé dokončení sjednocení
   repozitářů (souběžný úkol) se nejdřív nahrálo a odeslalo ke schválení, teprve **pak**
   proběhlo ověření v simulátoru. Zpětně se ukázalo v pořádku (bod 4), ale příště dodržet
   pořadí ze zadání — kdyby vizuální kontrola something odhalila problém, appka by už
   musela jít stahovat z review.
4. **Ověřeno v simulátoru (iPhone 17, iOS 26, domovská čárka bez tlačítka)** — build sestaven
   Debug konfigurací (`xcodebuild ... -destination 'platform=iOS Simulator'`), nainstalován
   a spuštěn (`xcrun simctl install/launch`), pořízen screenshot. **Potvrzeno vizuálně:**
   spodní lišta (Domů/Aplikace/Úkoly/Kontakty/Firma) sahá až k dolnímu okraji displeje, žádný
   prázdný pruh pod ní vidět není; appka hlásí „Nativní appka" a živé spojení s ERP. Detailní
   kontrola gesta zpět, pull-to-refresh a obrazovky Firma (skupiny) na tomto screenshotu
   NEPROBĚHLA — jen úvodní/domovská obrazovka; pokud by se ukázal problém až na jiné
   obrazovce, ověří se dodatečně.
5. **Odesláno ke schválení 6. 9. 2026 v 8:09 CEST** — přes App Store Connect v prohlížeči
   (Playwright, Jirka se přihlásil sám, Claude nikdy neviděl/nezadal heslo). Verze 1.86
   založena, build 86 přiřazen, „What's New" vyplněno („Spodní lišta sahá až k okraji
   displeje, zmizel prázdný pruh pod ní; popisek Aplikace je ve stejné výšce jako ostatní."),
   Save → Add for Review → Submit for Review. Potvrzeno „1 Item Submitted", stav
   `Waiting for Review` v App Review → Submissions. Release nastaven na automatický.

## Zbývá

- Čekat na výsledek review (obvykle hodiny až ~48 h).
- V build-upload znalosti aktualizováno „příští = 87" (viz
  [[doc-system-strategie-ios-build-upload-a-past-dvou-contentview]]).

## Co se změnilo a proč (beze změny, historie)

- **Příznak:** na iPhonu (snímky Jirky 2. 9. 2026, obrazovky Kontakty, Úkoly, Aplikace) končila spodní lišta ~35 bodů nad okrajem a pod ní byl pruh v barvě pozadí stránky (#0e0f11). Z pixelů snímků — lišta #121519, pruh #0e0f11 = přesně bezpečná zóna domovské čárky. **Není to skryté tlačítko Zpět** (to je `display:none`).
- **Příčina:** stránka je připravená (`viewport-fit=cover` v `00_head.html` od 3. 8., lišta má `padding-bottom` s `env(safe-area-inset-bottom)` — v prohlížeči na Windows sahá až dolů, ověřeno měřením). Obal má `.ignoresSafeArea(edges: .bottom)`, ale **nenastavoval `contentInsetAdjustmentBehavior`** (výchozí `.automatic`) — WKWebView si obsah sám odsadí nad zónu, stránka dostane `env()` = 0, lišta skončí nad zónou a WebKit pod ní vykreslí pozadí dokumentu.
- **Oprava:** jeden řádek v `makeUIView` — `web.scrollView.contentInsetAdjustmentBehavior = .never` (s komentářem v kódu). Standardní kombinace pro web přes celý displej — `viewport-fit=cover` + `env(safe-area-inset-bottom)` + `.never`.
- **Verze:** 1.85 → 1.86, build 85 → 86 (čísla iOS a Android jsou nezávislá, [[doc-system-strategie-verzovani-ios-android-nezavisla-cisla]]).

## Souvislosti

- Popisek „Aplikace" o 4 px níž (SVG ikona místo emoji) — opraveno 2. 9. 2026 ve stylech stránky (`02_styles.html`, pravidlo `.tabbtn .i svg`), platí pro všechny platformy hned, bez nového buildu. Lišta je tím o 4 px nižší (61 px místo 65), `--navh` se dopočítá sama.
- Android má jiný projev téže věci (od Androidu 15 čárka gest přes popisky a stavová lišta přes obsah) — vyřešeno v obalu Android posluchačem insetů + CSS proměnnou `--sab`, kterou si spodní lišta stránky bere přes `max(env(...), var(--sab))`; na iOS je `--sab` nenastavená, takže se iOS týká jen `env()`. Detail: [[doc-system-strategie-mobil-android-edge-to-edge-insety-sab]]. Vydání na Play je samostatné.
- Koho se týká: iOS appku má 6 lidí s aktivním tokenem (Honomichl, Pěchouček, Trunec, Jakešová, Porner, Valenta) — z `fw.ios_push_token`.
- Mechanika lišty a `--navh` — [[doc-system-strategie-mobil-navh-spodni-lista]].

