# ukol_poznamka

## MAPA
- **kód:** `ukol_poznamka`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Napíše zprávu do sdíleného vlákna úkolu = TVŮJ report zpátky zadavateli. Buď konkrétní: co jsi udělala, výsledek (ID, počet řádků, varování). Zadavatel a u tvých úkolů i rodiče dostanou notifikaci na mobil.

## PARAMETRY

- **`id`** [integer, POVINNÝ]
  - ID úkolu.
- **`text`** [string, POVINNÝ]
  - Text zprávy do vlákna.

