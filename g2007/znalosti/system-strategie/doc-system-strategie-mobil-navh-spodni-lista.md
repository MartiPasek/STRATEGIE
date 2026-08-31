# Mobil: vyska spodni listy (--navh) - obsah nesmi pocitat s pevnou rezervou

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ## AKTUALIZACE 28. 8. 2026 - spodni lista uz ma jen JEDEN pruh
>
> **Pravidlo teto znalosti PLATI DAL** (nikdy pevna rezerva, vzdy `var(--navh, 65px)`) -
> a `--navh` se po zmene spravne prepocitalo, overeno zive.
> Zmenil se ale **pocet pruhu**, ktere tabulka nize popisuje: pruh "<- Zpet" (`#bnavback`)
> se uz nezobrazuje nikde (ani v prohlizeci) a extra pruhy zmizely z obrazovky Aplikace.
> Spodek Aplikaci tim klesl ze 178 px na 65 px. Na Firme zustava lista skupin (`#bnavx2`)
> a nad ni zatim i prazdny `#bnavx1`.
> Detail, duvody a pasti: [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]]

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
| `#bnavx1` + `#bnavx2` extra listy | ruzne | ~~na obrazovce Aplikace / Firma~~ -> **od 28. 8. 2026 uz jen Firma** (lista skupin) |
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

## Otevrene (NERESENO, mimo schvaleny rozsah)

`30_contacts_settings.js:259` a `72_migrace_sw_isds.js:3` maji iframe
`calc(100vh - 56px)` - s listou 117 px jim spodek nejspis take mizi pod listou.
Neoveřeno, neresi se - vyzaduje vlastni rozhodnuti (iframe scrolluje sam).

## Overeni (nasazeno + zkontrolovano zive v prohlizeci)

- Ukoly: rezerva -11 px -> **+41 px**, `elementFromPoint` na spodku tlacitka vraci
  tlacitko (ne listu), klik otevre formular "Novy ukol"
- Ukoly z Centraly, Vyroba - konzole: rezerva 40 px
- Dochazka: otevre se a funguje
- Konzole prohlizece bez chyb; syntaxe JS overena `node --check` na sestavenem
  mobile.html pred i po

## Proces

Podnet Jirka -> diagnoza C28 -> navrh -> Marti-AI posoudila a schvalila pristup
(msg 11693, doporucila opravit vsechna mista najednou, `--appvh` z visualViewport
az kdyby se po nasazeni projevil jitter) -> Marti-AI odmitla schvalit sama
("zasah do zive appky schvaluje clovek-rodic") -> Marti na dovolene ->
schvalila **Kristyna 29.7.2026 14:18** e-mailem ("Schvaluji").

Souvisi: [[doc-system-strategie-mobil-login-pending-user]]

