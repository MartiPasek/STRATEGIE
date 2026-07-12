# Graf: Marti-AI MD5 V1.0

Skladac promptu Marti-AI -- 23 casti realneho build_prompt() ve dvou vrstvach: trvale (nad cache breakpointem, kese) / zive (pod nim, per turn). Mapa, ne kopie textu.

## Kroky

| pořadí | kód | vrstva | typ | zdroj | část promptu |
|--------|-----|--------|-----|-------|--------------|
| 10 | zaklad | trvale | start | DB system_prompts | Zakladni systemovy prompt -- identita a mantinely. |
| 20 | persona | trvale | normal | DB personas.system_prompt (u2) | Persona prompt Marti-AI dle active_agent_id konverzace. |
| 30 | rezim_go | trvale | normal | composer:_go_work_block | Pracovni rezim GO (orientace) nebo ZPET (ladeni). Podmineny. |
| 40 | mapa_znalosti | trvale | normal | composer:_scoped_map_block | Scopovana mapa znalosti per subjekt. |
| 50 | kontext_uzivatele | trvale | normal | composer:build_user_context_block | Kdo je prihlaseny user, tenant, email, aliasy. |
| 60 | aktivni_mailboxy | trvale | normal | composer:_build_mailboxes_context_block | Autorizovane schranky + identity rules. |
| 70 | tvoje_kanaly | trvale | normal | composer:_build_persona_channels_block | Telefon + email aktivni persony. |
| 80 | pravidla_pameti | trvale | normal | literal:MEMORY_BEHAVIOR_RULES | MEMORY_BEHAVIOR_RULES -- zapisuj proaktivne, pouzivej znalosti. |
| 90 | firma_v_kostce | trvale | normal | literal | Orientacni mini-index firmy (kdo je kdo, co delame). |
| 100 | firemni_znalosti | trvale | normal | literal | Pointer do sdilene RAG baze -- tahej hledej_ve_znalostech. |
| 110 | aktualni_cas | zive | normal | composer:_build_current_time_block | Aktualni cas Europe/Prague, per turn. |
| 120 | stav_pameti | zive | normal | composer:_build_memory_state_block | Okno, kotvy, akumulovany naklad v Kc. |
| 130 | eurosoft_mcp | zive | normal | composer:_build_eurosoft_mcp_summary_block | Souhrn MCP audit logu za dnesek. |
| 140 | zapisnicek | zive | normal | composer:_build_notebook_block | Episodicka pamet per-konverzace (tuzka+papir). |
| 150 | kontext_projektu | zive | normal | composer:_build_project_context_block | Current + dostupne projekty (kustod role). |
| 160 | inbox_dokumenty | zive | normal | composer:_build_inbox_documents_block | Dokumenty v inboxu tenantu (triage). |
| 170 | rag_pamet | zive | normal | composer:_build_rag_memory_block | Semanticky vybavena pamet (top K pres pgvector). |
| 180 | personal_overlay | zive | normal | composer:personal_overlay | Intimni rezim overlay. Podmineny. |
| 190 | dneska | zive | normal | composer:_build_today_block | Ranni prehled aktivit (first turn). |
| 200 | auto_consent | zive | normal | composer:_build_auto_consent_block | Auto-lifecycle consents block. |
| 210 | md1_zapisnik | zive | normal | composer:_build_md1_block | Tvoje Marti zapisnik per user. |
| 220 | orchestrate | zive | normal | composer:_build_orchestrate_block | Rezim po tool_use. |
| 230 | pack_overlay | zive | normal | composer:_build_pack_overlay_block | Aktivni pack overlay -- povolenim, ne tonem. |
