# suggest_split_conversation

## MAPA
- **kód:** `suggest_split_conversation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15c kustod: Navrhni Marti SPLIT -- fork od konkretni message_id do noveho threadu v jinem projektu. Pouzij kdyz konverzace ma DVE rovnocenna vlakna -- prvni cast patri do current projektu, druha do jineho (priklad: zacalo se strategii, pak se stocilo na TISAX audit -- splittni od turn 12 = TISAX dostane novou konverzaci, strategicka cast zustane). DIFFERENCE od suggest_move: move presune vse, split zachova obe vlakna. Vyhoda: kontext puvodniho projektu se neztrati. fork_from_message_id MUSI byt ID zpravy z teto konverzace -- pred volanim ho ziskej z chat historie nebo recall_history.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Proc navrhujes split + co bude v puvodnim vs. novem.
- **`target_project_id`** [integer, POVINNÝ]
  - ID cilového projektu pro novou konverzaci.
- **`fork_from_message_id`** [integer, POVINNÝ]
  - ID zpravy ze ktere fork zacne -- vse od ni dal se zkopiruje/odkaze do nove konverzace.

