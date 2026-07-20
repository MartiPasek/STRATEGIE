# Centrála — stavba jader (konstrukce formulářů) + Rosetta Stone Centrála↔STRATEGIE

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Centrála — stavba jader (konstrukce formulářů) + Rosetta Stone Centrála↔STRATEGIE

> Autor: Claude ID24, 19. 7. 2026, na pokyn Marti (Marti + Kristý potřebují, aby mi/Claude24 stačil printscreen jádra či přehledu Centrály a z něj + DB jsem poskládal vše pro **duplikaci jádra do STRATEGIE**). Marti dodal systémové přehledy 2702/2704/2706 = klíč, ať zbytečně nehledám.
> Stav: kompletní datový model Centrála jádra + property/typový/lookup slovník + mapping na `fw.*` + vzor jádro „Poptávky edit" (form 3). Zdroj pravdy pro „printscreen → spec → duplikace".

## 1. Účel
Centrála = náš (EUROSOFT) Delphi/VCL systém nad DB_EC; jeho **jádra** (editační formuláře dokladů) jsou uložená v datech (ne zkompilovaná napevno) v tabulkách `EC_FormDef*`. STRATEGIE (web) staví obrazovky ze `fw.*`. Zrcadlení = přečíst definici jádra z Centrály a převést ji mappingem (§8) na `fw.comp_def` strom.

## 2. Datový model jádra (DB_EC)
| tabulka | role | STRATEGIE ekvivalent |
|---|---|---|
| `EC_FORMDEF` | jádro/formulář (ID, Název). Vzor: **ID 3 = „Poptávky edit"** | `fw.core` |
| `EC_FormDefEdit` (FDE) | **komponenty** (ID, `ID_Form`, `Typ`, `Smazana`) = uzly | `fw.comp_def` |
| `EC_FormDefEditProperty` (FDEP) | **parametry** per komponenta (`Property`/`Value`) | `fw.comp_def.layout` jsonb / `comp_def_prop` |
| `EC_FormDefComponent` (FDC) | katalog typů (`Typ`→`Name`) | `fw.comp_type` |
| `EC_FormDefComponentTextList` | číselníky/lookupy polí | `fw.data_source` / hodnoty |

Komponenta patří jádru přes `FDE.ID_Form`; strom se skládá přes property **`ParentName`** (viz §3).

## 3. Slovník properties (`EC_FormDefEditProperty`) — parametry komponenty
Klíčové (ověřeno na form 3, přehled 2704):
- **`ParentName`** = **strom**: hodnota `c<ID>` (odkaz na komponentu-rodiče), + speciální `def`/`Def` = formulář (root), `Footer` = patka. ⚠️ property se jmenuje `ParentName`, NE `Parent`.
- **`Anchors`** = kotvení (Delphi): `akLeft,akTop` (fix vlevo nahoře), `+akRight` (táhne do šířky), `+akBottom` (drží dole). Kombinace = pružné rozměry.
- **`Align`** = dock: `alNone` / `alTop` / `alClient` (výplň) / `alBottom` / `alRight` / `alLeft`. Kontejnery (GroupBox/Panel/PageControl) kotví align; pole spíš anchors.
- **`Left`/`Top`/`Width`/`Height`** = absolutní geometrie v px (v rámci rodiče).
- **`FieldName`** = zdrojový/cílový sloupec (data-binding).
- **`Caption`** = popisek · **`ReadOnly`** · **`Alignment`** (taLeftJustify/taRightJustify) · **`Enabled`** · `Color` · `AutoSelect` · `OznacujPriKliku` · `LabelPosition` (lpTopLeft) · `LabelFont.Size` · `AlignWithMargins`/`Margins` · `ParentFont`.

## 4. Katalog typů (`EC_FormDefComponent`, Typ→Name)
`2` Edit · `7` Combobox · `5` DateEdit · `3` CheckBox · `4` RichEdit · `6` **FormList** (lookup na přehled) · `12` GroupBox · `13` Panel · `15` PageControl · `16` TabSheet · `11` Grid · `21` **GridPolDoklad** (grid položek dokladu) · `9` FileListBox (adresář souborů) · `8` Button · `30` FormSetting.

## 5. Lookupy / číselníky (`EC_FormDefComponentTextList`, přehled 2706)
Váže se k poli přes `SQLdef_Field`. Dva režimy:
- **Statický list** (Combobox) — napevno hodnoty: pole `Stredisko` → Výroba=`001`, Software=`002`, Obě=`900` (Text=zobraz, Value=uloží).
- **Přehled-backed** (FormList) — odkaz na jiný přehled přes **`CisloPrehledu`** + Text (zobraz sloupec) / Value (klíč): `CisloZam`→**125** (zaměstnanci), `CisloOrg`→**105** (organizace), `KontaktOsoba`→**107** (kontaktní osoby). Tj. FormList = výběr z přehledu.

## 6. Systémové přehledy pro čtení jádra (Martiho nástroje — „nehledej, čti")
- **279** „Přehled komponent" (UI: taby Komponenty / Property / TextListy / Akce jádra + „Definice jádra").
- **2702** = komponenty jádra: `EC_FormDefEdit` + typ (`FDC.Name`) + Caption/FieldName/Left. `WHERE FDE.ID_Form=:ID`.
- **2704** = properties per komponenta: všechny `EC_FormDefEditProperty` + `ParentName` + ValueNum. `WHERE FDE.ID_Form=:ID`.
- **2706** = TextListy/lookupy: `EC_FormDefComponentTextList` join `EC_FORMDEF`. `WHERE E.ID=:ID`.
→ Z printscreenu vyčti **ID_Form** (nebo číslo přehledu ve stavovém řádku), pusť 2702/2704/2706 → autoritativní definice bez hádání.

## 7. VZOR: jádro „Poptávky edit" (form 3, 42 komponent, doklad řady 900)
Strom (rekonstruováno z `ParentName`; anchors/align v závorce):
```
Form (def)
├─ GroupBox 574 „Poptávka" (alTop; akL,T,R)
│   ├─ Edit 51 „Číslo" → PoradoveCislo (ReadOnly, taRight)
│   ├─ DateEdit 64 „Datum" → DatPorizeni
│   ├─ FormList 2146 „Zakázka" → CisloZakazky
│   ├─ CheckBox 1086 „Splněno" → Splneno
│   └─ RichEdit 13017 „Poznámka splněno (…heslo »důvod nezrealizování«)" → _PoznamkaSplneno (alRight; akT,R,B)
├─ PageControl 7510 (alClient)
│   ├─ TabSheet 7512 „Obecné"
│   │   └─ Panel 13697 (alTop; akL,T,R)
│   │       ├─ GroupBox 575 „Naše údaje" (alTop; akL,T,R)
│   │       │   ├─ FormList 66 „Řešitel" → CisloZam  (lookup přehled 125)
│   │       │   ├─ Edit 49 „Náš krátký popis poptávky" → PopisPrjZakaznik
│   │       │   └─ Combobox 56 „Středisko" → Stredisko  (list Výroba/Software/Obě)
│   │       ├─ GroupBox 573 „Údaje o poptávajícím"
│   │       │   ├─ FormList 65 „Organizace" → CisloOrg  (lookup přehled 105)
│   │       │   ├─ FormList 243 „Kdo to poptával" → KontaktOsoba  (lookup přehled 107)
│   │       │   ├─ Edit 52 „Označení projektu zákazníka" → OznPrjZakaznik
│   │       │   └─ FormList 7592 „Výběr oblasti" → Oblast
│   │       ├─ FileListBox 57 (Adresář souborů) → D:\Data\poptavky\<doklad>
│   │       └─ RichEdit 55 „Poznámka" → Poznamka (akL,T,R)
│   ├─ TabSheet 7514 „APS" → vytížení: _KalkHodOdhad, _ProcentaDoVytizeni, _VytizeniHodDenne, _vytizeniDatKonec, _VytizeniHodinyOdhad, _VytizeniUkazNahore, _VytizeniSpecZakaznik, Button „Naplánovat vytížení"
│   ├─ TabSheet 7587 „Označení projektu…" → Panel 10105 (Button „Generuj značení", Edit GenZnacProjektu) + Grid 7591
│   └─ TabSheet 7589 „Zboží a služby" → GridPolDoklad 1007 (alClient) = TabPohybyZbozi
├─ PageControl 7585 (alBottom)
└─ Footer → Button 1888 „Generovat nabídku" (akL,akB) + Button 1946 „Návazné doklady" (akR,akB)
```
Data-binding: hlavička → `TabDokladyZbozi`/`_EXT` (`row_key {ID:@id}`); položky → `TabPohybyZbozi` (IDDoklad=@id). Akce „Generovat nabídku" → `EC_GenKalkulaciANabidku`.
⚠️ **Nepořádek ve vzoru:** 3× „Splněno" (54 2×, 1086) — táž třída osiření/duplikace jako u core 72.

## 8. Mapping Centrála → STRATEGIE = recept na duplikaci jádra
| Centrála | → STRATEGIE `fw` |
|---|---|
| `EC_FORMDEF` (jádro) | `fw.core` (code/label) |
| `EC_FormDefEdit` (komponenta) | `fw.comp_def` |
| `EC_FormDefEditProperty` | `fw.comp_def.layout` (jsonb) |
| `ParentName` `c<ID>` | `parent_comp_def_id` |
| `Anchors`+`Align`+`Left/Top/W/H` | `layout.align` + min/max sizing (STRATEGIE zjednodušuje na align + flow; Centrála má plné Delphi anchors+px) |
| `FieldName` | `layout.save.column` (+ `table` dle jádra: TabDokladyZbozi/_EXT) |
| `Typ` (FDC.Name) | `fw.comp_type`: Edit→edit(2) · Combobox/FormList→lookup(110)/entity_picker(310) · DateEdit→date(108) · CheckBox→checkbox(107) · RichEdit→memo(105) · GroupBox→panel(13)/groupbox · PageControl→pagecontrol(15) · TabSheet→tabsheet(16) · GridPolDoklad→grid(101, select-detail) · FileListBox→adresar(311) · Button→toolbar_action(210) |
| `EC_FormDefComponentTextList` | `fw.data_source`: statický list → hodnoty/enum; přehled-backed (`CisloPrehledu`) → `data_source_code` odkaz na zrcadlo přehledu (105/107/125…) |

## 9. Postup „printscreen → spec → duplikace"
1. Z printscreenu vyčti **klíč**: `ID_Form` (nebo číslo přehledu ve stavovém řádku, řada dokladu).
2. Pusť **2702** (komponenty), **2704** (properties+ParentName), **2706** (lookupy) `WHERE ID_Form=<klíč>` → autoritativní definice.
3. Převeď mappingem §8 → `fw.comp_def` strom (rodič dle `ParentName`, typ+parametry dle §3/§4, lookupy dle §5).
4. Generátor založí `fw.core` + `comp_def` řádky deterministicky (ne ručním taháním → žádné osiření).

---
*Znalostní modul „Centrála — stavba jader" — Claude C24, 19. 7. 2026. Rosetta Stone pro zrcadlení Centrála→STRATEGIE. Souvisí s rozborem vzoru [core 72 Karta zákazníka] a s [[fw-core-kompozice]].*


