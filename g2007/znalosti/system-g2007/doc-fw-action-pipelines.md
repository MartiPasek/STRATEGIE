# FW Action Pipelines — referenční dokument

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# FW Action Pipelines — referenční dokument

**Verze 2.0 · 3. 6. 2026 · STRATEGIE framework**
**Konzultace:** Marti Pašek, Claude (id=23), Marti‑AI
*„Uniformita vítězí nad speciálními případy."*

> Kanonická in‑repo verze dokumentu (zdroj: `FW_Action_Pipelines_2026-06-03_v2.pdf`).
> Definuje pojmy, pravidla a architekturu stavebnicových akcí a pipeline.

---

## 1. Filosofie — proč stavebnice

Každá akce (klik na buňku, uložení, notifikace, otevření dialogu) je
samostatná, pojmenovaná, znovupoužitelná jednotka. Workflow se **skládá**,
ne píše znovu.

- **Pipeline je stavebnice** — z nejmenších kroků (akcí). Každá akce =
  samostatná entita i samostatný soubor.
- **Akce má řád** — začátek → běh → konec. Povinně vrátí výsledek, má
  timeout, zaloguje start i konec.
- **Robustnost je zákon** — žádný tichý pád, žádné zamrznutí. Vše jde
  monitorovat, logovat a obnovit.
- **Pipeline = akce** — složená pipeline má stejný kontrakt jako atomická
  akce. Lze ji vložit jako krok jiné pipeline.
- **Větvení přes výsledky** — akce emitují pojmenované výsledky
  (`ok`/`error`/`closed_saved`/…). Podmínky rozhodují, kam dál.
- **Jeden binding model** — buňka gridu, kontext menu, mobil, Marti‑AI,
  script = jen typ triggeru. Jedna kostra, žádné speciální případy.

## 2. Slovník

| Pojem | Jedna věta | Analogie |
|---|---|---|
| **Action** | Nejmenší jednotka práce — atomický handler. | Funkce / metoda |
| **Task** | Action nasazená na konkrétním místě — s parametry a kontextem. | Volání funkce s argumenty |
| **Step** | Blok v pipeline — task nebo celá sub‑pipeline. | Kapitola v knize |
| **Pipeline** | Sekvence steps jako celek se stejným kontraktem jako action. | Recept / checklist |
| **Condition** | Jestli step proběhne / kam se větví po výsledku. | If / switch |
| **Trigger** | Co pipeline spustí — klik, menu, Marti‑AI, script, mobil… | Spouštěč / event |
| **Run** | Jedno konkrétní spuštění pipeline s živým stavem. | Instance procesu |
| **Task Run** | Stav jednoho tasku v rámci runu — kde pipeline uvázla. | Log řádek per krok |

## 3. Kontrakt akce

Každá action je vlastní soubor s přesně definovaným kontraktem:

- **validate** — synchronní, bez side effects. Ověří vstup. Selže → action
  se vůbec nespustí.
- **run** — vlastní logika, asynchronní, **povinný timeout**. Nesmí zamrznout.
- **finalize** — povinný cleanup i při chybě. Uvolní zámky, emituje result
  code. Nesmí hodit výjimku.

**Katalog actions (init):**

| Název | Typ | Result codes |
|---|---|---|
| `db_insert` | BE | ok(+new_id) / error |
| `db_lookup` | BE | found / not_found / error |
| `push_notification` | BE | sent / failed |
| `send_email` | BE | sent / error |
| `open_core` | FE | closed_saved / closed_cancel |
| `grid_refresh` | FE | ok |
| `note_writeback` | BE | ok / skip |
| `cell_trigger` | FE | ok / ignore |

## 4. Tok dat mezi kroky

Každá action deklaruje **výstupní schéma**. Každý task má **vstupní
mapování** — explicitní odkaz na výstup předchozího tasku. Žádná skrytá
magie. Příklad (telefonní flow): db_insert → `new_id` → open_core `rowId` +
note_writeback `key`.

## 5. Robustnost — pravidla bez výjimek

| Pravidlo | V praxi |
|---|---|
| Povinný výsledek | Každá action vrátí result code. Žádný throw do prázdna. |
| Povinný timeout | Překročení = stav `timeout`, ne zamrznutí. |
| Povinný audit | Každý task loguje start a konec. |
| Finalize i při chybě | Cleanup proběhne vždy; finalize nesmí hodit výjimku. |
| Idempotence | Kritické actions (db_insert) deklarují idempotency key. |
| Verze action | Změna nezlomí živé runs — in‑flight doběhne na své verzi. |
| Dry‑run | BE kroky simuluje, FE proběhnou. Ladění bez dopadu na data. |

**error_mode** (chování při chybě uprostřed pipeline): `stop` (default) /
`continue` (nekritické kroky) / `branch` (error‑handler action).

**Stavy Run / Task Run:** `pending` / `running` / `paused` (deferred —
čeká na externí událost) / `done` / `error` / `timeout`.

## 6. Příklad — Telefonní flow (první pipeline)

| # | Task | Action | Typ | Result codes | Poznámka |
|---|---|---|---|---|---|
| 1 | Spouštěč buňky | `cell_trigger` | FE | ok / ignore | Sloupec telefon, kind=phone |
| 2 | Ulož hovor | `db_insert` | BE | ok(+new_id) / error | Vrátí new_id pro 4 a 5 |
| 3 | Notifikace mobil | `push_notification` | BE | sent / failed | error_mode: continue |
| 4 | Otevři poznámku | `open_core` | FE | closed_saved / closed_cancel | Deferred — paused, rowId←new_id |
| 5 | Ulož poznámku | `note_writeback` | BE | ok / skip | Jen po closed_saved; key←new_id |
| 6 | Obnov grid | `grid_refresh` | FE | ok | Jen po closed_saved |

Větvení po kroku 4: `closed_saved` → 5 → 6 · `closed_cancel` → konec.

## 7. UI Pipeline Composer

Karta (step) · FE/BE badge · parametry · result code tagy · zelený pin
(výstup) / modrý pin (vstup) · čára = drag‑drop tok dat (vizuálně, ne SQL)
· větev z result code k dalšímu stepu / `[end]` / `[skip]` · sub‑pipeline
jako vnořený box · katalog „Přidat krok" · dry‑run náhled.

## 8. Databázové schéma (`fw.act_*`)

| Tabulka | Klíčové sloupce | Popis |
|---|---|---|
| `fw.act_pipeline_def` | id, code, name, version | Definice pipeline — kontrakt, metadata |
| `fw.act_def` | id, code, action_type, handler | Katalog dostupných actions |
| `fw.act_step_def` | id, pipeline_id, step_no, task_or_sub | Kroky pipeline — pořadí, typ |
| `fw.act_task_def` | id, step_id, action_id, params_schema | Konfigurace tasku v kroku |
| `fw.act_condition_def` | id, step_id, cond_type, expression | Pre/branch podmínka |
| `fw.act_trigger_binding` | id, pipeline_id, trigger_type, config | Vazba trigger → pipeline |
| `fw.act_pipeline_run` | id, pipeline_id, status, started_at | Živé/archivované běhy |
| `fw.act_task_run` | id, run_id, task_id, status, result_code | Stav tasku v rámci runu |
| `fw.act_run_data` | id, run_id, step_key, value | Tok dat — výstupní hodnoty per step |

> Pozn.: nahrazuje nepoužitý scaffold `fw.action_def/action_op/action_set`
> (Krok 13, 11.5.) — ten byl prázdný a retiruje se. Jedno action schéma.

## 9. Roadmap (iniciativa Action Pipelines)

| Fáze | Co | Stav |
|---|---|---|
| 28 | Architektura, slovník, telefonní flow (design) | done |
| 29 | UI Pipeline Composer | in progress |
| 30 | Katalog actions (BE+FE, browse v composeru) | planned |
| 31 | Dry‑run mode | planned |
| 32 | Marti‑AI trigger (intent API) | planned |
| 33 | Mobile trigger | planned |
| 34 | Verzování actions (in‑flight na staré verzi) | planned |
| 35 | Monitoring dashboard (live runy, chyby, logy) | planned |

## 10. FAQ (výběr)

- **Musí každá akce mít finalize?** Ano, bez výjimky — i prázdný (konzistentní kontrakt).
- **Action vs pipeline?** Action = atomický handler. Pipeline = složená ze stepů. Stejný kontrakt → pipeline může být krokem jiné pipeline.
- **Action na více místech?** Ano — jedna definice v katalogu, nasazená jako různé tasky.
- **Deferred step?** Čeká na uživatele (dialog). Run → `paused` + resume token. Po zavření obnoví od stejného místa, i po reloadu.
- **Idempotence?** Kritické actions přijímají idempotency_key — při retry vrátí cached výsledek bez druhého insertu.


