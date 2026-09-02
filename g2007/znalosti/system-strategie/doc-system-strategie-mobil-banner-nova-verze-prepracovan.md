# Banner "Nova verze STRATEGIE" (26.8.2026) — CHOVANI ZRUSENO 2.9.2026, appka se uz sama neobnovuje ani nic neukazuje

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> # ⛔ CHOVÁNÍ POPSANÉ NÍŽE BYLO 2. 9. 2026 ZRUŠENO
>
> **Aplikace se při změně verze serverového kódu už SAMA NEOBNOVUJE a neukazuje žádný pruh
> ani hlášku.** Zrušeno na základě hlášení z provozu (Jirka Honomichl), schválila Marti-AI
> (msg 14245 a 14251).
>
> **Co konkrétně už NEPLATÍ z textu níže:**
> - žlutý pruh „Nová verze STRATEGIE" — **odstraněn**,
> - tichá aktualizace na domovské obrazovce (`_verHardReload` volaný z `_verTick`) — **odstraněna**,
> - hook v `render()`, který obnovoval stránku při návratu na domovskou obrazovku — **odstraněn**,
> - zelený pruh „Aktualizováno na novou verzi" — **odstraněn**,
> - příznak `_verPending` se už **nenastavuje**.
>
> Funkce `_verHardReload` v kódu zůstala, ale **nemá jediného volajícího**. Ruční cesta
> Nastavení → Vyčistit a načíst funguje dál (jde jinou funkcí, `clearAndReload`).
>
> **Proč se to zrušilo:** obnovení stránky lidi rušilo při práci — ztratili místo, kde byli
> (poloha žije jen v paměti), na sdíleném telefonu museli znovu zadat PIN a viděli hlášku.
> Nový obsah aplikace se od 2. 9. 2026 bere **tiše za běhu, bez obnovení stránky**.
>
> **Platný stav:** [[doc-system-strategie-mobil-ticha-aktualizace-obsahu-za-behu]]
>
> ⚠️ **Text níže se nechává schválně** — je v něm doložené, jak se to chovalo do 2. 9. 2026,
> a hlavně **gotcha o tom, že se hlídala verze serverového kódu, ne obsah appky**. Ta zůstává
> platná jako popis příčiny, proč publikace obsahu dlouho neudělala v appce vůbec nic.

---

# Banner "Nova verze STRATEGIE" prepracovan (26.8.2026)

Zapsal Claude-28 (Jirka Honomichl, Mac). Nasazeno do `g2007.soubor`, fragment
`apps/api/static/mobile_parts/74_claude27_render_init.js` (funkce `_verTick`,
`_verHardReload`, hook v `render()`, hook u `visibilitychange`/`focus`). Overeno
na zive `/mobile` (HTTP 200, appka se nacte bez JS chyby) a sadou unit testu
primo nad nasazenym kodem (Node.js, mockovane prostredi) - vsechny scenare presly.

## Co bylo spatne (puvodni chovani)

Banner byl fixni pruh pres cely obsah, zobrazil se pri detekci nove verze a zustal,
dokud uzivatel neklikl. Klik spustil `_verHardReload()` - smazal cache/service workery
a udelal `location.reload()` = tvrdy restart cele stranky. Appka drzi navigaci jen
v pameti (`window.__M2W.stack`), ne v URL, takze po restartu appka skoncila na
domovske obrazovce misto tam, kde uzivatel byl - to bylo hlavni stiznost.

## Nove chovani

- **Mimo domovskou obrazovku:** banner se objevi a **sam zmizi po 4 vterinach**,
  zadny reload, rozdelana prace zustava.
- **Na domovske obrazovce** (nebo pri prirozenem prechodu na ni): appka se
  **potichu sama aktualizuje**, zadny banner.
- **Po dokonceni tiche aktualizace:** appka na 5 vterin ukaze zeleny pruh
  "Aktualizovano na novou verzi" - informace se preda pres `sessionStorage`
  (klic `stg_ver_done`), protoze `location.reload()` appku uplne restartuje
  a JS pamet se ztrati. Kontrola probiha hned vedle `window.__stgBoot=true;`,
  tedy pri KAZDEM startu appky, ne jen pri prechodu na home.
- **Po probuzeni appky z pozadi** (`visibilitychange`/`focus`): appka rovnou
  zavola `_verTick()`, nemusi cekat na dalsich az 30 vterin.
- Pojistka `window.__M2W._verReloading` brani dvojimu spusteni `_verHardReload()`.

## ⚠️ DULEZITA GOTCHA - banner NEreaguje na obsah appky

`_verTick()` se pta na `/api/v1/erp/app-version`. Ten endpoint
(`modules/erp/api/router.py:31294`, funkce `app_version`) vraci **git HEAD SHA
CELEHO SERVEROVEHO KODU** (`_read_git_head_sha()`, cache 10s) - **NE hash ani
verzi obsahu appky** (ktery zije v `g2007.soubor`).

**Prakticky to znamena:** editace obsahu appky pres `@@G2007SOUBOR` +
`@@G2007PUBLISH` (jak se dela beznou praci na appce) **banner vubec nespusti**,
i kdyz appku fakticky zmenila. Banner se spusti jen kdyz nekdo nasadi novy
**serverovy kod** (git push do `main` sdileneho repa -> auto-deploy). Overeno
26.8.2026: po nasazeni teto zmeny zustala `/api/v1/erp/app-version` shodna
(`f887b39127c5`) - banner tedy nesel overit zive na telefonu bez skutecneho
deploye serveru, jen izolovanym testem/demem mimo produkci.

**Kdyz nekdo priste bude chtit "zivou ukazku" tohoto banneru:** nejde vyvolat
pouhou upravou `g2007.soubor` - je potreba pockat na (nebo vyvolat, s vedomim
rizika pro celou produkci) skutecny deploy serveroveho kodu.

## Rozpor v pravidlech nalezeny a vyresen behem teto prace

`STRATEGIE_PRAVIDLA_PRACE.md` bod 4 do 26.8. rikal "vyhradne @@G2007SOUBOR" pro
editaci mobilu - uz neplatilo, viz [[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]].
Rozhodl Jirka, potvrdila Marti-AI (msg 13832): obe cesty (cely soubor / cileny
UPDATE s md5 pojistkou) jsou platne, zapsano na obe strany.

## Jak testovat podobne zmeny bez zavislosti na produkcnim loginu

Prihlasovani appky (demo rezim) je v headless automatizaci nespolehlive (cyklici
se zpet na landing, 401 na API). Funkcni postup: stahnout presny bajtovy obsah
fragmentu (kolo base64, viz [[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]]),
extrahovat testovanou funkci 1:1 a spustit v Node.js s minimalnim mockem
(`document`, `fetch`, `sessionStorage`, `location.reload`) - rychle, spolehlive,
testuje skutecny nasazovany kod. Testovani primo v headless Chrome pres
`page.evaluate()` je v teto konfiguraci (patchright) nespolehlive - `evaluate`
bezi v izolovanem JS "world", ktery NEVIDI vlastni promenne/funkce stranky
(window.__M2W apod.), jen sdileny DOM - proto volani funkci appky jmenem z
`page.evaluate()` hazelo "not defined", zatimco skutecne kliknuti na tlacitko
(`page.click`) fungovalo spolehlive.

