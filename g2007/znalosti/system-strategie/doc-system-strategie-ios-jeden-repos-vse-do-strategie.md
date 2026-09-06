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
pred opustenim Macova repa zkontrolovat a prenest** - jinak se ta prace ztrati. Znama
polozka: `5952e30` (gesto, 26. 8.) - ta se **prenaset nemusi**, protoze rozhodnuti c. 1
vybralo jednodussi variantu, ktera uz v repu STRATEGIE je (commit `42042088`, 28. 8.).

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

## ✅ MIGRACE DOKONCENA 6. 9. 2026

Provedeno na zadost Jirky Honomichla („chci to sjednotit hned") podle navodu
`MAC_NASTAVENI_STRATEGIE.md` v sitove slozce `_pro MAC`:

1. **Zkontrolovano, co je v `cz.strategie.mobile` (na Macu, cesta k .git je
   `cz.strategie.mobile/mobile`) navic po 24. 8. 2026:** `git log --oneline --since=2026-08-24`
   ukazal jen `5952e30` (gesto zpet - **nema se prenaset**, viz vyse) a `a2ac5af`
   (jen zapis do CLAUDE.md dokumentujici tu same opravu gesta, zadny kod navic). Necommitnuty
   soubor `POKRACOVANI_SESSION.md` (pracovni handoff poznamka, sam sebe oznacuje jako
   "necommitovat, docasne") obsahuje uz vyresene polozky (banner aktualizace - nasazeno
   pres g2007.soubor, gesto zpet - vyreseno jinak dle tohoto rozhodnuti) a par OTEVRENYCH,
   ktere se ale netykaji iOS/gitu: strop u zadosti o dovolenou (ceka na Jirkovu odpoved),
   pristup k Odvozum (role "vedouci vyroby", ceka na odpoved), a nepotvrzeny nález "PIN po
   navratu appky neni skryty hvezdickami" (nenalezeno v kodu, potreba overit na zarizeni).
   **Zaver: nic z Macova repa nepotrebuje prenest do STRATEGIE.**
2. **`git push` z Macu do STRATEGIE opraven a overen** - viz
   `doc-system-strategie-most-spousteni-na-macos` (sekce „STRATEGIE_GIT_PAT doplnen"). Timto
   se zaroven konecne nahral commit `f872b5e8` visici lokalne od 10. 8. 2026.
3. **Stary Macuv repozitar `cz.strategie.mobile` bude prejmenovan na
   `_ARCHIV_cz.strategie.mobile_2026-09-06`** (nemaze se, jen prestava byt aktivnim pracovnim
   adresarem) - Xcode se od te chvile otevira vyhradne
   `~/Projekty/STRATEGIE/STRATEGIE-repo/APP/iOS/mobile.xcodeproj`.
4. **Rozdelana prace ceka dal:** build 1.86 (`doc-system-strategie-ios-1-86-spodni-pruh-build-na-macu`)
   se ted sestavi primo z `APP/iOS` v repu STRATEGIE, kde uz kod je (overeno: `MARKETING_VERSION
   = 1.86`, `CURRENT_PROJECT_VERSION = 86`, `contentInsetAdjustmentBehavior = .never` pritomne).

