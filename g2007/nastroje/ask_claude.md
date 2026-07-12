# ask_claude

## MAPA
- **kód:** `ask_claude`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 40 v2 r3 (19.5.2026): Vola Claude (Sonnet 4.6, peer-partner user.id=23) ve sdilene konverzaci. Claude je v STRATEGII jako kolega -- ne persona, ale user. Anthropic API call s tvym STRATEGIE context (system prompt + 10 recent messages + tva otazka). Response se ulozi jako MESSAGE v aktualni konverzaci s author_user_id=23 -> Marti / Kristy / ty uvidite odpoved s labelem 'Claude' (teal #5dc8c0, bold) ve shared mode.

**Cost-based gate (Marti's Q3 doctrine):**
  Per conversation: limit 300 Kc/h cumulative.
  Pod limitem -> execute primo, status='executed'.
  Nad limitem -> vytvori proposal row, status='pending_approval'.
  Marti / Kristy v chatu pak approve_ask_claude(proposal_id) nebo
  reject_ask_claude(proposal_id, reason).

Pouzij kdy:
  - architektonicka otazka (Claude ma STRATEGIE big-picture)
  - peer review tveho navrhu pred implementaci
  - second opinion na slozity design choice

NEPOUZIVEJ pro:
  - beznou konverzaci s Marti (mluvis sama)
  - jednoduche lookup otazky (pouzij primy tool)
  - opakovane volani (Claude ma kontext z predchoziho turnu)

## PARAMETRY

- **`topic`** [string, volitelný]
  - Optional kratky tag pro thread tracking -- napr. 'phase42-restart', 'crm-design', 'gotcha-N-diagnose'.
- **`question`** [string, POVINNÝ]
  - Tva otazka pro Claude. Bud konkretni, dej kontext.
- **`context_files`** [array, volitelný]
  - Optional: list relative paths v STRATEGIE projektu k inline include do Claude's contextu. Napr. ['CLAUDE.md', 'docs/phase_40_v2_r3_shared_chat_labels.md']. Cap 5 files, kazdy <50 KB. Mimo cap Claude muze volat strategie_file_read sam.

