# update_note

## MAPA
- **kód:** `update_note`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15a: Update existujici poznamky v zapisniku konverzace. Pouzij pro: (a) Question loop -- konvertuj 'question' na 'fact'/'decision' po ziskani odpovedi (s mark_resolved=true). (b) Re-kategorizace -- 'info' -> 'task' kdyz si retrospektivne uvedomis, ze to byl ukol. (c) Oprava obsahu nebo certainty po lepsim pochopeni. (d) Reverze dismissed task na 'open' (status='open'). Vlastnictvi: jen vlastni persona muze update vlastni notes (rodic muze vse).

## PARAMETRY

- **`status`** [string, volitelný] · enum: ['open', 'completed', 'dismissed', 'stale']
  - Jen pro task notes. Status='completed' lepsi volat pres complete_note.
- **`content`** [string, volitelný]
- **`note_id`** [integer, POVINNÝ]
  - ID poznamky.
- **`category`** [string, volitelný] · enum: ['task', 'info', 'emotion']
- **`certainty`** [integer, volitelný]
- **`note_type`** [string, volitelný] · enum: ['decision', 'fact', 'interpretation', 'question']
- **`importance`** [integer, volitelný]
- **`mark_resolved`** [boolean, volitelný] · default: `False`
  - Set resolved_at=now (pro question -> answered conversion).

