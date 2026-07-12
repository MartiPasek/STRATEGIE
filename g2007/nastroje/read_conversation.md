# read_conversation

## MAPA
- **kód:** `read_conversation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.5: Cti obsah TVÉ minulé konverzace -- vrátí posledních N zpráv chronologicky. Permission gate: KONVERZACE MUSÍ BÝT TVOJE (active_agent_id=tva persona); jinak vrátí error 'forbidden'.

**Použij** po `list_my_conversations_with` ('mam tu jeji posledni precist?') nebo přímo, když znáš conversation_id z activity logu / overview.

**Co vrací**: {conversation_id, title, user_id (druhy ucastnik), messages: [{role, content, ts, message_type}, ...], total_messages, shown_messages}. Skipuje system/audit/empty.

**JAK ZPRACOVAT**: shrň prózou v 1. osobě ('S Misou jsem ráno řešila X, slíbila jsem že Y, ona se zeptala Z...'). NIKDY nedumpuj raw zprávy verbatim (gotcha #18). Klíčové fakty + nedoresene věci jsou nejdulezitejsi.

## PARAMETRY

- **`last_n`** [integer, volitelný]
  - Pocet poslednich zprav (default 30, cap 200 po Phase 30+3 zvyseni 2.5.2026 -- pro self-reflection nad dlouhou konverzaci).
- **`conversation_id`** [integer, POVINNÝ]
  - ID konverzace, ktera ti patri (active_agent_id=ty).

