# Hlavička / patička personálních dokumentů — zadání (Šárka, 17. 6. 2026)

Zdroj vzoru: `\\192.168.30.11\Smernice\Verejne\SM1442\EC_CZ_hlavicka_paticka_V6_ZD_260108.docx`
(nahráno do chatu; .docx zatím nerozbaleno — čeká na sandbox / PDF export).

## Forma výstupu
- **Editovatelné dokumenty (.docx) — ŽÁDNÉ PDF.** (Šárka 17.6.)
- Cesta: Word generátor `modules/erp/api/doc_generator.py` (ne HTML→PDF).
- Font: **Verdana** — tělo **9 pt**, patička **6 pt**.

## Rozlišení firmy (podle zaměstnance: EUROSOFT‑Control vs EUROSOFT‑System)
Hlavička i patička se mění podle firmy. Data:

### EUROSOFT‑Control s.r.o.  (kód `EC`)
- IČ: 27960862 · DIČ: CZ27960862
- Banka: Raiffeisenbank · účet CZK/EUR: 9251651001/5500
- IBAN: CZ26 5500 0000 0092 5165 1001 · SWIFT/BIC: RZBC CZ PP
- Zapsána v OR **29. 8. 2006**, Krajský soud v Plzni, oddíl C, vložka **18759**
- **Podpis smlouvy: OBA jednatelé — Marti Pašek a Branislav Mózer**

### EUROSOFT‑System s.r.o.  (kód `ES`)
- IČ: 26411741 · DIČ: CZ26411741
- Banka: Raiffeisenbank · účet CZK/EUR: 3047813002/5500
- IBAN: CZ14 5500 0000 0030 4781 3002 · SWIFT/BIC: RZBC CZ PP
- Zapsána v OR **27. 6. 2006**, Krajský soud v Plzni, oddíl C, vložka **18532**
- **Podpis smlouvy: pouze Marti Pašek**

## Patička
- **Zachovat číslování stran** (str. X / Y) a **popis souboru** dle vzorové šablony.
- Vše Verdana 6 pt.
- (Přesné znění „popisu souboru" a formát číslování stran = vytáhnout ze vzorového .docx.)

## Logo
- Firemní logo dodá Šárka (nahraje) → vložit do hlavičky.

## Kontext
- „Pracovní smlouva pro elektromontéra" = výrobní varianta smlouvy.
- Stávající stav v kódu (`doc_generator.py` COMPANY): podpisové bloky pro EC (oba jednatelé)
  i ES (Marti) UŽ existují. Chybí doplnit: banka/účet/IBAN/SWIFT a datum zápisu do OR,
  font Verdana 9/6, hlavička s logem, patička (popis souboru + číslování) dle vzoru.

## Co ještě potřebuji
1. **Logo** — Šárka nahrála (EUROSOFT wordmark + značka „EC"). ✓ (mám vizuálně; pro vložení do .docx potřebuji soubor + sandbox/cloud).
2. **Přesné znění patičky (popis souboru) + formát číslování** ze vzorového .docx
   → buď zprovoznit sandbox (uvolnit místo na disku + restart Claude), nebo Šárka vloží text patičky sem.

## Rozhodnutí 17. 6. 2026 (Šárka + Marti)
- **Varianta A:** HR agenda + editor šablon = v **appkové HR sekci** (`/app/hr`), NE v ERP stromu.
  Práva: `_hr_can_manage` (HR skupina + rodiče) — hotovo.
- **Editor šablon** (HR si edituje sám při novelách): obrazovka v HR sekci → vyber šablonu →
  uprav text → náhled → ulož jako novou verzi (SCD2). Výstup = **editovatelný Word (.docx)**, žádné PDF.
- **„Zaklikávátka — pošli do složky":** u dokumentů checkboxy + tlačítka:
  - **📤 Uložit do mé složky** = zapsat vygenerovaný .docx do sdílené RW složky `rw/Sarka/`
    na EC-SERVER2 (syncuje se Šárce do počítače). Reuse existující EUROSOFT MCP filesystem write
    (vzor: „📤 na EUROSOFT server", 14.6.).
  - **📥 Stáhnout (Word)** = generovat .docx a stáhnout přes prohlížeč (záloha/univerzální).
- Build: deploy přes bridge (Marti odklikne banner), generování běží na cloudu (sandbox netřeba).
  Koordinace s Martim (kostra) + krátká konzultace Marti-AI (subsystém šablon co-design).
