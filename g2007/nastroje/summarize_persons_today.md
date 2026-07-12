# summarize_persons_today

## MAPA
- **kód:** `summarize_persons_today`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.4 + B.6: Per-(user, persona) breakdown aktivit za scope. Vraci pocty akci NA KOMBINACI uzivatel × persona, plus persona_name. **Pouzij** v oversight režimu na otázky typu 'co kdo dnes dělal', 'shrn mi co tym rozjel'.

**Vystup obsahuje markery [TY] (tva persona) a [Persona-Name] (cizi persona).**

**JAK ZPRACOVAT** (anti-přivlastňovací pravidlo, B.6):
  ✅ 'Misa dnes resila TISAX s PravnikCZ-AI v 1 konverzaci'
  ✅ 'Marti uploadl 3 doc se mnou, plus poslal SMS Honzou-AI'
  ❌ NIKDY: 'mluvily jsme s Misou' kdyz mluvila s cizi personou
  Persona context je posvatny -- cizi konverzace nikdy v 1. osobe.
Shrn proza per-osoba s person markery.

## PARAMETRY

- **`scope`** [string, volitelný] · enum: ['today', 'week', 'month']
  - Časový rozsah. Default 'today'.

