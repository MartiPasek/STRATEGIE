# iOS appka: gesto zpět tažením od levého okraje (nasazeno 26.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS appka: gesto zpět tažením od levého okraje

Zapsal Claude-28 (Jirka Honomichl) 26.8.2026. Navazuje na
`doc-system-strategie-mobil-ios-companion-bez-js-mostu-a-kopie-mimo-xcode-target`.

## Problém

`WKWebView.allowsBackForwardNavigationGestures = true` (nativní gesto zpět/vpřed
z historie WKWebView) nemělo na co sahat. Appka drží vlastní kroky obrazovek ve
vlastním JS poli (`window.__M2W.stack`), ne v historii prohlížeče (žádné
`pushState`) — takže tažení od kraje nikdy nic nevrátilo.

## Řešení

`mobile/ContentView.swift`: `allowsBackForwardNavigationGestures` vypnuto,
místo toho přidán `UIScreenEdgePanGestureRecognizer` (hrana `.left`) přes
`Coordinator` (nově implementuje i `UIGestureRecognizerDelegate`,
`shouldRecognizeSimultaneouslyWith` → `false`, ať nekoliduje se scrollem/swipem
uvnitř WKWebView). Po dokončení tažení (`gesture.state == .ended`) appka zavolá
`window.__stgBack()` přes `evaluateJavaScript` — přesně stejný mechanismus,
jaký pro krok zpět používá Android hardwarové tlačítko
(`HybridActivity.onBackPressedDispatcher`).

## Ověření (26.8.2026, iPhone 17 simulátor, iOS 26.5)

Naostro v simulátoru, opakovaně (dvakrát nezávisle): z obrazovky
„Aplikace" → „Moje osobní údaje" tažení od levého okraje appku vrátilo
zpět na „Aplikace". Ověřeno screenshoty před/po po každém pokusu.

## Stav

Commitnuto a nahráno do `main` repa `cz.strategie.mobile`
(GitHub `GHubGeorge/strategie-mobile`), commit `5952e30`, 26.8.2026.
**Verze/build appky NEZVÝŠENA** — Jirka rozhodl vydat novou verzi až po
vyřešení tématu „banner s aktualizací" (viz níž), aby se nevydávalo po
kouskách. Změna tedy leží v gitu, ale zatím není v žádném buildu odeslaném
do App Store.

## Co zatím čeká (nesouvisí přímo s gestem, jen vzniklo ve stejné session)

- Banner „Nová verze STRATEGIE — klepni pro obnovení" překrývá obsah a po
  kliknutí skočí na domovskou obrazovku místo tam, kde uživatel byl —
  Jirka chce probrat možnosti řešení, zatím žádná analýza ani kód.
- Bod o stropu u žádosti o dovolenou (má i sick day blokovat, ne jen
  varovat) — čeká na Jirkovu odpověď.
- Tlačítko „Odvozy" vrací appce 403 (`/api/v1/erp/app/vyroba/odvozy`) —
  Jirkův účet nemá roli „vedoucí výroby", čeká se, kdo tuhle roli má mít.
- PIN po probuzení appky z pozadí na iOS není skrytý hvězdičkami — nenašel
  jsem to v nativním kódu, potřeba ověřit přímo v simulátoru/na telefonu.

