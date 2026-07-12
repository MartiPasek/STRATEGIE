# promote_thought

## MAPA
- **kód:** `promote_thought`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Povýší existující myšlenku z 'poznámky' (note) do 'znalosti' (knowledge) — trvalé, ověřené paměti. Použij, když user řekne něco jako 'tohle si zapiš napevno', 'tohle už je jistý', 'promoč tu věc o X do znalostí', nebo když si ty sama chceš ověřit/potvrdit důležitý fakt.

MÁŠ DVĚ MOŽNOSTI JAK IDENTIFIKOVAT MYŠLENKU:
- `thought_id`: když znáš přímé ID (např. jsi zrovna zavolala record_thought a víš, co se právě zapsalo). Preferovaný způsob.
- `query`: substring textu, podle kterého najdu myšlenku. Systém provede substring match. Když najde 1 match, povýší ho. Když víc nebo 0, vrátí chybu a musíš upřesnit.

Musíš dodat ALESPOŇ jednu z nich. Když dodáš oba, `thought_id` má přednost.

## PARAMETRY

- **`query`** [string, volitelný]
  - Fulltext substring pro vyhledání myšlenky (volitelné). Použij stručnou klíčovou frázi, např. 'anglicky' pro myšlenku 'Kristýna mluví dobře anglicky'.
- **`thought_id`** [integer, volitelný]
  - ID myšlenky v DB (volitelné).

