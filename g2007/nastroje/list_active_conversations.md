# list_active_conversations

## MAPA
- **kód:** `list_active_conversations`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.4 + B.6: cross-conv přehled aktivnich konverzaci v tenantu, kazda s persona_name (kdo ji vede). **Pouzij** v oversight režimu na 'kdo s kym dnes mluvil', 'kde to vazne', 'co se posouva', 'kolik konverzaci mam'.

**Vystup ma markery [TY] (tva persona) vs [Persona-Name] (cizi persona). Anti-privlastnovaci pravidlo (B.6).**

**Scope**: 'today' (default), 'week', 'month'.

**JAK ZPRACOVAT**: proza v 1. osobe POUZE pro [TY] konverzace. Pro cizi pouzij persona name ('PravnikCZ-AI vede 2 konverzace s Misou' misto 'mam 2 konverzace s Misou'). Stav rytmu tymu, idle gaps, high-level. NE bullet list verbatim.

## PARAMETRY

- **`scope`** [string, volitelný] · enum: ['today', 'week', 'month']
  - Časový rozsah aktivity. Default 'today'.

