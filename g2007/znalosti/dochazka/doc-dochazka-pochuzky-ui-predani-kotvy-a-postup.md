# Pochůzky — UI: obrazovka cesta_vyber NASAZENA 9. 9. 2026 (kotvy, registrace, odchylky)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pochůzky — UI: obrazovka `cesta_vyber` NASAZENA (9. 9. 2026)

> **✅ HOTOVO 9. 9. 2026 (C24 / Kristý).** Text níže byl předání pro druhou session;
> zůstává jako záznam zadání a kotev. **Co se reálně nasadilo, je v oddílu
> „Jak to dopadlo" na konci** — včetně dvou odchylek od tohoto předpisu.

Navazuje na `doc-dochazka-pochuzky-zakazka-cinnost-a-tri-vstupy` (proč a co).
Tady je **jak** — připraveno C24, odsouhlasila Kristý 8. 9. 2026.
Hotový kód obrazovky leží v repu: `navrh_pochuzka_vyber_2026-09-08.js`,
plné předání `PREDANI_C24_pochuzky_2026-09-08.md`.

## Stav: backend HOTOVÝ, zbývá jen UI
`att_checkin` **v13** — `trip` vstupuje do větve s `_wa_open` a `att_apply_work_selection`,
takže služební cesta zakládá rozpad. Další serverová změna **není potřeba**.
Endpointy existují: `/app/work/set-zakazka`, `/set-rezie`, `/set-cinnost`, `/state`,
`/attendance/checkin`, `/attendance/announce`.

## Tři kotvy v `60_dochazka.js` (přesné znění, ověřeno 8. 9. 2026)
1. `dirBtn(box,"🚙 Jedu rovnou k zákazníkovi…","ghost",function(b){ act("checkin",{kind:"trip"},b); },_blueStyle);`
   → `window._cestaRezim="prichod"; go("cesta_vyber");`
2. `dirBtn(box,"📦 Služební pochůzka, pak dorazím…","ghost",function(b){ presence({text:"Na služební pochůzce, pak dorazím",add_since:true},b); },_blueStyle);`
   → `window._cestaRezim="dorazim"; go("cesta_vyber");`
3. `expOpt(bx,"🚗 Mám služební pochůzku…","ghost",function(b2){ chipsIn(b2,"Pochůzka potrvá cca:",…); timeChips(b2,"…nebo do kolika:",…); });`
   → `window._cestaRezim="zachodu"; go("cesta_vyber");`

⚠️ **Třetí je jiný** — rozbalovací volba s časovými čipy, ne tlačítko. Ty čipy se
**NESMÍ ztratit**, je to jediné místo, kde člověk řekne, jak dlouho bude pryč, a na tom
stojí tlačítka **Konec** a **Prodloužit**. V režimu `"zachodu"` proto nevykreslovat
„Potvrdit a vyrazit", ale rovnou ty dvě řady čipů; každý čip udělá
`checkin {kind:"trip", switch:true}` a pak `presence {eta_min / until_txt}`.

## Registrace obrazovky — bez ní TIŠE NEEXISTUJE
Všechna tři místa: `10_core.js` → `window.__M2W.cesta_vyber = mkWrap();` ·
`72_migrace_sw_isds.js` → `cesta_vyber=window.__M2W.cesta_vyber` ·
`73_pref_poptavka.js` → `cesta_vyber:cesta_vyber`.

## ⛔ Na co nesahat
- **113 NEPŘEVÁDĚT na `kind='standard'`** — 33 z 34 úseků od června je na Režii u 12 lidí.
  Obrazovka pochůzky je vědomá výjimka, která nabídne obě bez ohledu na `kind`.
- **Interní id je 16 (č. 9) a 37 (č. 113)**, ⛔ NE `ec_cislo` — pod `id=9` sedí Značení vodičů.
- **`att_checkin` nezná `cinnost_id`** — bere z předvolby (`_wp_get`). Proto NEJDŘÍV
  nastavit předvolbu, TEPRVE PAK píchnout. Kdo píchne dřív, založí úsek bez zakázky.
- **`prace_zak` a `prace_cin` si volbu nastaví SAMY** a volají `back()`. `go(id)` pushne
  na `window.__M2W.stack`, `back()` popne — takže se uživatel vrátí na `cesta_vyber`
  a ta si stav znovu načte z `/app/work/state`. Žádný callback nevymýšlet.
- **Typ záznamu zůstává `work`** u tripu i home office (mzdy nerozlišují, kde člověk je).
- **`status='announced'` nepředefinovávat** — na šesti místech znamená „nepočítat".
  Kdo chce, aby pochůzka počítala hodiny, přidá píchnutí VEDLE ohlášení.

## Ještě dořešit v `prace_cin()`
Seznam se vybírá podle druhu zakázky. Kdo si vezme reálnou zakázku + činnost 113
(`kind='rezie'`), uvidí jen `standard` seznam a svoji činnost tam nenajde. Ošetření:
když je aktuální `cinnost_id` jedna z těch dvou, přidat obě do mřížky vždycky.

## Jak zapsat
⛔ **NE přes SQL UPDATE** — most jede přes SQLAlchemy, `:slovo` je bind parametr a v JS je
`display:flex`, `flex:1`, `padding:9px`; každé takové CSS dotaz položí.
✅ **`@@G2007SOUBOR`** — bere celý obsah souboru, takže napřed přečíst celý
`60_dochazka.js` (na několik čtení), složit a poslat vcelku. Ořízne koncový nový řádek.
Past: **`@@G2007SESTAV` skládá VŠECHNY aktivní fragmenty** — před spuštěním zkontroluj,
co čeká nepublikované od jiných instancí. `60_dochazka.js` je sdílený a živý (8. 9. do
docházky commitovali C26, C28 i C25) — ohlas se přes `@@WORK`.

## Ověření naostro
Jedno reálné píchnutí pochůzky → v `tenant.vyroba_work` musí vzniknout položka
**se zakázkou i činností** a `att_entry` mít zakázku v hlavičce.

---

## Jak to dopadlo (nasazeno 9. 9. 2026, C24 / Kristý)

**Publikováno:** `mobile.html` v180 → **v181**. Dílky: `60_dochazka.js` 81→**82**,
`10_core.js` 17→**18**, `71_plan_prace_cinnosti.js` 21→**22**,
`72_migrace_sw_isds.js` 10→**11**, `73_pref_poptavka.js` 13→**14**.
Před zápisem ověřeno **md5 každého dílku proti DB**, po zápisu md5 znovu (souhlasí),
před publikací zkontrolováno, že novější než poslední publikace je **jen mých 5 dílků**
(past `doc-provoz-g2007publish-selftest-deadlock-a-sestav-past`).

### ⚠️ Odchylka 1: `presence()` a `act()` se z nové obrazovky NESMÍ volat
Obě na konci volají `dochLoad()` a kreslí do DOM obrazovky docházky. Z `cesta_vyber`
by to skončilo v prázdnu. **Obrazovka si dělá vlastní `checkin` + `announce` a pak `back()`** —
`back()` vrátí na docházku, ta se překreslí sama.

### ⚠️ Odchylka 2: čipy „za chodu" — scope, ne copy-paste
`chipsIn`, `timeChips` i `presence` žijí **uvnitř `dochLoad()`**, kdežto obrazovka musí být
na vnější úrovni dílku (patka ji registruje přes `__setImpl`). Řešení:
- řada „cca" (6 čipů) je v obrazovce **vlastní** (`_cestaChipy`, 8 řádků, závisí jen na `el`),
- kolečko „…nebo do kolika" se **zpřístupní jedním řádkem** uvnitř `dochLoad()`:
  `window.__M2W._cestaTimeChips=timeChips;` — je to čistý renderer, z DOM docházky nic nepotřebuje,
- pojistka: když hook chybí (na obrazovku by se někdo dostal, aniž proběhl dílek docházky),
  vykreslí se `<input type="time">`.

Zachováno i tlačítko **„Zatím nevím — bez času"**, které v předpisu nebylo (do původní
volby přibylo později) — bez něj by lidem zmizelo.

### ✅ Ověřeno v kódu: `@@G2007SOUBOR` koncový newline NEOŘEZÁVÁ, ale DOPLŇUJE
`10_core.js` má v DB o 1 znak víc, než se poslalo. Důvod je v `modules/erp/api/router.py`
(větev `@@G2007SOUBOR`, bod 2 z 17. 8. 2026): `if _obsah3 and not _obsah3.endswith(chr(10)): _obsah3 += chr(10)`.
Most (`claude_sql_runner.py`) koncový řádek `.strip()`em opravdu ořeže, ale **server ho vždy vrátí zpět**
— proto je uložený dílek idempotentně zakončený newline a **dorovnávat ho ručně už netřeba**.
(Starší návod „doplnit `chr(10)`" platí jen pro cílený zápis mimo `@@G2007SOUBOR`.)

### Co ještě čeká
- **Ostrý test:** jedno reálné píchnutí pochůzky → v `tenant.vyroba_work` musí vzniknout položka
  **se zakázkou i činností** a `att_entry` mít správnou zakázku v hlavičce.
- Body 4 a 5 (návrat z pauzy přes notifikaci bez zakázky; strop pro `kind='commute'`)
  a body 1, 2, 6 z Péťina seznamu zůstávají mimo tenhle úkol.

