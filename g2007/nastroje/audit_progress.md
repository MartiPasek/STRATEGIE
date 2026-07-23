# audit_progress

## MAPA
- **kód:** `audit_progress`
- **kategorie:** generated
- **v kufrech:** —
- **implementace:** `generated:audit_progress`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí přehled konverzací, které jsem auditovala za posledních N dní (default 7). Ukazuje kolik konverzací prošlo auditem per den. Slouží jako zpětné zrcadlo při slow audit workflow — list_unaudited_conversations říká co čeká, tento nástroj říká co jsem udělala.

## PARAMETRY

- **`days`** [integer, volitelný] · default: `7`
  - Kolik dní zpět hledat (default 7, max 90).

