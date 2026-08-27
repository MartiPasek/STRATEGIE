# Nepřítomnost OSVČ: kde se zobrazuje a kde ne (Docházka new ne, Správa info, Opravy šedě)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nepřítomnost OSVČ — kde se zobrazuje a kde ne

**27. 8. 2026, Peťa + C26.** Peťa: *„v Docházce new nesmí být žádný, to už jsme řešili,
má být ve Správě jen jako info, a pak být šedě v Opravách."* Prověřeno, jedno místo
odpovídalo, druhé ne.

## Co to je
Typ `osvc_absence` = **„Nepřítomnost OSVČ"** (činnost 37), zavedla Peťa 25. 6. 2026.
Živnostník jen oznámí, že ten den nebude — nemá dovolenou ani nemocenskou, takže je to
prostě neplacená nepřítomnost. **Není to docházka.**

## Kde se má a nemá zobrazovat

| Kde | Jak | Stav k 27. 8. 2026 |
|---|---|---|
| **Docházka new** | vůbec | ✅ bylo v pořádku — dataset `dochazka.zakazky_vse_list` má `AND et.code <> 'osvc_absence'` (Peťa 17.–18. 8.) |
| **Správa docházky** | jen jako informace | ✅ |
| **Opravy docházky** | **šedě**, needitovatelně | ❌ nebylo — doplněno 27. 8. |

## Co se 27. 8. změnilo
`att_fix_day` počítal `editable` jen z toho, jestli je období zamčené a jestli má řádek
značku původu (`source_system`). OSVČ nepřítomnost z mobilu značku nemá, takže vycházela
jako **běžný editovatelný záznam**. Doplněno `and r[7] != "osvc_absence"` do `editable`.

**STORNO ZŮSTALO POVOLENÉ — a to schválně.** Nejdřív jsem zablokovala i to a hned to
vrátila: pravidlo Peti ze 4. 8. (`doc-dochazka-nepritomnost-osvc-nepatri-do-fondu`) říká,
že když chce člověk nepřítomnost přepsat prací, **jediná cesta je `fix/void` + `fix/add`**
(`fix/entry` u ní nejde, nemá časy). Blokem storna by ta cesta přestala existovat.
**Kdo bude sahat na `editable`/`stornable`, ať si to pravidlo přečte první.**

## Ověřeno na produkci
- Voříšek, 14. 8. (měsíc odemčený): `editable=false`, `stornable=true` ✅
- Kontrolní den (Havlát, 26. 8.): Práce i Přestávka dál `editable=true` — nic jiného
  se nezablokovalo ✅

## Past, na kterou jsme narazily
Šedý řádek v Opravách **ještě neznamená, že platí pravidlo o OSVČ**. Peťa poslala snímek
Lubošе Lva z 21. 7., kde byla nepřítomnost OSVČ šedá — jenže **červenec je uzamčený**
(mzdy zpracovány) a v uzamčeném měsíci je šedý každý řádek. Porovnání dvou dnů to
odhalilo: Lev 21. 7. `locked=true`, Voříšek 14. 8. `locked=false` a přesto tehdy
`editable=true`. **Vždy ověřovat v ODEMČENÉM měsíci.**

## Souvislost
`doc-dochazka-nepritomnost-osvc-nepatri-do-fondu` (do FPD se nezapočítává, 4. 8.) ·
`doc-dochazka-neplacene-volno-z-mobilu-jen-ohlaseni` (27. 8.).

## Otevřené
Nepřítomnost OSVČ z „Tady budu jinde" se pořád zapisuje **bez vazby** (`source_id` prázdné),
takže zrušení v appce (`att_absence_cancel`, hledá podle `source_system='absence_req'`
a `source_id`) ji nenajde a den zůstane viset. K 27. 8. jsou takové **3 dny**, všechny
Pavel Voříšek (30. 7., 31. 7., 14. 8.). Totéž platí pro `sickday` — ten ale čeká na Jirku,
viz `doc-dochazka-sickday-budouci-den-se-tise-ztrati`.

