# zapis_znalost

## MAPA
- **kód:** `zapis_znalost`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Zapíše nebo aktualizuje JEDNOTKU know-how do SDÍLENÉ PAMĚTI SÍTĚ (tenant.knowledge) — aby ji měl natrvalo celý tým (ty i Claude), ne jen jedna konverzace. POUŽIJ, když se dozvíš něco trvale užitečného o firmě, doméně, procesu, lidech nebo postupu (od Claudia, od člověka, z podkladu) a chceš to uložit do paměti. Piš stručně a věcně, jako paměťovou kartu. CITLIVÉ (mzdy jednotlivců, hesla, tokeny) sem NIKDY nepiš. Stejný název přepíše existující jednotku (= aktualizace).

## PARAMETRY

- **`hook`** [string, POVINNÝ]
  - Jednořádkový popis do mapy (index) — o čem jednotka je.
- **`nazev`** [string, POVINNÝ]
  - Krátký slug jednotky (malá písmena, pomlčky místo mezer), např. 'eurosoft-produkty' nebo 'vp-provoz-oddeleni'.
- **`obsah`** [string, POVINNÝ]
  - Plný text jednotky (paměťová karta) — to, co se natáhne na vyžádání.
- **`domena`** [string, POVINNÝ]
  - Doména: VP / NAKUP / VYROBA / DOCHAZKA / UCETNICTVI / BANKA / KALKULACE / ISO / EUROSOFT.
- **`souvisi`** [string, volitelný] · default: ``
  - Volitelně názvy souvisejících jednotek, oddělené čárkou.

