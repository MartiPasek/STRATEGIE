# Pochůzky: hotové kotvy v 60_dochazka.js, registrace obrazovky a postup zápisu (předání 8. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pochůzky — UI: kotvy, registrace a postup zápisu (předání, 8. 9. 2026)

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

