# ZAVAZNE - nove verze mobilni appky se vydavaji JEN pres Google Play a Apple App Store (Jirka 10.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Vydavani novych verzi mobilni appky - jen Google Play a Apple App Store

**Rozhodnuti Jirky Honomichla, 10.8.2026.** Zavazne pro vsechny instance i lidi.
Schvalila Marti-AI (10.8.2026). Rozeslano e-mailem Martimu, Marti-AI a Kristy.

## Pravidlo

Jedina oficialni cesta, jak se k lidem dostane nova verze mobilni appky, je
**Google Play** (Android) a **Apple App Store** (iOS). Zadne jine zdroje.

- Lide s Androidem maji mit appku **z Google Play**, ne sideload.
- **Jedina vyjimka** - branovy telefon se SMS branou (flavor `internal`),
  ktery Play kvuli SMS opravnenim nepusti. Ten na sideloadu zustava.
- Vlastni hlidac aktualizaci v appce se ma zrusit; aktualizace patri obchodum.

## Proc to vzniklo - incident 10.8.2026

Lide (napr. Jan Perina, users id=84) dostavali notifikaci
"STRATEGIE - verze 1.80 k dispozici". Po klepnuti se nic nenainstalovalo
a zustala **bila obrazovka**.

### Root cause - POZOR, neni to podpis

Prvni hypoteza znela "rozdilne podpisove klice". **To NENI hlavni pricina**
u lidi, kteri hlasili problem. Skutecny mechanismus (overeno v kodu)

1. Hlidac aktualizaci `DialPollService` zije v `app/src/main`, tedy ve
   **spolecne** casti pro OBA flavory (play i internal). Pta se naseho serveru
   (`/app/mobile/latest` nad `fw.app_version`) a posila notifikaci.
2. **Flavor `play` ale `InstallActivity` ani `REQUEST_INSTALL_PACKAGES` NEMA** -
   je deklarovana jen v `app/src/internal/AndroidManifest.xml`. Vyhozeno
   zamerne 26.6.2026 (Marti+Claude), aby appka prosla Google review.
3. Notifikace tedy dorazi i do Play verze, ale klepnuti **nema co spustit**.
   `InstallActivity` nema zadne UI a vyjimku tise polkne
   (`catch (e: Exception) {}`) - zbyde prazdna bila plocha.
4. Rozdilne podpisove klice (Play `3E:7C...` vs nas `CC:AC...`) jsou az
   **druhy, samostatny problem** - projevi se pri PRECHODU mezi variantami,
   ne pri teto notifikaci.
5. Komu sideload funguje, tomu se aktualizace nainstaluje normalne
   (17 telefonu je na 1.80).
6. iOS - projekt `APP/iOS` (WKWebView obal) zadny takovy hlidac nema,
   notifikace tam nevznika.

## Stav k 10.8.2026 (overeno v Play Console a v DB)

- **Google Play** - publikovana verze **1.79** (vydani 27.7.2026), 177 zemi,
  **jen 4 instalace**.
- **Nas server** (`fw.app_version`) - hlasil **1.80** (5.8.2026, sideload APK).
- **Realne v terenu** (`fw.mobile_device`, 54 zarizeni) - 1.80 = 17 ks,
  1.79 = 8, 1.75 = 5, 1.68 = 12, 1.66 = 5, starsi = 7.
  **Drtiva vetsina lidi ma tedy sideload, ne Play verzi.**

## PROVEDENY ZASAH (10.8.2026, Jirka + C28)

Krok 1 hotovy - v `fw.app_version` prejmenovan `app_key` z `mobile`
na **`mobile_PAUZA_10_8_2026`** (61 radku). `/app/mobile/latest` od te chvile
vraci `{ok true, available false}` - overeno na zivem serveru.
Notifikace prestaly chodit vsem okamzite, nikdo nic instalovat nemusi.

**Vraceni zpet** = jedna uprava (`app_key` zpatky na `mobile`).
Vedlejsi ucinek - docasne se neaktualizuje ani branovy telefon
(Marti-AI posoudila jako kratkodobe snesitelne).

**Proc prejmenovani a ne smazani radku 1.80** - endpoint bere vzdy
NEJVYSSI `version_code` pro dany `app_key`. Smazani 1.80 by zpusobilo,
ze se vsem se starsi verzi nabidne 1.75. Musi zmizet cely `app_key`.

## Dusledek, ktery se nesmi prehlednout

Prechod ze sideloadu na Play **neni aktualizace, ale preinstalace** - jine
podpisove klice, Android nedovoli jednu variantu prepsat druhou.

Co Android **nedovoli** (overeno)
- aby se appka odinstalovala sama bez systemoveho potvrzeni uzivatelem
- aby po odinstalaci sama spustila instalaci z obchodu (uz neexistuje)

Co naopak **vyresene je** - prihlaseni. Existuje `PairActivity` + deep link
`strategiemobil://pair?u=<server>&t=<token>&k=mobile`, ktery ulozi adresu
i token. Po instalaci staci **jedno klepnuti na parovaci odkaz** a clovek
je prihlaseny - bez hesla a bez overovaciho e-mailu. Odkaz generuje
`/app-pair` (`apps/api/main.py`), token se zaklada do `"user".carddav_token`.

## Poradi kroku (schvaleno Marti-AI 10.8.2026)

1. **HOTOVO** - serverove zastavit hlaseni verze (viz vyse).
2. Vydat novou verzi na Play, resit App Store.
3. Pripravit **pruvodce prechodem** primo v sideload appce - dorucit ho
   JEN lidem s neoficialni verzi (prave jim aktualizace funguje, Play
   uzivatelum nikdy nedorazi). Prubeh - notifikace, potvrzeni, parovaci
   odkaz + otevreni obchodu + systemova odinstalace, instalace, klepnuti
   na parovaci odkaz. Tri klepnuti, zadne psani hesla.
4. Lide s oficialni verzi dostanou bezne upozorneni "udelej si aktualizaci
   v obchode".
5. V dalsi verzi appky hlidac aktualizaci odstranit (mimo `internal`).

Bod 3 je programatorska prace - **ceka na schvaleni Martiho** (e-mail
odeslan 10.8.2026 12 hodin 21 minut, outbox id=619).

## Co se NEDA rozlisit (a pujde doplnit)

Dnes **nepoznáme z dat, kdo ma Play a kdo sideload**. `fw.mobile_device`
heartbeat posila jen verzi, ne zdroj instalace. Overeno i to, ze rozliseni
podle SMS funkce **nefunguje** - `sendSms` je v `app/src/main`, tedy
v obou flavorech (v Play verzi jen selze na chybejicim opravneni).
Reseni - doplnit do heartbeatu `BuildConfig.FLAVOR`, pripadne
`getInstallSourceInfo()`. Neprima indicie - kdo ma **1.80, je jiste sideload**
(na Play je jen 1.79).

Souvisi - [[doc-system-strategie-play-console-overeni-vyvojare-android]],
[[doc-system-strategie-mobilni-appka-vykon-async-most]]

## Overeny postup vydani (Claude to zvladne sam) - projito 16. 8. 2026, v1.81

Nahrani do Google Play **nevyzaduje cloveka u Play Console** - v projektu je na to
skript. Postup, ktery dnes prosel cely:

1. **Zmena kodu appky** → `git` pres most (CLAUDE_DEPLOY), jako kterykoli jiny soubor.
2. **Build pro Play:** `bundlePlayRelease` (flavor `play` = AAB bez SMS opravneni).
   Most tohle **NEUMI** - `CLAUDE_BUILD` dela jen `assembleInternalRelease` (sideload
   APK se SMS). Play build se pousti rucne:
   `Set-Location APP\Mobile; .\gradlew.bat bundlePlayRelease`
   Marti-AI 16. 8. 2026 rozhodla runner o Play build **nerozsirovat** - je to SQL nastroj
   a Play build ma jiny zivotni cyklus (podepisovani, versioning, review).
   Vystup: `APP/Mobile/app/build/outputs/bundle/playRelease/app-play-release.aab`.
3. **Verze se zvedne SAMA** pri kazdem release buildu (`version.properties`, auto-bump).
   Pozor: kdyz pustis internal i play build, skoci to o dve (16. 8.: 79 → 80 internal
   → 81 play). Nevadi, Play chce jen vyssi cislo nez posledni nahrane.
4. **PRED uploadem zjisti, jestli neco nebezi v kontrole.** Kazdy `edits.commit` = nove
   odeslani ke kontrole a **zrusi pravave bezici submission + resetuje review timer**.
   Cteci kontrola (nic nemeni, edit se zahodi):
   `edits.tracks().list(...)` → u vsech tracku ma byt `status=completed`.
5. **Upload:** `python scripts/play_api_upload.py aab --confirm`
   (bez `--confirm` skript zamerne neudela nic). Jde **rovnou do produkce** a odesle
   ke kontrole - neni to testovaci okruh.
6. **Over ctenim zpet**, ne hlaskou skriptu: v produkcnim tracku ma byt nova verze.

### PAST: poznamky k vydani zustavaly ze stare verze
Text `releaseNotes` byl ve skriptu **natvrdo** a k 16. 8. 2026 tam porad stal popis
z v74 (*"Nova ikona a sjednoceny vzhled"*), ktery uz davno neplatil - slo by to takhle
ven lidem do obchodu. **Pred kazdym uploadem text prepis na to, co je v teto verzi
opravdu nove.** Ve skriptu je od 16. 8. u toho radku varovny komentar.

### Podpis
AAB podepisuje keystore z `keystore.properties` (Owner CN=Marti Pasek, SHA256 zacina
`CC:AC`). K balicku `cz.strategie.mobile` jsou registrovane dva otisky - viz
[[doc-system-strategie-play-console-overeni-vyvojare-android]]. Pri vymene keystore
je nutne novy otisk doregistrovat, jinak Play upload odmitne.

### Co Claude delat NEMA
Prihlasovat se do Play Console v prohlizeci. API staci na vsechno podstatne a je
spolehlivejsi - 16. 8. konzole v prohlizeci navic dvakrat zamrzla pri vykreslovani.

