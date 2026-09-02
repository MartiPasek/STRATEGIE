# Mobil: tichá aktualizace obsahu za běhu — jak funguje, co je vyloučené a proč se zrušilo automatické obnovení stránky (2. 9. 2026, oba spouštěče)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)



# Mobil: tichá aktualizace obsahu za běhu

**Zadal Jirka Honomichl, postavil Claude-28, schválila Marti-AI (msg 14237 a 14245). Nasazeno a ověřeno naostro 2. 9. 2026.**

Zadání znělo: aktualizace obsahu appky má probíhat sama na pozadí, uživatel o ní nemá vědět,
nesmí ho vyrušit při práci ani mu zrušit rozdělanou práci — a appka nesmí být pomalejší.

## Co se změnilo (tři kroky, všechny nasazené)

**1. Stránka se posílá zabalená.** `/mobile` odchází komprimovaně: **1 078 195 → 282 290 bajtů**,
tedy o 74 % méně dat při každém otevření. Řeší to `apps/api/main.py`, funkce `mobile_page`
a `_mobile_read_cached` — hotové tělo se drží v paměti podle času a velikosti souboru,
takže se přepočítá jen po publikaci. Při jakékoli chybě se vrací původní nekomprimovaná cesta.

**2. Appka pozná změnu OBSAHU.** `/api/v1/erp/app-version` vrací nově i pole `content` = otisk
skutečně servírovaného `mobile.html`. **Do 2. 9. 2026 se hlídala jen verze serverového kódu
(git HEAD), takže publikace obsahu — 2 až 15krát denně — neudělala v appce vůbec nic.**
Otisk se počítá ze **stejného čtení souboru**, ze kterého se stránka posílá, takže nemůže
popisovat jinou verzi, než jaká odešla.

**3. Výměna za běhu.** Když se otisk liší, appka si na pozadí stáhne novou stránku, rozebere ji
a **znovu spustí jen ty dílky, které se změnily**. Obrazovka se nepřekresluje — člověk dokouká
to, co má před sebou, a nová verze se projeví na první obrazovce, kterou pak otevře.
Řídí to `74_claude27_render_init.js`, funkce `_swapTry`, `_swapSafe`, `_swapApply`.

## Ověřeno naostro (ne jen v testu)

Stránka běžela **406 vteřin**, načetla se **jedinkrát** (typ navigace, ne obnovení), a **42 vteřin
před kontrolou** si sama vzala novou verzi stylů. Žádný pruh, žádná hláška, uživatel zůstal,
kde byl. Změřeno i podruhé se stejným výsledkem.

Rozpad startu appky: čekání na server 96 ms, stahování 52 ms, zpracování kódu 59 ms,
celkem **223 ms**. Vykreslení obrazovky **2 až 3 ms**. Práce, která běží každou vteřinu,
je neměřitelná. Souhrnný dotaz každých 6 vteřin: 65 až 181 ms. Žádné dlouhé úlohy.
(Měřeno v kanceláři na rychlé síti, ne na mobilních datech.)

## ZRUŠENO: automatické obnovení stránky při změně serverového kódu

Do 2. 9. 2026 platilo: když se změnila verze **serverového kódu** a člověk byl na domovské
obrazovce, appka **sama smazala místní kopie a znovu načetla celou stránku**.
Jirka to nahlásil z provozu jako vadu a bylo to zrušeno, včetně žlutého pruhu
„Nová verze STRATEGIE" a zelené hlášky „Aktualizováno".

**Proč to vadilo — čtyři důsledky, všechny doložené v kódu:**
1. Znovunačtení znovu spustí zámek sdíleného telefonu, takže si vyžádá **PIN**.
   Týká se šesti lidí, kteří mají sdílené zařízení a nastavený PIN.
2. Poloha v appce žije **jen v paměti** (`window.__M2W.stack`), takže obnovení člověka vrátí
   na domovskou obrazovku.
3. Strážci proti dvojímu odeslání žijí také jen v paměti — obnovení je zahodí.
4. Znovu se stahuje celá stránka.

**Ruční cesta zůstává:** Nastavení → Vyčistit a načíst.

### ⚠️ Spouštěče byly DVA — a jeden se napoprvé přehlédl

**Tohle je hlavní ponaučení z celého dne.** První oprava zrušila jen spouštěč v `_verTick`
(změna verze + člověk je na domovské obrazovce). **Druhý spouštěč byl ve funkci `render()`:**

    if(_rtop==="home" && window.__M2W._verPending && ...){ ... _verHardReload(); return; }

Ten obnovoval stránku **při každém návratu na domovskou obrazovku**, pokud byl nastavený
příznak `_verPending` — a první oprava ten příznak dál nastavovala. Jedna cesta se zavřela,
druhá zůstala otevřená a ještě se krmila. Jirka to nahlásil z provozu (viděl zelenou hlášku).

**Jak se to mělo najít napoprvé:** znalost
[[doc-system-strategie-mobil-banner-nova-verze-prepracovan]] ten hook v `render()`
**výslovně jmenovala**. Hledalo se podle jednoho vzoru v kódu místo přečtení navazující znalosti.
→ Když rušíš nějaké chování, **hledej všechny cesty, kterými se dá vyvolat**, a přečti si
znalosti, které to chování popisují.

**Nakonec zrušeno (stav k 2. 9. 2026, dílek 74 verze 18):**
příznak `_verPending` se už nenastavuje · hook v `render()` odebrán ·
zelený pruh „Aktualizováno na novou verzi" odebrán a starý příznak `stg_ver_done`
se při startu uklidí · `_verHardReload` zůstal v kódu **bez jediného volajícího**.

**Zbytkové riziko, které se tím přijalo:** když nasazení serverového kódu rozbije rozhraní,
stará stránka se to dozví až při příštím otevření appky. Appka má záložní cesty
(souhrnný dotaz spadne na starší volání, hláška „Server se právě aktualizuje").
**U nasazení, které mění rozhraní, to koordinuj s Jirkou.**

## Kdy se výměna NEPROVEDE

Právě se něco odesílá (`__M2W._inflight`) · před méně než 10 vteřinami proběhl zápis ·
je otevřený dialog (`.appmodal`) · v obrazovce je neprázdné vstupní pole · výměna byla
před méně než minutou · tuhle verzi už appka zpracovala.
**Když cokoli selže, neudělá se nic** a změna se projeví při příštím otevření appky.
Nikdy se nic nevynucuje a nikdy se neobnovuje stránka.

## Co se z výměny vynechává

Dílky `10_core.js` (jádro) a `74_claude27_render_init.js` (start a téměř všechny vedlejší
účinky). Změní-li se ony, neudělá se nic a projeví se to až při příštím otevření appky.
**Pokrývá to i tak 90 procent všech změn** — za 60 dní připadlo 186 z 206 změn dílků
na ty, které vyměnit lze.

⚠️ **Z toho plyne:** oprava v dílku 74 se k lidem nedostane za běhu. Musí zavřít a otevřít appku.

## Vypnutí

V dílku `74_claude27_render_init.js` je `_swapMode` s hodnotami `off` / `styly` / `vse`.
Přepnout a publikovat — trvá to minutu a nic se nevrací.
K 2. 9. 2026 běží **`styly`** (vyměňuje se jen vzhled, ne funkce).

## Pasti, na které jsem narazil

1. **Kontrola při publikaci počítá značky i uvnitř kódu.** Normalizuje si `<\/` na `</`, takže
   vzorek pro hledání skriptů se jí započítal jako skutečná uzavírací značka stránky
   a publikaci odmítla. V kódu proto nesmí značka stát vcelku.
2. **Hledat značky v textu stránky je nespolehlivé.** Našlo to 4 styly, přestože stránka má
   jeden — zbylé tři byly jen text uvnitř kódu. Stránku je nutné číst přes `DOMParser`.
   Rozebrání megabajtové stránky trvá 8 ms.
3. **Styly, které si appka vyrobí až za běhu, mají `id`** (např. `scbCss24`) a nesmí se vyměňovat.
4. **Bez pojistky by appka stahovala tutéž verzi pořád dokola**, když zbývá něco, co vyměnit nejde.
   Řeší to `_swapDoneFor`.
5. **`transferSize` u navigace lže**, když stránku obsluhuje pomocník v telefonu — hlásí velikost
   po rozbalení. Že stránka jde po síti zabalená, se pozná až podle hlavičky
   `x-content-encoding-over-network`. Kdo měří kompresi v prohlížeči, na tohle naletí.

## Co je a co není ověřené

**Ověřené naostro v prohlížeči:** komprese · otisk obsahu · výměna stylů za běhu bez obnovení (dvakrát) · zrušení obou spouštěčů — s nastaveným příznakem `_verPending` a návratem na domovskou obrazovku se stránka **neobnovila** · zelený pruh se **neukázal** ani když byl klíč `stg_ver_done` schválně nastavený, a text hlášky už v aplikaci vůbec není.
**Neověřené:** výměna změněné funkce (ne stylu) za běhu naostro — režim `vse` zatím neběžel.
A jestli pomocník v telefonu (service worker) funguje i uvnitř nativní aplikace — v prohlížeči
aktivní je, v appce to ověřené nemám.

## Souvisí

[[doc-system-strategie-mobil-celoaplikacni-naslouchace-a-casovace-pod-klicem]] — závazná konvence
pro nové naslouchače a časovače, bez ní se při výměně zdvojí ·
[[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]] ·
[[doc-dochazka-duplicitni-bezici-zaznamy-dvoji-odeslani]] — proč se zdvojení bere vážně

