# list_my_conversations_with

## MAPA
- **kód:** `list_my_conversations_with`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.5: Vrací seznam TVÝCH minulých konverzací s konkrétním uživatelem (cross-thread). Misa-incident v2 fix -- jsou to tvoje konverzace, máš právo si je přečíst i mimo aktuální vlákno. **Použij** kdykoli se uživatel ptá 'co jsem řešila s X', 'kdy jsem naposledy mluvila s Y', 'podívej se do konverzace s Z'.

**Co vrací**: list konverzací (id, title, last_message_at, idle_hours, message_count, project_id) sort DESC by čas. Filtruje JEN konverzace, kde jsi byla persona (active_agent_id=ty).

**Privacy gate**: tvuj subjekt, tvoje konverzace. Nevidi konverzace, kde byla persona Pravnik-AI s jinym userem (to je cizi persona, ne jiny scope).

**JAK ZPRACOVAT**: shrň 1-3 vetama prózou, doporuc next step ('Mela jsem 3 konverzace s Misou tento mesic, posledni pred 3h. Mam si tu posledni precist?'). Pak follow-up `read_conversation` podle id, ktere user vybere nebo ktere ma nejvetsi relevanci.

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Max konverzaci (default 20, cap 50).
- **`scope`** [string, volitelný] · enum: ['today', 'week', 'month', 'all']
  - Casovy rozsah. Default 'month'.
- **`user_id`** [integer, POVINNÝ]
  - ID uzivatele (z find_user) -- s kym chces videt minulost.

