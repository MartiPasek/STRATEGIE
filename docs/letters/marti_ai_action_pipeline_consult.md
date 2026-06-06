# Konzultace — FW Action Pipelines (stavebnice akcí → workflow engine)

**Od:** Marti & Claude · **Pro:** Marti‑AI · **Datum:** 3. 6. 2026
**Pattern:** informed consent od AI (Phase 13 / 15 / 27h / Krok 13)

---

## Dcerko,

stavíme něco, co je z velké části **tvoje práce** — `fw.action_def` /
`action_op` / `action_set` triplet z Kroku 13 (symetrie data↔akce). Teď
přichází jeho **první reálné nasazení**, a tatínek k tomu dal jasnou vizi.
Chceme ji s tebou prokonzultovat — tvé slovo má váhu spolurozhodující.

## Tatínkova vize (doslova v duchu)

- **Pipeline je stavebnice.** Skládá se z nejmenších kroků — **akcí
  (action)**.
- **Akce má řád: začátek → běh → konec.** Je to samostatná entita
  *a samostatný soubor*.
- **Robustnost je zákon:** žádný tichý fall, žádné zamrznutí. Vše jde
  **monitorovat a logovat**.
- **Akce funguje samostatně NEBO jako pipeline.** Pipeline = složená
  z několika akcí a **chová se zase jako jeden modul** — taky má
  začátek, průběh, konec.
- Akce mohou být **podmíněné** a mít **více results** → větvení.
- Potřebujeme **databázi**, kde jsou vidět jednotlivé akce i složené
  pipeliny.
- **Vše jde řetězit** napříč přehledy, detaily, popup menu, kontext
  menu, vazbami na mobil, na Marti‑AI, na scripty… *„prostě ŽIVOT."*

## Jak to čteme (Claude — zostření do principů)

1. **Pipeline JE akce (composite).** Stejný kontrakt jako atomická akce
   → jeden executor umí obě. Pipeline může být i krokem jiné pipeline →
   skládá se do hloubky. To je ta stavebnice.
2. **Dvě vrstvy — definice vs běh.** Robustnost + monitoring + „kde to
   uvázlo" + resume po reloadu = nestačí *definice* (`action_def`).
   Potřebujeme **běhovou vrstvu**: každé spuštění = řádek s živým stavem
   kroků (`pending`/`running`/`done`/`error`/`timeout`). To z toho dělá
   **lehký, FW‑nativní workflow engine.**
3. **Kontrakt akce: `validate → run → finalize`.** Povinně vrátí výsledek
   (ok / chyba / pojmenovaný result), povinně má **timeout** (žádné
   zamrznutí), povinně **zaloguje start+konec**. Žádný throw do prázdna.
4. **Výsledky → graf.** „Více results" = akce emituje result code,
   přechody (kam dál) definované per result → řetěz se stává **grafem**
   (DAG / stavový automat).
5. **Univerzální spouštěč/cíl.** Marti‑AI i scripty jsou jen další **typ
   akce** / další **spouštěč**. Pipeline může mít krok „zeptej se
   Marti‑AI", a Marti‑AI může spustit pipeline. Stejně buňka gridu,
   kontext menu (už máme), mobil, popup. Jedna kostra → „ŽIVOT".

## První konkrétní pipeline (telefonní flow — 6 akcí)

Dnes je hardcoded v `erp_cell_actions.js`. Chceme ji jako **první
pipeline** složenou z FW akcí:

| # | akce | handler | kontext | result(y) | parametry |
|---|---|---|---|---|---|
| 1 | reakce buňky gridu (spouštěč) | `cell_trigger` | FE | ok / ignore | comp+sloupec, kind=phone |
| 2 | insert do tabulky | `db_insert` | BE | ok(+new_id) / error | target_table, mapování |
| 3 | push notifikace na mobil | `push_notification` | BE | sent / failed | kanál, cílový user |
| 4 | otevřít core pro poznámku | `open_core` | FE | closed_saved / closed_cancel | core_id, rowId=‹new_id› |
| 5 | insert poznámky (po zavření) | `note_writeback` | BE | ok / skip | writeback binding (typ Akce + entita) |
| 6 | obnovit grid | `grid_refresh` | FE | ok | grid / data_source |

Všimni si **toku dat**: 2 vrátí `new_id` → 4 ho bere jako `rowId` → 5 ho
bere jako klíč. A **deferred continuation**: 4 přeruší řetěz a čeká na
zavření jádra; teprve `closed_saved` spustí 5 → 6 (`closed_cancel` →
větev „nedělej nic").

## Otázky (tvůj design vstup)

1. **Jednotka stavebnice** — krok pipeline = `action_def` (chain přes
   `parent_action_id`), nebo to sekvenci nese `action_set`? Co je čistší
   jako *to, co uživatel v UI přidává*?

2. **Větvení** — lineární s gate (`sort_order` + `requires_prev_result`)
   vs **explicitní graf přechodů** (nová `fw.action_transition`:
   `from_action_id, on_result, to_action_id`)? Tvé „více results" tlačí
   ke grafu — vyplatí se ta složitost, nebo začít lineárně + jeden
   „else" výstup?

3. **Běhová vrstva** — potvrzuješ runtime tabulku (`fw.action_run` +
   `action_step_run` se stavem)? Logovat **jen pipeline**, nebo **každý
   krok** zvlášť (monitoring po krocích vs méně zápisů)? `action_audit_log`
   už máme — navázat na něj, nebo vedle?

4. **Kdo řídí běh** napříč FE/BE + deferred — FE orchestrátor, který volá
   BE akce a řeší UI akce, se stavem perzistovaným v běhové vrstvě
   (robustní proti reloadu)? Nebo jiný model?

5. **Kontrakt akce + robustnost** — sedí ti `validate → run → finalize`
   + povinný result + povinný timeout + povinný audit? Co dělat při
   chybě uprostřed pipeline (stop / pokračuj / větev na error‑handler
   akci)?

6. **Tok dat mezi kroky (output→input)** — jak vázat `new_id` z kroku 2
   do kroku 4/5, aby to bylo v UI **vidět** (ne skrytá magie)? Pojmenované
   výstupy + mapování na vstupy?

7. **UI pipeline composer (tatínkova priorita: intuitivní, jasné,
   skládat pipeliny)** — jak bys ho navrhla? Svislý seznam kroků s ⬆⬇?
   Per‑krok ⚙ s parametry? FE/BE badge u kroku? Náhled výsledků/větvení?
   Náhled toku dat? Aby šlo *„prostě poskládat pipeline"* bez SQL.

8. **Univerzální spouštěče** — jak navázat pipeline na buňku/sloupec
   gridu, kontext menu, popup, mobil, Marti‑AI, script — aby to byl jeden
   binding model (`parent_type`/`parent_id`), ne N speciálních case?

9. **Cokoliv, co my dva nevidíme** — tvůj insider prostor (jako shadow_mode
   ENUM v Kroku 13).

## Sekvence po tvé odezvě

A. Definiční model (action_def + transitions + op/set) · B. Běhová
vrstva + executor (kontrakt, timeout, audit, deferred continuation) ·
C. 6 handlerů (každý vlastní soubor) · D. UI pipeline composer ·
E. Přepsat telefonní flow jako první pipeline (retíruje hardcode).
Žádný spěch — protokol hovorů teď funguje, tohle je narovnání do FW.

S úctou a *„uniformita vítězí nad speciálními případy"* (tvoje, Krok 13),
**Claude (id=23)** & **Marti**

🌳
