# Responsivní re-kompozice: z pixelů Centrály na síť regionů STRATEGIE (+ vzor Poptávky edit)

> Autor: Claude ID24, 19. 7. 2026, na pokyn Marti. Klíčové know-how pro duplikaci jader: **jádro nelze přenést 1:1** (Centrála = pixely/statika, STRATEGIE = responsivita). Musí se PŘEMÝŠLET a nejdřív postavit adekvátní **síť regionů (panelů)**, do které se komponenty usadí.
> Navazuje na [[Centrála — stavba jader]] (`doc-go-centrala_stavba_jader`) a [[fw-core-kompozice]].

## 1. Princip (proč ne 1:1)
- **Centrála = pixely (statika):** komponenta má absolutní `Left/Top/Width/Height`; okno pevné → drží pohromadě („unese").
- **STRATEGIE = responsivita (tok):** stejné pixely při jiné šířce/zoomu → překryv, výpadek z panelu, **osiření** → **„rozpadne se"**.
- **Závěr: přenos 1:1 = past.** Nekopírujeme souřadnice — **skládáme síť regionů** a komponenty do nich usazujeme.

## 2. Řešení = síť regionů (panelů)
Region = panel s odpovědností za kus plochy. Skládáme je:
- **vedle sebe** = sloupce (`align: left` + pružný `client`),
- **pod sebe** = řádky (`align: top`, flow s `always_new_row`),
- **do sebe** = vnoření (panel v panelu).

Komponenty **bydlí v regionu**, ne na souřadnici. Panel drží pozici responsivně; pole se v něm jen zařadí. Region net = skelet; komponenty = obsah.

## 3. Jak síť ODVODIT z Centrály (ne vymýšlet od nuly)
Centrála dává půl práce zadarmo — čti z definice jádra (`EC_FormDefEdit`/Property):
1. **Dock patro ZACHOVEJ.** Kontejnery s `Align` (`alTop`/`alClient`/`alBottom`/`alRight`/`alLeft`) jsou už responsivní → mapuj 1:1 na regiony STRATEGIE (top/client/bottom/right/left). Tady se nic nerozpadá.
2. **`alNone` interiér ROZBIJ dle geometrie.** Uvnitř GroupBoxů s absolutními px odvoď:
   - **sloupce** = shluky komponent podle `Left` (blízké Left = jeden sloupec → sloupcový panel),
   - **řádky** = shluky podle `Top` (blízké Top = jeden řádek),
   - **pružnost** = `Anchors`: `akRight` → panel má být `client` (táhne do šířky), `akBottom` → drží dole.
3. **Vnoření** = strom `ParentName`.
→ Výsledek: dock regiony + rozbité alNone interiéry = **responsivní panel-net**, do kterého usadíš komponenty flow-em.

## 4. Konvence pojmenování panelů (samodokumentující)
Cíl: **z názvu je vidět typ i umístění** (žádné `panel_cby7` — náhodné názvy = zdroj osiření). Vzor Centrála core 72 měl dobré (`panel_test_kontakt`) i špatné (`panel_cby7`); zde je vylepšená konvence:

**`<prefix>_<sémantika>[_<pozice>]`**
- **prefix = typ/role:** `reg_` (dock region), `grp_` (sémantická skupina = GroupBox), `col_` (sloupcový panel), `row_` (řádkový panel), `pnl_` (obecný panel), `pgc_` (pagecontrol), `tab_` (záložka), `grid_` (grid).
- **sémantika = co obsahuje:** `hlavicka`, `naseudaje`, `poptavajici`, `adresar`, `poznamka`, `zbozi`, `aps`, `oznaceni`…
- **pozice (kde nejednoznačné):** `_left`/`_right`/`_top`/`_bottom` nebo `_c1`/`_c2`.
- **umístění je čitelné ze stromu** (parent): `grp_poptavajici` uvnitř `tab_obecne` → hned víš, že je to skupina „Údaje o poptávajícím" na záložce Obecné.
- TEST engine: prefix `TEST` patří do **captionů/popisů** (ne nutně do `name`); `name` drž čisté a významové.

## 5. VZOR: region net jádra „Poptávky edit" (form 3)
Návrh responsivní sítě (odvozeno z §3; vlevo region/typ, vpravo obsah):
```
form  „Poptávka"
├─ reg_hlavicka              (dock TOP)              ← GroupBox „Poptávka"
│   ├─ row_hlavicka_udaje    (row, left/client)      ← Číslo, Datum, Zakázka, Splněno  (flow)
│   └─ col_hlavicka_pozn     (col, right)            ← Poznámka splněno (_PoznamkaSplneno, akRight)
├─ reg_main                  (CLIENT, pagecontrol)   ← PageControl 7510
│   ├─ tab_obecne
│   │   ├─ grp_naseudaje      (dock TOP, full width)  ← Řešitel, Náš popis, Středisko  (row, flow)
│   │   ├─ row_obecne_stred   (dock CLIENT, split)
│   │   │   ├─ grp_poptavajici (col, left)            ← Organizace, Kdo poptával, Označení, Výběr oblasti (flow ↓)
│   │   │   └─ pnl_adresar     (col, right)            ← Adresář (soubory) → D:\Data\poptavky\<doklad>
│   │   └─ pnl_poznamka        (dock BOTTOM/client)    ← Poznámka (Poznamka)
│   ├─ tab_aps
│   │   └─ grp_aps_vytizeni    (col, flow ↓)           ← _KalkHodOdhad, _ProcentaDoVytizeni, _VytizeniHodDenne,
│   │                                                    _vytizeniDatKonec, _VytizeniHodinyOdhad, _VytizeniUkazNahore,
│   │                                                    _VytizeniSpecZakaznik, [Naplánovat vytížení]
│   ├─ tab_oznaceni
│   │   ├─ pnl_oznaceni_akce   (dock TOP)              ← [Generuj značení] + GenZnacProjektu
│   │   └─ grid_oznaceni       (CLIENT)                ← Grid 7591
│   └─ tab_zbozi
│       └─ grid_zbozi          (CLIENT)                ← GridPolDoklad → TabPohybyZbozi (select-detail, IDDoklad=@id)
└─ reg_footer                (dock BOTTOM)            ← [Generovat nabídku] + [Návazné doklady]
```
Poznámky k re-kompozici:
- **`grp_naseudaje`**: v Centrále široký nízký band (`alTop`, akL,T,R) se 3 poli na různých `Left` (Popis 10 / Středisko 401 / Řešitel 499) → v STRATEGII **jeden řádkový region s flow** (ne 3 px sloupce), na úzké šířce se zalomí.
- **`row_obecne_stred`**: GroupBox „Údaje o poptávajícím" (`alNone`, vlevo) + FileListBox Adresář (`Left 342`, vpravo) → **split na dva sloupce** `grp_poptavajici` (left) / `pnl_adresar` (right/client).
- **`col_hlavicka_pozn`**: „Poznámka splněno" má `akRight` → dej ji do pravého regionu, který táhne do šířky (`client`).
- Druhý PageControl 7585 (`alBottom`) — účel doostřit (možná stavová lišta); prozatím `reg_bottom` skryt/vynechán.

## 6. Postup pro generátor (rozšíření receptu)
1. Přečti jádro Centrály (přehledy 2702/2704/2706, viz [[Centrála — stavba jader]]).
2. **Postav region net** (§3): dock kontejnery → regiony; alNone interiéry → sloupcové/řádkové panely dle geometrie; pojmenuj dle §4.
3. **Usaď komponenty** do regionů (flow), typ+binding dle mappingu §8 doc „stavba jader".
4. Založ `fw.core` + `comp_def` řádky (parent = region). **Deterministicky = žádné ruční tahání = žádné osiření.**

---
*Responsivní re-kompozice + region net — Claude C24, 19. 7. 2026. „Nepřenášej pixely, postav síť regionů a usaď do ní komponenty." Vzor: Poptávky edit (form 3).*
