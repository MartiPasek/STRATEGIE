# iOS appka STRATEGIE Mobil - build, upload a gotchy (aktualizovano 24.8.2026 - vyprsele prihlaseni pri uploadu)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# iOS appka STRATEGIE Mobil - build, upload a gotchy

> oblast: system-strategie · Jirka (C28) + Claude, 10. 8. 2026, **aktualizovano 24. 8. 2026**
> Overeno pri vydani 1.80 (build 3), 1.84 (build 84) a 1.85 (build 85).

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

V `ExportOptions-upload.plist` je klicove **`destination = upload`**; `export` jen vyrobi
lokalni IPA. Dalsi klice: `method=app-store-connect`, `teamID=D3Y6Y63UMA`,
`signingStyle=automatic`, `uploadSymbols=true`.

**Gotchy:**
- `xcodebuild` vyzaduje plny Xcode. Kdyz `xcode-select -p` vraci `CommandLineTools`, nepostavi
  se nic; prepnuti chce `sudo`, ktere Claude Code nema jak zadat - musi clovek
  (Xcode -> Settings -> Locations).
- **Pri spousteni na pozadi pouzivat ABSOLUTNI cesty** - relativni `-exportOptionsPlist`
  selze na "no such file" (19. 8. 2026).
- **Export compliance:** v projektu je `INFOPLIST_KEY_ITSAppUsesNonExemptEncryption = NO`,
  takze se Apple od buildu 4 neptá.

## 1b. GOTCHA (24.8.2026): vyprsele prihlaseni Xcode uctu vypada jako zaseknuty upload

`xcodebuild -exportArchive` s `destination: upload` muze na kroku **„Waiting for App Store
Connect analysis response"** viset **10+ minut beze zmeny a bez sitoveho spojeni** (overeno
`sample <pid>` — hlavni vlakno cekalo v `_dispatch_semaphore_wait_slow` uvnitr
`DVTITunesConnect uploadApplicationWithPath:...`, vedlejsi `NSURLConnectionLoader` vlakno bylo
idle). **Neni to zaseknuti** — je to vyprsela relace Apple uctu v Xcode, kterou proces neumi
sam obnovit. Prokazatelne v `ContentDelivery.log` z `xcdistributionlogs`:

```
GET UPLOAD STATE (ASSET_DESCRIPTION) RESPONSE: status code: 401 (unauthorized)
"detail": "Authentication credentials are missing or invalid..."
GET UPLOAD STATE: failed to reauthenticate:
  DVTITunesSoftwareServiceFoundation.AuthContextDelegateError.reauthenticationNotSupported
```

**Zadny viditelny dialog se pri tom neukaze** — ani na obrazovce Macu, ani jako 2FA push na
jine zarizeni (overeno, zadne nebylo). **Reseni:** otevrit Xcode → Settings → Accounts,
kliknout na ucet a potvrdit/obnovit prihlaseni (napr. „Download Manual Profiles" nebo znovu
zadat heslo, pokud se o nej rekne). Po tomhle kroku dalsi pokus `xcodebuild -exportArchive`
projde bez chyby (`UPLOAD SUCCEEDED with no errors`) — overeno 24.8.2026 na uploadu buildu 85.

**Diagnostika, kdyz se to stane priste:** `ps aux | grep xcodebuild` — pokud CPU cas procesu
dlouho neroste a `lsof -p <pid> -i` neukazuje zadne spojeni, je to tenhle pripad, ne skutecne
zaseknuti. `sample <pid> 2` a hledat `DVTITunesConnect` / `reauthenticationNotSupported`
v ceste vlakna to potvrdi bez nutnosti cekat dalsich 10 minut.

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
`pairingState: unsupported` a `xcodebuild -showdestinations` telefon vubec neukaze - vypada
to jako chyba parovani, ale neni. Funkcni cesta je **`ios-deploy`** (brew):

```sh
ioreg -p IOUSB -l -w0 | grep -i "USB Serial Number"      # UDID telefonu
xcodebuild ... -configuration Debug -destination 'platform=iOS,id=<UDID>' build
ios-deploy --id <UDID> --bundle build-dev/.../mobile.app --noninteractive --debug --no-wifi
```

`--debug` streamuje `NSLog` do konzole - tak se cte i device token pro test notifikaci.

⚠️ **GOTCHA (24.8.2026): telefon se muze behem instalace sam uzamknout** (auto-lock) —
`run` pak selze na *„Unable to launch … because the device was not, or could not be,
unlocked"*, nebo appka nabehne, ale zustane na pozadi bez logu. Telefon pred kazdym spustenim
odemknout a nechat displej rozsviceny.

## 4. App Store Connect: odeslani je DVOUKROKOVE (19. 8. 2026)

Tlacitko **"Add for Review"** verzi jen prida do panelu **Draft Submission**. Teprve
**"Submit for Review"** v tom panelu ji skutecne odesle (pak stav `Waiting for Review`,
"1 Item Submitted", az 48 h na posouzeni). Kdo skonci u prvniho tlacitka, mysli si, ze
odeslal, a appka lezi neodeslana.

**Postup od zalozeni verze (overeno 24.8.2026, verze 1.85):**
1. Na strance existujici verze (`iOS App` sekce vlevo) kliknout na modre **„+"** vedle
   nadpisu „iOS App" → dialog „New Version" → zadat cislo → „Create".
2. Vyplnit „What's New in This Version" (povinne pro odeslani).
3. V sekci „Build" → „Add Build" → vybrat nahrany build (podle cisla, napr. 85) → „Done".
4. **„Save"** (jinak zustane „Add for Review" sede/disabled).
5. **„Add for Review"** → otevre se panel „Draft Submission" s polozkou a tlacitkem
   „Submit for Review".
6. **„Submit for Review"** → potvrzeni „1 Item Submitted", verze v levem panelu zmeni stav
   na „Waiting for Review".
7. **Overit dvema zpusoby:** banner „musis vzit verzi zpet z review, abys mohl nahrat novy
   build" (zobrazuje se jen u opravdu odeslane verze) + zaznam v `App Review` → `Submissions`
   s aktualnim casem a stavem „Waiting for Review".

## 5. PAST dvou ContentView.swift (VYRESENO 19. 8. 2026)

V `APP/iOS` lezely dve kopie; kompiluje se **`APP/iOS/mobile/ContentView.swift`** (projekt ma
`PBXFileSystemSynchronizedRootGroup` s `path = mobile`). Commit `73a06f1d` (12. 6.) doplnil
marker `applicationNameForUserAgent` jen do te referencni - do vydane appky se nedostal skoro
dva mesice. **Osirela kopie uz v `origin/main` NENI**, past uzavrena. Obecne pouceni plati:
pred editaci over, ktery soubor je v build targetu.

## 6. Co z pomalosti appky plati pro iOS

Puvodni rozbor (`doc-system-strategie-mobilni-appka-vykon-async-most`) mluvil o synchronnim
JS mostu - ten ma **jen Android**, iOS jede na async `fetch()`, takze se ho netyka.
**19. 8. 2026 se ale zmerilo neco jineho a zavaznejsiho:** server sam se zadrhava a stoji
39 % casu, coz brzdi obe platformy i web na pocitaci. Viz
`doc-system-strategie-server-zadrhavani-mereni`.

**GOTCHA:** git NENI zdroj pravdy pro frontend appky - `mobile_parts/*.js` a `mobile.html`
na disku jsou stale projekce, ostry kod zije v `g2007.soubor`.

## 7. Verzovani iOS

`MARKETING_VERSION` se drzi cisla Android appky, pokud jde o spolecnou zmenu; ciste iOS opravy
(napr. odznak, 24.8.2026) mohou jit ve vlastnim cisle bez cekani na Android. Stav 24.8.2026:
ziva **1.84**, **1.85 (build 85) odeslana ke schvaleni** (24.8.2026 10:47 CEST — oprava
odznaku na ikone, viz `doc-system-strategie-ios-odznak-na-ikone-appky-cislo-ze-serveru`).
Pri kazdem uploadu zvysit `CURRENT_PROJECT_VERSION`; pristi = **86**.
`CFBundleDisplayName` musi byt nastaveny, jinak se appka uzivatelum jmenuje podle targetu
(do 1.83 se jmenovala "mobile").

## 8. Prava na sdilenem repu

Ucet `GHubGeorge` (Jirka) ma na `MartiPasek/STRATEGIE` jen `pull`, ne `push`. Zadny PAT to
neobejde - token neda prava, ktera ucet nema. Funkcni cesta: **fork + pull request**.
Tenhle bod se **iOS wrapper repa (`cz.strategie.mobile`) netyka** — tam ma Jirka plny pristup
pod vlastnim uctem, push jde primo do `main`.

