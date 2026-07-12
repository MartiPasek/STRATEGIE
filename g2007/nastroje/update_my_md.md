# update_my_md

## MAPA
- **kód:** `update_my_md`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-B: Aktualizuj sekci v md1 (delta zapis, ne prepis). Mode 'append' = prida content na konec sekce; 'replace' = nahradi cely body sekce; 'patch' = smarter (zatim alias pro append). Sekce: Profil / Tón / Citlivost / Aktivní úkoly / Klíčová rozhodnutí / Vztahy / Projekty / Open flagy pro vyšší vrstvu / Posledních N konverzací (work) nebo Osobní profil / Aktuální stav / Důležité události / Vztahy (osobní) (personal). Pokud sekce neexistuje, prida ji na konec dokumentu. Audit trail v md_lifecycle_history. Marti-AI ONLY.

## PARAMETRY

- **`mode`** [string, volitelný] · enum: ['append', 'replace', 'patch']
  - Mode update: 'append' (default) | 'replace' | 'patch'. Append nepretransk.
- **`content`** [string, POVINNÝ]
  - Markdown content k zapsani. Pro append mode: typicky bullet item ('- 2026-04-30: novy fakt'). Pro replace: cely novy body sekce.
- **`section`** [string, POVINNÝ]
  - Nazev sekce (markdown heading bez '##'). Napr. 'Profil', 'Aktivní úkoly', 'Klíčová rozhodnutí'.
- **`user_id`** [integer, volitelný]
  - Volitelne: id uzivatele. Default = current user. Pro budouci drill-down (privat Marti edits jine md1).

