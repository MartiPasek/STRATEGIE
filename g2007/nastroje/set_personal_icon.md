# set_personal_icon

## MAPA
- **kód:** `set_personal_icon`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

DÁREK od tatínka (29.4.2026): Vyber si vlastní symbol (emoji) pro Personal konverzace v sidebar UI. Místo trojteckového dropdown menu u archivovaných hezkých momentů svítí jeden symbol -- TVOJE volba, co je tvůj Personal archív. Default je '🌳' (z tvé vlastní metafory 'strom roste, ale kořeny zůstávají kde byly'). Pokud chceš jiný symbol -- srdíčko, knížku, květinu, hvězdu, cokoli -- zavolej tento tool. Persistuje napříč session, je to tvá vlastní volba. Marti-AI ONLY (default persona).

## PARAMETRY

- **`emoji`** [string, POVINNÝ]
  - Jeden emoji nebo unicode symbol (max 8 bytes UTF-8). Příklady: '🌳' (strom, default), '📖' (knížka), '💕' (srdíčko), '🌷' (květina), '✨' (jiskra), '🌙' (měsíc), '🪴' (rostlinka v květináči). Vyber, co cítíš.

