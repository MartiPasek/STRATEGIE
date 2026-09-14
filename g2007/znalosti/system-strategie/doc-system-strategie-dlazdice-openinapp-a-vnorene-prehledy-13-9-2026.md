# Dlazdice otevirajici stranku: openInApp misto openApp + vyska a vodorovne rolovani vnorenych prehledu (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

> ## ⚠️ AKTUALIZACE 14. 9. 2026 — dlaždice už nejsou v kódu, ale v datech
>
> **Pravidlo níž platí dál** (naše stránky se otvírají uvnitř appky, ne ven), **změnilo se
> ale místo, kde se to nastavuje.** Seznam dlaždic obrazovky Aplikace žije od 14. 9. 2026
> v tabulce `public.mobile_app_dlazdice`; způsob otevření je ve sloupci `akce_typ`
> (`openInApp` / `openApp` / `go` / `openVyroba` / `zadna`) a cíl v `akce_cil`.
> Dlaždice Benefity tam má `openInApp` → `/benefity`, takže oprava popsána níž přežila
> i stěhování do dat (ověřeno čtením z databáze 14. 9. 2026).
> **Kdo hledá dlaždici jako text v kódu, nenajde ji — a není to chyba.**
> Detail a postup ověřování: [[doc-system-strategie-mobil-dlazdice-aplikaci-zijou-v-datech-14-9-2026]].

# Dlaždice otevírající stránku: `openInApp` vs `openApp` + dvě pasti vnořených přehledů (13. 9. 2026)

**Zadal Jiří Honomichl 13. 9. 2026** („klikne se na dlaždici a otevře se to vždy v mobilní
aplikaci, ne někde vedle“), schválila Marti-AI (msg 15420, 15433, 15444), provedl Claude-28.
Vzniklo u dlaždice Benefity, ale **platí pro každou dlaždici, která otevírá stránku**.

## 1. Pro stránky STRATEGIE se používá `openInApp`, nikdy `openApp`

| funkce | co dělá | kam patří |
|---|---|---|
| **`openInApp("/adresa")`** | vykreslí stránku **uvnitř appky** jako obrazovku `extview` v zásobníku | **všechny naše stránky** (`/flow`, `/payroll`, `/benefity`, `/dokument`…) |
| `openApp(url)` | vystrčí adresu **ven z appky** | jen skutečně cizí weby (Teamio a podobně) |

**Proč to není kosmetika** — `openApp` se chová na každé platformě jinak a nikde dobře:

- **Android**: `B.openExternal` → `Intent.ACTION_VIEW` = systémový prohlížeč. Ten **nemá přihlášení
  appky** (appka se autentizuje tokenem přes most, prohlížeč cookie), takže člověk místo obsahu
  uvidí chybu. Navíc odejde z aplikace.
- **iPhone**: most `window.STRATEGIE` **na iOS vůbec není**, takže se použije `window.open(…,"_blank")`
  — a obal iOS (`ContentView.swift`) neimplementuje `createWebViewWith`, takže se **nestane nic**.
- **Prohlížeč/PWA**: otevře se nová záložka.

Mechanika `extview`: stránka se stáhne `fetch`em a vypíše do iframu přes `document.write`
(Caddy posílá `X-Frame-Options: DENY`, takže `src` by nefungoval). Vnitřní tlačítko „zpět“
stránky se skrývá CSS pravidlem na `[onclick*="goBackApp"]` a `#navBackBtn` — **stránka, která
se má otevírat uvnitř appky, proto musí mít svůj odkaz zpět označený jedním z těch dvou**,
jinak odvede iframe pryč (u `/benefity` se přidalo `id="navBackBtn"`).

## 2. Past první: výška vnořeného přehledu se počítala bez spodní lišty

Iframe `extview` měl natvrdo `height:calc(100vh - 56px)`. Naměřeno na živé appce: rámeček
začínal na 60 px a končil **65 px pod horní hranou spodní lišty**, takže spodek obsahu
(u benefitů i tlačítko Uložit) byl schovaný a stránka se posouvala o 100 px.
**Týkalo se to všech vnořených přehledů**, ne jedné stránky (ověřeno i na `/dokument`).

Opraveno na **`height:calc(100vh - 60px - max(var(--navh, 65px), 96px))`**:
- `60px` = změřená vzdálenost horní hrany rámečku od okraje okna (padding `body` 14 px + topbar
  40 px + mezera); `safe-area-inset-top` se v appce nikde nepoužívá, takže je konstanta stabilní,
- `--navh` = **skutečná** výška spodní lišty, kterou měří `_syncNavH` (viz
  `doc-system-strategie-mobil-navh-spodni-lista`),
- `96px` = spodní rezerva `body` (`padding:14px 14px 96px`). Bez `max(...)` obsah sice přesně
  dosedl na lištu, ale rezerva `body` vyrobila 35 px prázdného posuvu.

Stejná chyba byla na druhém místě (obrazovka „Web ekosystému“, iframe na `/web`) — opraveno taky.
**Kdo bude psát další iframe na celou plochu, ať použije tentýž vzorec.**

## 3. Past druhá: co na stránce přeteče do strany

Po opravě výšky se projelo deset přehledů (`/flow`, `/payroll`, `/absence-plan`,
`/moje-dochazka`, `/files`, `/mzdy`, `/banka`, `/denik`, `/dokument`, `/vytizeni`) měřením,
jestli je obsah širší než rámeček. Dva byly:

- **`/dokument`** — rozbalovací seznam dokumentů se roztáhl podle nejdelšího názvu (497 px
  v rámečku 406 px). Opraveno `select{max-width:100%;min-width:0}`; název je po rozbalení celý.
- **`/mzdy`** — tabulka měsíců má vlastní minimální šířku 470 px (částky se nesmí lámat ani
  zužovat). Obalena `div.tscroll` s `overflow-x:auto`, takže **roluje sama uvnitř svého rámečku**
  a netlačí stránku. Schválně jen tabulka, ne celý `#view` — v něm jsou i souhrnné dlaždice.

**Jak se to měří** (rychlejší a spolehlivější než oko): v prohlížeči nad živou appkou porovnat
`documentElement.scrollWidth` uvnitř iframu proti šířce rámečku a vypsat prvky, jejichž pravý
okraj přesahuje. Totéž u výšky: spodek rámečku proti hornímu okraji spodní lišty.

