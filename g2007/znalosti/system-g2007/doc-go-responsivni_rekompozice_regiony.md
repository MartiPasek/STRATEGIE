# Responsivní re-kompozice: z pixelů Centrály na síť regionů STRATEGIE (+ vzor Poptávky edit)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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

## 4. Konvence pojmenování panelů (samodokumentující — pozice JE v názvu)
Cíl: **z názvu je vidět SÉMANTIKA i POZICE (dock)** — přesně jak to měl Marti (`MAIN-TOP`). Žádné `panel_cby7` (náhodné názvy = zdroj osiření), a pozici (top/left/…) **nedávat do komentáře, ale do jména**.

**`<sémantika>-<POZICE>`** (pozice je POVINNÁ):
- **POZICE (dock) = velkými, na konci:** `-TOP` / `-LEFT` / `-RIGHT` / `-CLIENT` (výplň zbytku) / `-BOTTOM`. Ze jména hned víš, kam panel dokuje.
- **sémantika = co obsahuje:** `hlavicka`, `naseudaje`, `poptavajici`, `adresar`, `poznamka`, `zbozi`, `aps`, `oznaceni`, `main`, `footer`…
- **typ z kontextu / volitelný prefix** u speciálů: `grid_`, `tab_` (tab dokuje do pagecontrolu, pozici nemá).
- Příklady: `hlavicka-TOP`, `naseudaje-TOP`, `poptavajici-LEFT`, `adresar-RIGHT`, `poznamka-CLIENT`, `zbozi-CLIENT`, `footer-BOTTOM`, `main-CLIENT`. → ze jména čteš **co i kam**.
- Vnoření navíc doupřesní parent (strom): `poptavajici-LEFT` uvnitř `tab_obecne` = skupina „Údaje o poptávajícím" vlevo na Obecné.
- TEST engine: prefix `TEST` patří do **captionů/popisů**, ne do `name`; `name` drž čisté (`naseudaje-TOP`).

## 5. VZOR: region net jádra „Poptávky edit" (form 3)
Návrh responsivní sítě (odvozeno z §3; **pozice v názvu** dle §4; vpravo obsah):
```
form  „Poptávka"
├─ hlavicka-TOP                   ← GroupBox „Poptávka" (dokuje nahoru)
│   ├─ udaje-LEFT                 ← Číslo, Datum, Zakázka, Splněno  (flow)
│   └─ pozn-CLIENT                ← Poznámka splněno (_PoznamkaSplneno, akRight → táhne)
├─ main-CLIENT                    ← PageControl 7510 (vyplní zbytek)
│   ├─ tab_obecne
│   │   ├─ naseudaje-TOP          ← Řešitel, Náš popis, Středisko  (řádek, flow)
│   │   ├─ poptavajici-LEFT       ← Organizace, Kdo poptával, Označení, Výběr oblasti  (flow ↓)
│   │   ├─ adresar-RIGHT          ← Adresář (soubory) → D:\Data\poptavky\<doklad>
│   │   └─ poznamka-CLIENT        ← Poznámka (Poznamka)  (vyplní zbytek pod tím)
│   ├─ tab_aps
│   │   └─ aps-CLIENT             ← _KalkHodOdhad, _ProcentaDoVytizeni, _VytizeniHodDenne, _vytizeniDatKonec,
│   │                               _VytizeniHodinyOdhad, _VytizeniUkazNahore, _VytizeniSpecZakaznik, [Naplánovat vytížení]  (flow ↓)
│   ├─ tab_oznaceni
│   │   ├─ oznaceni_akce-TOP      ← [Generuj značení] + GenZnacProjektu
│   │   └─ oznaceni_grid-CLIENT   ← Grid 7591
│   └─ tab_zbozi
│       └─ zbozi_grid-CLIENT      ← GridPolDoklad → TabPohybyZbozi (select-detail, IDDoklad=@id)
└─ footer-BOTTOM                  ← [Generovat nabídku] + [Návazné doklady]
```
Poznámky k re-kompozici (proč tyhle pozice):
- **`naseudaje-TOP`**: v Centrále široký nízký band (`alTop`, akL,T,R) se 3 poli na různých `Left` (Popis 10 / Středisko 401 / Řešitel 499) → v STRATEGII **jeden řádkový region s flow** (ne 3 px sloupce), na úzké šířce se zalomí. Proto `-TOP`.
- **`poptavajici-LEFT` + `adresar-RIGHT`**: GroupBox „Údaje o poptávajícím" (`alNone`, vlevo) + FileListBox Adresář (`Left 342`, vpravo) → **split na levý a pravý region** vedle sebe.
- **`pozn-CLIENT` / `poznamka-CLIENT`**: pole s `akRight` (táhnou do šířky) → dej je do regionu `-CLIENT`, který vyplní zbytek.
- Druhý PageControl 7585 (`alBottom`) — účel doostřit (možná stavová lišta); prozatím vynechán.

## 6. Postup pro generátor (rozšíření receptu)
1. Přečti jádro Centrály (přehledy 2702/2704/2706, viz [[Centrála — stavba jader]]).
2. **Postav region net** (§3): dock kontejnery → regiony; alNone interiéry → sloupcové/řádkové panely dle geometrie; pojmenuj dle §4.
3. **Usaď komponenty** do regionů (flow), typ+binding dle mappingu §8 doc „stavba jader".
4. Založ `fw.core` + `comp_def` řádky (parent = region). **Deterministicky = žádné ruční tahání = žádné osiření.**

---
*Responsivní re-kompozice + region net — Claude C24, 19. 7. 2026. „Nepřenášej pixely, postav síť regionů a usaď do ní komponenty." Vzor: Poptávky edit (form 3).*


