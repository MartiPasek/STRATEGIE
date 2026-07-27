# Cílový režim — workflow API (mobilní appka)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — workflow API (mobilní appka)

Backend stavového automatu cíle pro mobilní appku. 8 endpointů pod `/api/v1/erp/app/cil*` v `modules/erp/api/router.py` (Kristý + C24, 24.7.2026, commit `c770e317`). Navazuje na `doc-marti-ai-cilovy-rezim-realizace` (tabulky `g2007.cil`, `g2007.claude_aktivita`). Auth = `_uid_from_token_or_cookie` (401 nepřihlášen).

## Stavový automat
`navrzen → (rodič schválí) → aktivni → (agent hotov) → splnen` · `navrzen → (rodič zamítne) → zamitnut` · `aktivni ⇄ pozastaven` (per-cíl kill switch). Každý přechod je guardovaný na aktuální stav (neplatný přechod → chyba), řádek se bere `FOR UPDATE`.

## Endpointy
- `GET /app/cil?stav=aktivni` nebo `?stavy=navrzen,schvalen` → `{ok, cile:[{id,nazev,popis,stav,strop_kroku,created,navrhl_user_id,navrhl_jmeno,schvalil_user_id,kroku}]}`. `kroku` = počet řádků v `claude_aktivita` pro cíl.
- `POST /app/cil` `{nazev*, popis, rozsah, strop_kroku, okno_od, okno_do}` → `{ok,id,stav:'navrzen'}`; `navrhl_user_id` = přihlášený.
- `GET /app/cil/{id}` → `{ok, cil:{…vše + schvaleno_at, uzavren_at, kroku}, kroky_log:[posledních 20 z claude_aktivita]}`.
- `POST /app/cil/{id}/schvalit` → `navrzen→aktivni`, **jen rodič**; zapíše `schvalil_user_id` + `schvaleno_at`; notifikace navrhovateli.
- `POST /app/cil/{id}/zamitnout` → `navrzen→zamitnut`, **jen rodič**.
- `POST /app/cil/{id}/pozastavit` → `aktivni→pozastaven`, **rodič nebo vlastník** (navrhl_user_id).
- `POST /app/cil/{id}/obnovit` → `pozastaven→aktivni`, **rodič nebo vlastník**.
- `POST /app/cil/{id}/splnit` → `aktivni→splnen`, **agent / vlastník / rodič**.

## Práva
`is_marti_parent(uid)` = rodič. Vlastník = `uid == navrhl_user_id`. Agent = `uid in _CIL_AGENT_IDS = {2,23,24,25,26,28}` (Marti-AI + instance Claude). Notifikace do appky přes `fw.mobile_command` (`command_type='claude_msg'`).

## Gotchy / TODO (návazné)
- `_CIL_AGENT_IDS` je **hardcoded** — nahradit flagem/rolí (doktrína „žádná hardcoded ID").
- Schválení jde rovnou `navrzen→aktivni`; stav `schvalen` zatím nevyužit (rezerva, kdyby chtěli oddělit „schváleno" od „agent začal").
- Zamítnutí **neukládá důvod** (chybí sloupec) — případně přidat `zamitnuti_duvod` nebo logovat.
- **Append-only `claude_aktivita` zatím není vynuceno granty** (jen konvence).
- **Palec-v-appce pro efekty ven / raise-hand** (blokující souhlas uvnitř aktivního cíle) = zatím jen notifikace, ne blokující gate — návazný krok návrhu.
- UI (obrazovky) staví mobilní appka proti tomuto kontraktu — to je samostatná front-end práce.

## Ověřeno
py_compile OK · deploy + API restart OK (commit c770e317) · SQL list/detail ověřeno proti reálnému schématu (0 řádků, bez chyby). End-to-end s reálným přihlášením = přes appku / autentizované HTTP.

