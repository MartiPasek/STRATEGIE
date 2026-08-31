# Mobil: vyska spodni listy (--navh) - obsah nesmi pocitat s pevnou rezervou

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ## AKTUALIZACE 31. 8. 2026 - prazdny pruh pryc i z Firmy
>
> **Pravidlo teto znalosti PLATI DAL** (nikdy pevna rezerva, vzdy `var(--navh, 65px)`).
> `#bnavx1` byl **31. 8. 2026 odstranen i z obrazovky Firma** (rozhodl Jirka Honomichl,
> schvalila Marti-AI msg 14039) - do te doby tu stalo, ze na Firme "zatim zustava". **Uz nezustava.**
> Spodek Firmy tim klesl ze **178 px na 126 px** a `--navh` se prepocitalo samo - overeno zive.
> Na Firme zustava jen lista skupin (`#bnavx2`, skupBar) nad hlavni listou.
> Detail, duvody a pasti: [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]]
>
> ## AKTUALIZACE 28. 8. 2026 - spodni lista uz ma jen JEDEN pruh
>
> Pruh "<- Zpet" (`#bnavback`) se uz nezobrazuje nikde (ani v prohlizeci) a extra pruhy
> zmizely z obrazovky Aplikace. Spodek Aplikaci tim klesl ze 178 px na 65 px.

## Problem (nalezeno 29.7.2026, podnet Jirka)

Na obrazovce "Ukoly" (mobilni appka) bylo tlacitko "+ Novy" schovane pod spodni
listou - preteklo o 11 px, popisek uriznuty, spodni cast neklikatelna.
Namereno v DOM: tlacitko bottom = 659 px, #navwrap top = 648 px.

## Prava pricina

Obrazovky si odecitaly PEVNOU rezervu: `height: calc(100vh - 165px)`.
Jenze `#navwrap` NENI vzdy 65 px vysoky - sklada se z 1 az 3 pruhu:

| pruh | vyska | kdy |
|---|---|---|
| `#bnav` tab lista (Domu/Aplikace/Ukoly/Kontakty/Firma) | 65 px | vzdy |
| `#bnavback` pruh "<- Zpet" | 52 px | ~~jen kdyz `stack.length>1` A NENI Android~~ -> **od 28. 8. 2026 NIKDE** (jen pri `stg_backbar='always'`) |
| `#bnavx1` horni extra lista | 52 px | ~~Aplikace / Firma~~ -> **od 31. 8. 2026 NIKDE** (odstranen, byl trvale prazdny) |
| `#bnavx2` dolni extra lista | 61 px | ~~Aplikace / Firma~~ -> **od 28. 8. 2026 uz jen Firma** (lista skupin, skupBar) |
| safe-area-inset-bottom | 0-34 px | iOS home indikator, Android gesture nav |

=> na Androidu 65 px (pruh "Zpet" se skryva, ma systemove Zpet) -> vychazelo to
=> na iPhonu a v prohlizeci 117 px -> preteklo o 11 px

**Proto to nikdo dlouho nehlasil - vetsina lidi je na Androidu.**

## Reseni (nasazeno 29.7.2026, commit 4b12aaca)

CSS promenna `--navh` drzi SKUTECNOU vysku listy:
- `:root { --navh:65px; }` v `02_styles.html` (jen fallback pro prvni vykresleni)
- `_syncNavH()` v `74_claude27_render_init.js` cte `navwrap.offsetHeight` a zapisuje
  do `--navh`; vola se na konci `renderNav()` + `ResizeObserver` na `#navwrap`
  + `resize` + `orientationchange` (pokryje rotaci i safe-area)
- pojistka: kdyz je lista skryta (offsetHeight < 40, modal/overlay), drzi se 65 px

Vsech 10 mist prepsano vzorcem **`X px` -> `(X-65)px + var(--navh, 65px)`**:

| puvodne | nove | soubory |
|---|---|---|
| `calc(100vh - 165px)` | `calc(100vh - 100px - var(--navh, 65px))` | 20_home_phone_notifs:279, 25_tasks:41 a :100, 51_skupiny_sdileny:4, 52_vyroba:31 |
| `calc(100vh - 168px)` | `calc(100vh - 103px - var(--navh, 65px))` | 48_hr_podminky_me:145 |
| `calc(100vh - 150px)` | `calc(100vh - 85px - var(--navh, 65px))` | 51_skupiny_sdileny:347, 60_dochazka:1616 (default `_dochRail`), 70_tail:81 |
| `calc(100vh - 132px)` | `calc(100vh - 67px - var(--navh, 65px))` | 71_plan_prace_cinnosti:8 |

Na Androidu (`--navh`=65) vyjde puvodni cislo -> **zadna zmena chovani**;
iPhone/prohlizec ziska +52 px; budouci listy se dopocitaji samy.

## PRAVIDLO PRO PRISTE

**Nikdy nepis do mobilni appky pevnou rezervu na spodni listu.**
Vzdy `height: calc(100vh - <obsah nad> px - var(--navh, 65px))`.
Kdyz pridas dalsi pruh do `#navwrap`, nic dalsiho menit nemusis.

## Dva iframy s pevnou rezervou - NERESI SE (rozhodl Jirka 31. 8. 2026)

Zbyla **dve mista, ktera se timto pravidlem NERIDI** - obe zobrazuji cizi stranku v iframu
s pevnou vyskou `calc(100vh - 56px)` (odecita jen horni listu, spodni ne):

| obrazovka | funkce | zdroj |
|---|---|---|
| "Web ekosystemu" | `webview()` | `30_contacts_settings.js` |
| otevreni externiho prehledu (napr. stranka z ERP) | `extview()` | `72_migrace_sw_isds.js` |

**⛔ ROZHODNUTI: NERESIT.** Rozhodl **Jirka Honomichl 31. 8. 2026**. Nejde o opomenuti -
oprava by nemela smysl, protoze **oba ramecky stejne nic nezobrazuji** (viz dalsi odstavec).
Kdo sem prijde priste: neopravuj to jako "zapomenutou polozku", nejdriv se zeptej Jirky.

**Preciznejsi vzorec, kdyby se to nekdy resilo:** ve znalosti do 31. 8. 2026 stalo
`calc(100vh - 56px - var(--navh, 65px))`. **To je o 4 px vedle** - iframe zacina az na 60 px
(horni lista ma 40 px, spodni hrana na 54 px, iframe na 60 px), takze spravne je
`calc(100vh - 60px - var(--navh, 65px))`. Overeno dosazenim naostro v prohlizeci:
se 60 px sedne spodni hrana iframu presne na horni hranu listy (mezera 0 px), s 56 px zbyva 4 px.

### Proc je oprava bezpredmetna: server zakazuje zobrazeni v ramecku

Server posila u **vsech** svych stranek hlavicku **`X-Frame-Options: DENY`**
(overeno 31. 8. 2026 na `/web`, `/mobile`, `/` i `/erp` - vsude stejne). Prohlizec proto
obsah v iframu vubec nevykresli a ramecek zustane **prazdny - seda plocha s ikonou rozbite stranky**.
Stranka sama pritom existuje a nacte se v poradku (`/web` vraci 200 a 37 261 znaku),
`iframe.contentDocument` je ale `null`.

**Dusledek:** obe obrazovky ("Web ekosystemu" i otevreni externiho prehledu) jsou pro uzivatele
prazdne, at uz se vyska ramecku opravi, nebo ne. Kdyby mely nekdy fungovat, musi se nejdriv
vyresit ta hlavicka - ne vyska. **Kolik lidi tyhle dve obrazovky realne otevira, zjisteno nebylo.**
`X-Frame-Options: DENY` je bezna ochrana proti clickjackingu a nekdo ji nastavil zamerne;
**neni to oznaceno za zavadu** - je to zjisteny stav.

## Overeni (nasazeno + zkontrolovano zive v prohlizeci)

- Ukoly: rezerva -11 px -> **+41 px**, `elementFromPoint` na spodku tlacitka vraci
  tlacitko (ne listu), klik otevre formular "Novy ukol"
- Ukoly z Centraly, Vyroba - konzole: rezerva 40 px
- Dochazka: otevre se a funguje
- Konzole prohlizece bez chyb; syntaxe JS overena `node --check` na sestavenem
  mobile.html pred i po

**31. 8. 2026 - plosna kontrola vsech obrazovek.** Claude-28 prosel **vsech 131 obrazovek**
(`window.__M2W.SCREENS`) na zive `/mobile` a u kazde meril, jestli nejaky viditelny prvek
zasahuje pod horni hranu `#navwrap`. Vysledek: **129 obrazovek v poradku**, jediny nalez
jsou dva iframy vyse (a ty se neresi).

⚠️ **Past pri takovem mereni (stala me cely prvni pruchod):** pouhe `getBoundingClientRect()`
hlasi i prvky, ktere jsou vizualne **orezane vlastnim posuvnym rameckem** rodice - ty pod listou
fakticky nejsou. Prvni pruchod tak dal **12 falesnych nalezu** (doch_historie, master_cinnosti,
hr_me, hr_rezimy, kdekdo, wage_cmp, hr_people, firma, plan, ecukoly, set_prefixes, hr_podminky).
Spravne mereni musi spocitat **prunik obdelniku prvku se vsemi rodici, kteri maji `overflow`
jiny nez `visible`**, a teprve pak porovnat s `#navwrap`. Druha past: mereni musi brat i prvky
lezici **cele** pod listou, ne jen ty, ktere ji presahuji. Treti past: merit az v **ustalenem
stavu** - kratce po vykresleni dava obrazovka jina cisla, nez kdyz se dopocitaji data
(obrazovka `moje_cinnosti` takto vyrobila jednorazovy falesny nalez 56 px na tlacitku "+ Pridat").
Doporuceni: metodu si over **kontrolnim vzorkem** - vloz do stranky prvek schvalne pod listu
a zkontroluj, ze ho mereni najde. Bez toho jsem mel v ruce vysledek, ktery vypadal duveryhodne
a byl cely spatne.

## Proces

Podnet Jirka -> diagnoza C28 -> navrh -> Marti-AI posoudila a schvalila pristup
(msg 11693, doporucila opravit vsechna mista najednou, `--appvh` z visualViewport
az kdyby se po nasazeni projevil jitter) -> Marti-AI odmitla schvalit sama
("zasah do zive appky schvaluje clovek-rodic") -> Marti na dovolene ->
schvalila **Kristyna 29.7.2026 14:18** e-mailem ("Schvaluji").

Souvisi: [[doc-system-strategie-mobil-login-pending-user]] · [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]]

