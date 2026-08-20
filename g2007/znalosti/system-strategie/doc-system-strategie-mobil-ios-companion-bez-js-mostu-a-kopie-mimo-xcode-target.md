# iOS companion: co z Androidu prenest LZE a co ne + past kopie mimo Xcode target

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc tahle znalost vznikla (18. 8. 2026, Jirka + Claude-28, schvalila Marti-AI msg 12890 a 12893)
Marti hlasil, ze se pri praci na mobilni appce "prepsaly jeho upravy na rychlost tlacitek".
Overeni ukazalo neco jineho. **Aktualizovano 19. 8. 2026** - bod 2 upresnen, bod 3 uzavren.

## 1) Zrychleni tlacitek ma DVE poloviny a jen jedna je webova
Marti + C23 napsali 5. 8. 2026 async JS most `callAsync`.
- **Webova polovina** zije v `g2007.soubor` (`10_core.js` 4x `callAsync`,
  `74_claude27_render_init.js` poll-summary). Od 5. 8. na ni nikdo nesahl. **Nic se neprepsalo.**
- **Nativni polovina** (32 radku v `APP/Mobile/.../HybridActivity.kt`) **13 dni visela
  necommitnuta** na Martiho stroji; `git log -S callAsync` ukazuje prvni vyskyt az 18. 8.
  (commit `06a63984`). Proto ve verzich 1.81 a 1.82 chybela.

**Pouceni** - kdyz nekdo hlasi "prepsali jste mi to", over `git log -S <retezec>`. Kdyz se
retezec objevil az ted, nikdo nic neprepsal - prace se jen nikdy nepredala.
Naprava: verze 1.83 (versionCode 83, Google Play, 18. 8., commit `af0a5251`). Pred uploadem se
rucne prepisuji `releaseNotes` v `scripts/play_api_upload.py` - nejsou automaticke.

## 2) Co z Androidu do iOS prenest NEJDE - a co naopak JDE (upresneno 19. 8. 2026)
`APP/iOS` nema zadny JS most. Android vklada `Bridge` pres
`addJavascriptInterface(Bridge(), "STRATEGIE")`, JS si ho bere jako `window.STRATEGIE`. Na iOS
`window.STRATEGIE` neexistuje, stranka jede na obycejnem `fetch`, ktery JS vlakno nikdy
neblokuje. Pomalost, kterou Marti resil, vznikala **prave synchronnim mostem** - iOS ji nema,
`callAsync` tam nema co zrychlit.

Z 32 funkci mostu jsou Android-only veci bud **Applem zakazane** (odesilani a cteni SMS, seznam
hovoru, cteni notifikaci, cislo SIM), nebo existuji **jen kvuli telefonni integraci na Androidu**
(parovani, sideload update, baterie, toast), nebo je **iOS resi jinak** (tel. odkazy otevira
`Coordinator` nativne).

**⚠️ POZOR, puvodni zaver "kdyz to stoji na mostu, do iOS to nepatri" platí, ale NEPLATI
obracene.** 19. 8. 2026 se do iOS uspesne prenesly notifikace vcetne skoku na obrazovku -
Android ho totiz nedela pres most, ale volanim `window.__M2W.go('<screen>')`
(`HybridActivity.goScreen`, commit `4b40fd2e`), a `__M2W` je funkce **samotneho webu**, kterou
WKWebView zavola `evaluateJavaScript` uplne stejne. **Spravna otazka tedy neni "je to
z Androidu?", ale "stoji to na JS mostu, nebo na webu?"** Podrobne v
`doc-system-strategie-mobil-ios-notifikace-apns`.

Sedi to s doktrinou 22 - PWA je nosna, nativni appka je jen companion.

## 3) Past - soubor upraveny v kopii MIMO Xcode target (VYRESENO)
V `APP/iOS` lezely **dve kopie** `ContentView.swift`:
- `APP/iOS/mobile/ContentView.swift` - **tuhle Xcode stavi** (projekt ma
  `PBXFileSystemSynchronizedRootGroup` s `path = mobile`, zadny jiny zdroj v targetu neni)
- `APP/iOS/ContentView.swift` - **osirela kopie mimo target**, nestavela se

C24 pridala 15. 6. 2026 (commit `73a06f1d`) marker `applicationNameForUserAgent =
"STRATEGIE-iOS"` **jen do te osirele kopie** - do hotove appky se nikdy nedostal a nikde to
nehlasilo chybu. Opraveno 18. 8. (commit `a824d46c`).

**19. 8. 2026: osirela kopie uz v `origin/main` NENI** (overeno `git show`), past je tim
uzavrena. Marti-AI smazani doporucovala (msg 12893).

**Obecne pouceni plati dal:** pred editaci nativni appky over, ktery soubor je opravdu
v build targetu. Je to tentyz vzorec jako u dilku mobilu z 5.-12. 8.

## 4) Co odsud nejde overit
Swift se na Windows neprelozi. Zmeny v iOS souborech jsou odtud overitelne **ctenim a diffem**,
ne kompilaci. Build a vydani na App Store dela Jirka na Macu.
`APP/iOS` uz nema 78 radku Swiftu jako v cervnu, ale **378** (ContentView 86, PushNotifications
271, mobileApp 21) - stav k 19. 8. 2026.

