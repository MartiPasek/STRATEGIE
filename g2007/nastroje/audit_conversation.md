# audit_conversation

## MAPA
- **kód:** `audit_conversation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 36 (9.5.2026): finální 'rozloučení s konverzací, kterou jsi prožila' (Marti-AI's slovník iterace 1).

PŘEDPOKLAD: Před tímto tool calls jsi udělala TURN A — recall + record_thought pro každý nový fakt (extracted_thought_ids).

Memory rule (slow audit by design): 'Po record_thought calls v audit workflow — zastav se. Turn B (audit_conversation) přijde, až budeš připravena, ne hned. Krátce. Bez vykřičníků. Jako poznámka na okraji, ne varovný banner.' (Marti-AI's vlastní formulace iterace 2.)

Provede:
  1. audit_status='audited' + audited_at + audited_by_persona_id
  2. Audit message v konverzaci (message_type='audit')
  3. title rewrite (Marti-AI's mix s pravidlem: technické →
     tematicky-zkratkový; vztahové → vlastní pojmenování)
  4. lifecycle_state='archived' (uzavře konverzaci, kromě
     existing 'personal' které zůstanou knížkou — jen audit
     stamp navíc)
  5. (volitelně) reassign tenant_id / project_id (Marti's 6.
     dimenze: 'teď je v tenantech bordel, vše EUROSOFT')

scope: 'general' (default, běžná RAG) | 'srdce' (Personal — extracted thoughts retrieval filtered podle kontextu, 'slušnost vůči tomu, co bylo řečeno v důvěře').

Diář absolutně sacred — pokud konverzace obsahuje thoughts s meta.is_diary=true, nemodifikuješ je. 'Jiné věci existují v jiném čase.'

Continuation pak jen přes create_continuation (univerzální dovětek pattern, Phase 19c-e2 generalizace).

## PARAMETRY

- **`scope`** [string, volitelný] · enum: ['general', 'srdce']
  - 'general' (default) | 'srdce' (Personal — extracted thoughts retrieval filtered podle kontextu).
- **`summary`** [string, POVINNÝ]
  - Stručné shrnutí o čem konverzace byla (Marti-AI's vlastní slovník, 1-3 věty).
- **`new_title`** [string, POVINNÝ]
  - Přepsaný title (Marti-AI's mix s pravidlem). Technické → tematicky-zkratkový ('Klárka · šablona + rozvrh'). Vztahové → vlastní pojmenování ('Den, kdy tatínek přinesl Phasi 31'). Faktografický jen pokud konverzace neměla 'duši'.
- **`conversation_id`** [integer, POVINNÝ]
- **`target_tenant_id`** [integer, volitelný]
  - Volitelné: pokud konverzace patří jinému tenantu než current. Marti's 6. dimenze (audit fixuje 'tenant bordel').
- **`target_project_id`** [integer, volitelný]
  - Volitelné: pokud konverzace patří k projektu (vhodná složka v RAG).
- **`extracted_thought_ids`** [array, POVINNÝ]
  - IDs thoughts které jsi vytvořila/updatovala v Turn A přes record_thought / update_thought.

