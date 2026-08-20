# iOS appka: build, upload do App Store a gotchy (aktualizovano 19. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS appka STRATEGIE Mobil - build, upload a gotchy
> oblast: system-strategie · Jirka (C28) + Claude, 10. 8. 2026, **aktualizovano 19. 8. 2026**
> Overeno pri vydani 1.80 (build 3) a 1.84 (build 84).

## 1. Upload do App Store Connect jde cely z CLI
Neni potreba Xcode GUI, heslo ani ASC API klic - Xcode ma na Jirkove Macu ulozeny ucet, takze
`-allowProvisioningUpdates` si sam doplni distribucni certifikat i profil.

```sh
xcodebuild -project mobile.xcodeproj -scheme mobile -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/mobile.xcarchive \
  -allowProvisioningUpdates archive
xcodebuild -exportArchive -archivePath build/mobile.xcarchive \
  -exportPath build/upload -exportOptionsPlist build/ExportOptions-upload.plist \
  -allowProvisioningUpdates
```

V `ExportOptions-upload.plist` je klicove **`destination = upload`**; `export` jen vyrobi lokalni
IPA. Dalsi klice: `method=app-store-connect`, `teamID=D3Y6Y63UMA`, `signingStyle=automatic`,
`uploadSymbols=true`.

**Gotchy:**
- `xcodebuild` vyzaduje plny Xcode. Kdyz `xcode-select -p` vraci `CommandLineTools`, nepostavi
  se nic; prepnuti chce `sudo`, ktere Claude Code nema jak zadat - musi clovek
  (Xcode -> Settings -> Locations).
- **Pri spousteni na pozadi pouzivat ABSOLUTNI cesty** - relativni `-exportOptionsPlist`
  selze na "no such file" (19. 8. 2026).
- **Export compliance:** v projektu je `INFOPLIST_KEY_ITSAppUsesNonExemptEncryption = NO`,
  takze se Apple od buildu 4 neptá.

## 2. PODEPISOVANI: archiv lze, IPA je pravda (19. 8. 2026)
`xcodebuild archive` podepise vyvojovym profilem, takze archiv ma
`aps-environment = development` a `get-task-allow = true`. **To NENI chyba** - `exportArchive`
s `method: app-store-connect` prepodepise distribucnim profilem na **`production`** /
`get-task-allow = false`. **Kontrolovat az na IPA, ne na archivu:**
```sh
codesign -d --entitlements :- Payload/mobile.app
```
Bez teto kontroly hrozi vydat appku, ktere notifikace v ostre verzi nefunguji.

## 3. INSTALACE NA FYZICKY TELEFON (19. 8. 2026)
**`devicectl` funguje az od iOS 17.** Na starsim zarizeni (iPhone X / iOS 16.7) hlasi
`pairingState: unsupported` a `xcodebuild -showdestinations` telefon vubec neukaze - vypada to
jako chyba parovani, ale neni. Funkcni cesta je **`ios-deploy`** (brew):
```sh
ioreg -p IOUSB -l -w0 | grep -i "USB Serial Number"      # UDID telefonu
xcodebuild ... -configuration Debug -destination 'platform=iOS,id=<UDID>' build
ios-deploy --id <UDID> --bundle build-dev/.../mobile.app --noninteractive --debug --no-wifi
```
`--debug` streamuje `NSLog` do konzole - tak se cte i device token pro test notifikaci.

## 4. App Store Connect: odeslani je DVOUKROKOVE (19. 8. 2026)
Tlacitko **"Add for Review"** verzi jen prida do panelu **Draft Submission**. Teprve
**"Submit for Review"** v tom panelu ji skutecne odesle (pak stav `Waiting for Review`,
"1 Item Submitted", az 48 h na posouzeni). Kdo skonci u prvniho tlacitka, mysli si, ze odeslal,
a appka lezi neodeslana.

## 5. PAST dvou ContentView.swift (VYRESENO 19. 8. 2026)
V `APP/iOS` lezely dve kopie; kompiluje se **`APP/iOS/mobile/ContentView.swift`** (projekt ma
`PBXFileSystemSynchronizedRootGroup` s `path = mobile`). Commit `73a06f1d` (12. 6.) doplnil
marker `applicationNameForUserAgent` jen do te referencni - do vydane appky se nedostal skoro
dva mesice. **Osirela kopie uz v `origin/main` NENI**, past uzavrena. Obecne pouceni plati:
pred editaci over, ktery soubor je v build targetu.

## 6. Co z pomalosti appky plati pro iOS
Puvodni rozbor (`doc-system-strategie-mobilni-appka-vykon-async-most`) mluvil o synchronnim JS
mostu - ten ma **jen Android**, iOS jede na async `fetch()`, takze se ho netyka.
**19. 8. 2026 se ale zmerilo neco jineho a zavaznejsiho:** server sam se zadrhava a stoji 39 %
casu, coz brzdi obe platformy i web na pocitaci. Viz
`doc-system-strategie-server-zadrhavani-mereni`.

**GOTCHA:** git NENI zdroj pravdy pro frontend appky - `mobile_parts/*.js` a `mobile.html` na
disku jsou stale projekce, ostry kod zije v `g2007.soubor`.

## 7. Verzovani
iOS `MARKETING_VERSION` se drzi cisla Android appky. Stav 19. 8. 2026: ziva **1.80 (build 3)**,
**1.84 (build 84) odeslana ke schvaleni**. 1.83 (build 83) zustala v TestFlightu neodeslana,
jeji obsah je v 1.84. Pri kazdem uploadu zvysit `CURRENT_PROJECT_VERSION`; pristi = **85**.
`CFBundleDisplayName` musi byt nastaveny, jinak se appka uzivatelum jmenuje podle targetu
(do 1.83 se jmenovala "mobile").

## 8. Prava na sdilenem repu
Ucet `GHubGeorge` (Jirka) ma na `MartiPasek/STRATEGIE` jen `pull`, ne `push`. Zadny PAT to
neobejde - token neda prava, ktera ucet nema. Funkcni cesta: **fork + pull request**.

