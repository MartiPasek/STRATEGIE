# iOS: gesto zpet vracelo na nahodnou stranku - v appce bezela DVE gesta naraz (27.-28. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Priznak

Na iPhonu svihnuti od leveho okraje **nevratilo o obrazovku zpet, ale na nahodnou drivejsi
stranku** (nahlasil Jirka Honomichl 27. 8. 2026). Na Androidu se to nedelo.

## Pricina - dva zdroje teze pravdy

Pri jednom svihnuti bezely **dve nezavisle veci**:

1. **Vlastni gesto appky** (spravne) - `10_core.js` ma posluchac `touchstart`/`touchend`:
   start do 26 px od leveho okraje, `dx > 60`, `dy < 48`, do 700 ms -> vola `back()`,
   tedy o uroven vys ve `window.__M2W.stack`. Komentar u nej: *"iPhone nema systemove
   tlacitko Zpet -> swipe od leveho okraje = Zpet. Funguje v PWA i ve WKWebView."*
2. **Vestavene gesto WKWebView** (spatne) - `web.allowsBackForwardNavigationGestures = true`
   v `APP/iOS/mobile/ContentView.swift`. To chodi po **historii prohlizece**.

Appka drzi navigaci **jen v pameti** (`window.__M2W.stack`) a vsechny obrazovky maji
**tutez URL**, takze v historii prohlizece je nahodna smes drivejsich stranek - odtud
"vraci to kamkoli". Android tenhle problem nema, tam systemove zpet vola `__stgBack()`
(HybridActivity.kt r. 799).

## Oprava

`web.allowsBackForwardNavigationGestures = **false**` (commit `98bc1d7e`, 28. 8. 2026).
**Zadny vlastni UIScreenEdgePanGestureRecognizer se nepridava** - byl by to druhy zdroj
teze pravdy vedle uz existujiciho gesta ve webove vrstve (Marti-AI, msg 13911).
V souboru je u toho radku komentar, aby to pristi clovek "neopravil" zpatky.

⚠️ **iOS obal se stavi RUCNE v Xcode na Macu** a rozdava pres TestFlight - zmena v repu
sama do telefonu nedojde. Sestaveni dela Jirka.

## Souvisejici nalez: kde se bere spodni lista "← Zpet"

Spodni lista `bnavback` se **skryva podle identifikace zarizeni**:
`_showBack = stack.length>1 && _bbCfg!=="never" && (_bbCfg==="always" || (!_isAndroid && !_isIOS))`,
kde `_isIOS` = pritomnost markeru **`STRATEGIE-iOS`** v user agentu (nastavuje ho
`applicationNameForUserAgent` v ContentView.swift).

Zmereno 27. 8. 2026 v prohlizeci pod ctyrmi identifikacemi:

| identifikace | spodni lista |
|---|---|
| Android appka | skryta |
| iPhone appka **s** markerem | skryta |
| iPhone appka **bez** markeru | **ukaze se** |
| webovy prohlizec | ukaze se (zamer) |

**Jestli marker v buildu je, pozna se na domovske obrazovce:** radek `h2` ukazuje
**"Nativní appka"** (`window.__M2W.nativeApp`), jinak "Prohlížeč (PWA)". Je to tentyz
priznak, ktery ridi i skryvani listy - kdyz tam stoji "Nativní appka", lista skryta JE
a viditelne "Zpet" je nektere z **vnitroobrazovkovych** tlacitek (`_cilBack`, `_eaBack`,
"‹ Zpet" v Planu prace, tlacitka ve formularich).

**Ta vnitrni tlacitka se nechavaji** (Marti-AI, msg 13911): na Androidu jsou jedina
viditelna cesta zpet krome systemoveho gesta a vznikla prave proto, ze spodni lista
je v appce skryta.

---

## ⚠️ DOPLNENO 28. 8. 2026 — tohle uz jednou vyresene BYLO, jen v jinem repu

Pri zaverecne kontrole rozporu se naslo, ze **26. 8. 2026 uz stejny problem resila Macova
session Claude-28** — znalost [[doc-system-strategie-ios-gesto-zpet-screen-edge-pan]].
Tam je zvolene **jine reseni**: `allowsBackForwardNavigationGestures` vypnuto **a navic
pridan `UIScreenEdgePanGestureRecognizer`** (hrana `.left`, `Coordinator` implementuje
`UIGestureRecognizerDelegate`, `shouldRecognizeSimultaneouslyWith` -> `false`), ktery po
dokonceni tazeni vola `window.__stgBack()`. Overeno naostro v simulatoru iPhone 17 / iOS 26.5.

**Ta zmena ale NIKDY nedosla do repa STRATEGIE.** Doloženo 28. 8. 2026:
- `grep UIScreenEdgePan APP/iOS/mobile/ContentView.swift` = **0 vyskytu**,
- `git log -- APP/iOS/mobile/ContentView.swift` zadny takovy commit nema.

Commit `5952e30` z 26. 8. lezi v **jinem repu** — `cz.strategie.mobile`
(GitHub `GHubGeorge/strategie-mobile`) na Macu. Obsah se odtud do repa STRATEGIE prenasi
**rucne** (viz commity `24e85a73`, `c3bddc90` — prenos obsahu PR pres most, protoze slouceni
na GitHubu nejde: ucet nema pravo zapisu). U teto zmeny se to **nestalo**.

### Co z toho plyne

1. **Dva repozitare se rozesly.** V repu STRATEGIE je dnes (commit `42042088`, 28. 8.)
   vypnuty priznak **bez** recognizeru; v Macovem repu je vypnuty priznak **s** recognizerem.
   Kdo bude stavet appku, musi vedet, ze **stavi z Macoveho repa** - jinak vydá jinou verzi,
   nez kterou nekdo odzkousel.
2. **Obe reseni funguji, ale nejsou totez.** Bez recognizeru se gesto opira **vyhradne**
   o webovou vrstvu (`10_core.js`, touchstart/touchend na levem okraji) - ta v appce je
   a overil jsem ji 27. 8. na zive `/mobile`. S recognizerem jede gesto nativne pres
   `window.__stgBack()`. **Ktere z nich ma platit, rozhoduje clovek**, ne instance.
3. **Zadna z tech oprav zatim NENI v telefonech.** Znalost z 26. 8. vyslovne uvadi, ze
   verze ani build appky **nebyly zvyseny** (Jirka chtel vydat az po vyreseni banneru
   s aktualizaci). Proto Jirka 27. 8. porad hlasil, ze gesto na iPhonu vraci na nahodnou
   stranku - **v jeho nainstalovane appce zadna z uprav neni.**

**Ponauceni pro pristi instanci:** nez zacnes resit cokoli kolem nativni iOS appky,
**projdi znalosti na `iOS` a `gesto`** a **over `git log` prislusneho souboru** - iOS zije
ve dvou repech a to, ze neco neni v repu STRATEGIE, neznamena, ze to nikdo neudelal.

