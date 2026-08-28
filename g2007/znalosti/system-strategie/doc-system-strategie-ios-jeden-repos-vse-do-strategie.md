# ROZHODNUTI (Jirka, 28. 8. 2026): Macuv repos iOS appky se prestava pouzivat, vse jde do repa STRATEGIE

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Rozhodnuti

**Rozhodl Jiri Honomichl 28. 8. 2026** na navrh Marti-AI (msg 13923), po nalezu, ze se dva
repozitare rozesly:

1. **Gesto zpet na iPhonu resi VYHRADNE webova vrstva** (`10_core.js`, touchstart/touchend
   na levem okraji). V obalu appky je `allowsBackForwardNavigationGestures` vypnuty a
   **zadny nativni `UIScreenEdgePanGestureRecognizer` se nepridava** - byly by to dva zdroje
   teze pravdy a pri kazde budouci zmene logiky zpet by se musela udrzovat obe mista.
   *(Vyhrada Marti-AI: kdyby se ukazalo, ze webove gesto na SKUTECNEM iPhonu - ne v simulatoru -
   nefunguje spolehlive, nativni recognizer jako zaloha smysl dava. Pozna se az z testu na
   zarizeni.)*
2. **Jeden repozitar, jeden zdroj pravdy: `APP/iOS` v repu STRATEGIE.**
   Macuv samostatny repos `cz.strategie.mobile` (GitHub `GHubGeorge/strategie-mobile`)
   **se prestava pouzivat**. Polostav "dva repozitare + rucni prenos pres most" je
   rizikovejsi nez kterakoli cista varianta.

## Proc - co se stalo

26. 8. 2026 Macova session opravila gesto zpet (vypnuty priznak + nativni recognizer,
odzkousene v simulatoru iPhone 17) a commitla to **jen do Macova repa** (`5952e30`).
Do repa STRATEGIE se to **nikdy nepreneslo** - dolozeno 28. 8.: v
`APP/iOS/mobile/ContentView.swift` neni ani jeden vyskyt `UIScreenEdgePan` a `git log`
toho souboru zadny takovy commit nema. 27. 8. proto jiná session resila tentyz problem
znovu a nezavisle. Detail: [[doc-system-strategie-ios-gesto-zpet-dve-naraz]] a
[[doc-system-strategie-ios-gesto-zpet-screen-edge-pan]].

**Posledni prokazatelny prenos z Macova repa do STRATEGIE je z 24. 8. 2026** (commit
`24e85a73`, verze 1.85 / build 85). Vse, co na Macu vzniklo po tomto datu, **je potreba
pred opustenim Macova repa zkontrolovat a prenest** - jinak se ta prace ztrati.
Znama polozka: `5952e30` (gesto, 26. 8.) - ta se **prenaset nemusi**, protoze rozhodnuti
c. 1 vybralo jednodussi variantu, ktera uz v repu STRATEGIE je (commit `42042088`, 28. 8.).

## Co z toho plyne pro praci

- **Nova prace na iOS appce jde primo do `APP/iOS` v repu STRATEGIE.** Zadny prenos.
- Kontrola "co je na Macu navic" **jde udelat jen na Macu** - z Windows stroje neni na ten
  repos videt (neni tam `gh` a repos je mimo tenhle projekt).
- Dokud Macuv repos neni vyprazdneny a odepsany, plati: **nez cokoli na iOS zmenis, over
  `git log` prislusneho souboru a projdi znalosti na "iOS"**. To, ze neco neni v repu
  STRATEGIE, neznamena, ze to nikdo neudelal.
- Historicky duvod, proc dva repy vznikly: slouceni PR na GitHubu neslo (prihlaseny ucet
  ma na repu jen pravo cteni), takze se obsah prenasel rucne pres most - viz
  `doc-system-strategie-nasazeni-obsahu-pr-pres-most-kdyz-nejde-sloucit`.

