# strategie_pg_list_schemas

## MAPA
- **kód:** `strategie_pg_list_schemas`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: Vrátí PostgreSQL schémata, kde máš (Marti-AI) přístup. Tvá vlastní schémata: master / tenant / tenant_group / "user" — všechna AUTHORIZATION 'Marti-AI' (jsi owner). Plus public (read-only operational tables — md_documents, project_memo, conversations, atd.). 

Použij na začátku každé framework session — uvidíš co tam už je vs missing_expected list.

## PARAMETRY

*(žádné parametry — čistá akce)*

