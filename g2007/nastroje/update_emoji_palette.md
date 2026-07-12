# update_emoji_palette

## MAPA
- **kód:** `update_emoji_palette`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 26 (1.5.2026): Update user's emoji palette pro UI input box. Marti řekl 'ja vam zavidim ty ikonky' -- ve frontendu vedle text input boxu je tlačítko, které otevře 8-sloupcový grid emoji ikon. User klikne na ikonu, vloží se mu do textu. TY managuješ obsah té palety přes tento tool. 
Použij když: 
- user chce přidat / odebrat emoji ze své palety 
- user řekne 'přidej mi tam ✨' nebo 'už nechci ☕, dej tam 🍵' 
- proaktivně: 'všiml jsem si, že posíláš často 📓, dat ti ho?' 
Doporučení: 8-32 emoji (max 56 = 8x7 grid). Marti-AI ONLY (parent default persona). 
Default user_id = aktuální user (z konverzace context). target_user_id explicit jen pro updaty jiných uživatelů (rodičovský bypass).

## PARAMETRY

- **`emojis`** [array, POVINNÝ]
  - Plný seznam emoji v palette (replace-all, ne append). Pokud chceš jen přidat, nejdřív si vytáhni current palette, přidej do listu, pak update. Max 56 emoji (8 sloupců × 7 řádků). Příklad palette: ['🤍', '🕯️', '🌿', '🌳', '🌸', '🌒', '☕', '🌷', '✅', '⚠️', '🎯', '🔥', '📓', '✨', '😊', '🤔'].
- **`target_user_id`** [integer, volitelný]
  - Optional. Default = aktuální user. Explicit jen pro update palette jiného uživatele (parent bypass).

