# iOS 1.86 (build 86) - prazdny pruh pod spodni listou; ZMENA JE V REPU, CEKA NA BUILD A UPLOAD NA MACU (2.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS 1.86 (build 86) — prázdný pruh pod spodní lištou; změna je v repu, čeká na build na Macu

**Stav k 2. 9. 2026 (Claude-28 / Jiří Honomichl, schválila Marti-AI msg 14263 a 14266).**
**Ověření na iPhonu dosud NEPROBĚHLO** — z Windows stroje nejde iOS sestavit. Tohle je zadání pro session na Macu.

## Co má Mac session udělat

1. `git pull` repa STRATEGIE (jediný zdroj pravdy pro iOS je `APP/iOS`, viz [[doc-system-strategie-ios-jeden-repos-vse-do-strategie]]). Ověř, že v `APP/iOS/mobile/ContentView.swift` je řádek `web.scrollView.contentInsetAdjustmentBehavior = .never` a v `project.pbxproj` je `MARKETING_VERSION = 1.86` a `CURRENT_PROJECT_VERSION = 86` (obě konfigurace). Když tam nejsou, přenos se nepovedl — nic nevymýšlej, ozvi se Jirkovi.
2. Sestav a spusť **nejdřív v simulátoru nebo na Jirkově iPhonu** (postup a pasti v [[doc-system-strategie-ios-build-upload-a-past-dvou-contentview]], ovládání simulátoru v [[doc-system-strategie-simulator-ovladani-osascript-cliclick]]).
3. **Ověř na zařízení / v simulátoru s domovskou čárkou (iPhone bez tlačítka)** — všechno tohle musí platit naráz:
   - spodní lišta s ikonami (Domů, Aplikace, Úkoly, Kontakty, Firma) sahá **až k dolnímu okraji** displeje, pod ní **není** pruh v barvě pozadí stránky;
   - ikony a popisky sedí **nad** domovskou čárkou, čárka je nepřekrývá (lišta si drží `padding-bottom: max(env(safe-area-inset-bottom), var(--sab))`);
   - **nahoře beze změny** — obsah nezačíná pod stavovou lištou (horní bezpečnou zónu drží SwiftUI, `.ignoresSafeArea` je jen pro `.bottom`);
   - obrazovka Firma — lišta skupin nad hlavní lištou dál funguje;
   - potáhnutí dolů (obnovení stránky) a gesto zpět od levého okraje dál fungují.
   Když něco z toho neplatí, **nevydávej** — zapiš sem, co konkrétně, a ozvi se Jirkovi.
4. Až to sedí: archiv + upload do App Store Connect + odeslání ke schválení (dvoukrokové „Add for Review" → „Submit for Review", viz build-upload znalost). Do „What's New" napiš lidsky: „Spodní lišta sahá až k okraji displeje, zmizel prázdný pruh pod ní; popisek Aplikace je ve stejné výšce jako ostatní."
5. Po uploadu **aktualizuj tuhle znalost** (stav, datum, kdo ověřil) a v build-upload znalosti řádek „příští = 87".

## Co se změnilo a proč

- **Příznak:** na iPhonu (snímky Jirky 2. 9. 2026, obrazovky Kontakty, Úkoly, Aplikace) končila spodní lišta ~35 bodů nad okrajem a pod ní byl pruh v barvě pozadí stránky (#0e0f11). Z pixelů snímků — lišta #121519, pruh #0e0f11 = přesně bezpečná zóna domovské čárky. **Není to skryté tlačítko Zpět** (to je `display:none`).
- **Příčina:** stránka je připravená (`viewport-fit=cover` v `00_head.html` od 3. 8., lišta má `padding-bottom` s `env(safe-area-inset-bottom)` — v prohlížeči na Windows sahá až dolů, ověřeno měřením). Obal má `.ignoresSafeArea(edges: .bottom)`, ale **nenastavoval `contentInsetAdjustmentBehavior`** (výchozí `.automatic`) — WKWebView si obsah sám odsadí nad zónu, stránka dostane `env()` = 0, lišta skončí nad zónou a WebKit pod ní vykreslí pozadí dokumentu.
- **Oprava:** jeden řádek v `makeUIView` — `web.scrollView.contentInsetAdjustmentBehavior = .never` (s komentářem v kódu). Standardní kombinace pro web přes celý displej — `viewport-fit=cover` + `env(safe-area-inset-bottom)` + `.never`.
- **Verze:** 1.85 → 1.86, build 85 → 86 (čísla iOS a Android jsou nezávislá, [[doc-system-strategie-verzovani-ios-android-nezavisla-cisla]]).

## Souvislosti

- Popisek „Aplikace" o 4 px níž (SVG ikona místo emoji) — opraveno 2. 9. 2026 ve stylech stránky (`02_styles.html`, pravidlo `.tabbtn .i svg`), platí pro všechny platformy hned, bez nového buildu. Lišta je tím o 4 px nižší (61 px místo 65), `--navh` se dopočítá sama.
- Android má jiný projev téže věci (od Androidu 15 čárka gest přes popisky a stavová lišta přes obsah) — vyřešeno v obalu Android posluchačem insetů + CSS proměnnou `--sab`, kterou si spodní lišta stránky bere přes `max(env(...), var(--sab))`; na iOS je `--sab` nenastavená, takže se iOS týká jen `env()`. Detail: [[doc-system-strategie-mobil-android-edge-to-edge-insety-sab]]. Vydání na Play je samostatné.
- Koho se týká: iOS appku má 6 lidí s aktivním tokenem (Honomichl, Pěchouček, Trunec, Jakešová, Porner, Valenta) — z `fw.ios_push_token`.
- Mechanika lišty a `--navh` — [[doc-system-strategie-mobil-navh-spodni-lista]].

