# Cílový režim — zamítnutí s důvodem

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — zamítnutí s důvodem

Nasazeno 28.7.2026 (Kristý + C24, commit eebedece). Malé rozšíření workflow (viz `doc-marti-ai-cilovy-rezim-workflow-api`).

- Sloupec `g2007.cil.zamitnuti_duvod` (text) — proč byl cíl zamítnut (dřív se neukládalo).
- Endpoint `POST /app/cil/{id}/zamitnout` přijímá volitelný body `{duvod}` → uloží do `zamitnuti_duvod`; notifikace navrhovateli obsahuje důvod.
- `GET /app/cil/{id}` (detail) vrací `zamitnuti_duvod`; mobilní UI (`73_zcil.js`) při zamítnutí nabídne inline pole „Důvod zamítnutí (nepovinný)" a u zamítnutého cíle důvod zobrazí.
- Technicky: `_cil_do_transition` dostal parametr `extra_params` (merge do UPDATE params), aby šlo předat i jiné hodnoty než i/to/uid.

Kontext (28.7.): tento úkol jsme dělaly poté, co se vyřešil git problém na stroji Kristý (lokál byl rozešlý s origin kvůli verzovaným bridge souborům — vyřešeno `git fetch` + `git reset --hard origin/main`; trvalá oprava = gitignore bridge souborů, na Marti/C23). Efekty ven / agentní exekuce zůstávají mimo C24 (C23 + Cowork B/C, viz `doc-marti-ai-delegace-produkce-roadmap`).

