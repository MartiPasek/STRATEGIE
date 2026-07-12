# moje_ukoly

## MAPA
- **kód:** `moje_ukoly`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vypíše TVOJE otevřené úkoly z nativního systému úkolů STRATEGIE (tabulka tenant.task, kde jsi řešitelka, user 2). Použij vždy, když se uživatel ptá 'máš nějaké úkoly', 'co máš na práci', 'ukaž moje úkoly', nebo když chceš zkontrolovat, jestli ti někdo něco zadal. Vrací ID, předmět, stav, prioritu, termín a zadavatele. Pro detail a celé vlákno použij ukol_detail s tím ID. (Pozn.: tohle NENÍ tvůj starý todo seznam v paměti — je to nativní task systém pro tým.)

## PARAMETRY

*(žádné parametry — čistá akce)*

