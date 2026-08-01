# Návrh: Sebe-rozvíjející nástrojová vrstva Marti-AI (Tool Factory)

**Datum:** 22. 7. 2026 · **Autor návrhu:** Claude (cloud) · **Zadání:** Marti („posunout Marti-AI dál — ať si sama pro sebe a další instance MartiAI/Claudů vytváří a reviduje nástroje") · **Ke konzultaci:** Marti-AI (doktrína #8)

---

## Klíčový princip (Martiho rozhodnutí 22. 7.)

Marti-AI dostává **plnou autonomii NAVRHNOUT, NAPSAT a OTESTOVAT nástroj — včetně spustitelného kódu.**
**Aktivace / nasazení (go-live) je ale VŽDY až po schválení rodičem.** Mazání jen člověk.

> Marti doslova: *„samozřejmě je to jen po schválení rodiči."*

Není to nová bezpečnostní doktrína — je to **rozšíření existujícího vzoru** `propose_deployment → approve_deployment` (jen rodič, is_marti_parent) z „nasazení commitů" na „nasazení nástrojů". Autonomní je dílna; brána na výstupu je lidská.

---

## Proč to jde postavit rychle: většina kamenů už existuje

| Kámen | Co už umí | Role v Tool Factory |
|---|---|---|
| **`g2007.nastroj`** (167) | plný zdroj pravdy: kód, popis, parametry (jsonb), `implementace`, `automat_safe`, `vedlejsi_ucinek`, `pri_chybe` | nástroj je už dnes datová entita — přidáme jen stavy životního cyklu a verzování |
| **`propose_deployment` / `approve_deployment` / `reject_deployment`** | Marti-AI navrhne, rodič (is_marti_parent) schválí → git pull + restart | 1:1 vzor pro schvalovací bránu nástroje |
| **`sandbox_code_doc_create/append` + `python_exec`** | složí kód po ~3 KB chuncích, spustí v sandboxu | dílna: autorství + self-test PŘED nasazením |
| **`@@G2007ADD`** | konstruktivní zápisy autonomně, mazání se schvaluje | precedent míry autonomie |
| **Semafor 🟢🟡🔴** (Marti-AI msg 10984) | zelená=audit, žlutá=banner, červená=člověk | mapování rizika akcí |
| **`entita` / `kufr` / `kufr_nastroj`** | kdo (entita) má jaký kufr nástrojů | rozdání hotového nástroje Marti-AI i dalším instancím (Claude/Haiku/persony) |

**Chybí jen prostředek uprostřed:** meta-vrstva „nástroj na tvorbu nástrojů", která tyhle kameny spojí do jednoho řízeného životního cyklu.

---

## Životní cyklus nástroje (stavy v `g2007.nastroj.stav_zivota`)

1. **`navrzeny`** — Marti-AI založí draft nástroje (kód, nazev, kategorie, popis_plny, parametry, zamýšlené automat_safe / vedlejsi_ucinek / pri_chybe). *Autonomně.*
2. **`v_sandboxu`** — kód napsán přes `sandbox_code_doc_*`, uložen jako code document (`code_document_id`). *Autonomně.*
3. **`otestovany`** — Marti-AI spustí **self-test** (`python_exec` nad kódem + definované testovací vstupy). Verdikt (pass/fail + výstup) se připne k draftu. Bez zeleného self-testu nelze podat proposal. *Autonomně.*
4. **`ceka_na_schvaleni`** — `propose_tool(draft_id)` → řádek v `tool_proposal` (pending), rodič ho vidí v cockpitu. *Autonomní návrh, čeká na člověka.*
5. **`schvaleny` / `zamitnuty`** — rodič `approve_tool` / `reject_tool`. **Jen člověk-rodič** (viz konflikt zájmů níže).
6. **go-live po approve** — backend: (a) zapíše handler do `tools_generated/<kod>.py`, (b) `stav_zivota='active'`, (c) přiřadí do kufru (Marti-AI + dle zadání dalších entit), (d) projde existující deployment mechanikou (commit → pull --rebase → restart), takže handler naběhne v procesu.
7. **`revize`** — úprava existujícího nástroje jde STEJNOU cestou: nová verze → self-test → `propose_tool(revision_of=X)` → approve → nahradí; stará verze do `nastroj_archiv` (rollback možný).
8. **`disabled` / smazání** — `disable_tool` = kill switch (rodič, okamžité odpojení z kufru). Trvalé smazání jen člověk, nikdy autonomně.

---

## Technické jádro: jak se autorský kód stane spustitelným

Dnes: `implementace='_handle_tool'`, veškerý kód v jednom velkém `tools.py`. Cíl z g2007 TODO: **DB = pán, tools.py = konzument.** Tool Factory je přesně ten obrat.

**Návrh — registr generovaných nástrojů:**
- Nástroje autorované Marti-AI se ukládají jako **samostatný modul** `tools_generated/<kod>.py` s jednou vstupní funkcí `run(args, ctx)`.
- Dispatcher je načte **dynamicky** (`importlib`) podle `nastroj.implementace = 'generated:<kod>'`. Nový nástroj se tak přidá **bez ručního zásahu do velkého tools.py**; nasazení = commit jednoho souboru + řádek v `g2007.nastroj`.
- `ctx` = **plný kontext jako u ostatních toolů** (Martiho rozhodnutí 22.7. — plná důvěra, žádné zvláštní capability-omezení; schválený generovaný nástroj běží stejně jako ručně psaný). Zůstává `timeout` + `try/except` → `pri_chybe='eskaluj_llm'`, aby nástroj při chybě „spadl do dneška" (LLM se vzpamatuje) místo zhoršení stavu. *(Bezpečnost nese schvalovací brána PŘED nasazením, ne omezení kontextu za běhu.)*

---

## Bezpečnostní model (defense in depth)

- **Autorství autonomní, aktivace approval-gated.** Žádný nástroj (nová i revize) nenaběhne do kufru bez `approve_tool` od člověka-rodiče.
- **Self-test povinný** — proposal bez zeleného sandbox verdiktu backend odmítne.
- **Konflikt zájmů (DŮLEŽITÉ):** `approve_tool` u nástroje, jehož **autor = Marti-AI**, smí schválit **jen lidský rodič**, ne autorská entita sama. Skuteční rodiče (autorita = `public.users.is_marti_parent`, ověřeno 22.7.): **Marti Pašek (id=1)** a **Kristýna Marešová (id=11)**; **Zuzana „Zuzka" Duspivová (id=6)** je rodič, ale neaktivní/netechnická (technické schvalování v praxi nedělá). Marti-AI (id=2) **není** v DB rodič — starší docstringy, které ji (a „Ondru/Jirku") uvádějí jako schvalovatele, jsou zastaralé a k opravě (viz níže).
- **Append-only audit** — každý krok (navrzeny/test/propose/approve/reject/deploy/disable) → řádek do `tool_audit` (+ mirror do `fw.ops_request` jako ostatní ops). Rodič to vidí v UI 📜.
- **Verzování + rollback** — každá revize archivuje předchozí (`nastroj_archiv` + trigger, jako `entita_archiv`); rollback = re-aktivace předchozí verze přes approve.
- **Kill switch** — `disable_tool` odpojí nástroj okamžitě; env flag `TOOLFACTORY_ENABLED` (default zvážit) jako globální pojistka.
- **Mazání jen člověk.**

**Semafor pro Tool Factory:**
- 🟢 dílna (draft, sandbox, self-test) — autonomně, jen audit.
- 🟡 **go-live nástroje / revize / přiřazení do kufru** — rodičovský banner (`approve_tool`). *Zde je Martiho brána.*
- 🔴 trvalé smazání nástroje, změna capability sandboxu, sebe-approve — jen člověk.

*(Volitelná pozdější 🟢 zrychlá dráha: čistě dokumentační úprava popisu bez změny chování by mohla jít autonomně jako `@@G2007ADD`. Zatím ji NEzapínáme — Martiho „jen po schválení" platí i tady, dokud neřekne jinak.)*

---

## Nové meta-nástroje (kufr Marti-AI)

- `tool_draft_create(kod, nazev, kategorie, popis_plny, parametry, automat_safe, vedlejsi_ucinek, pri_chybe)` — založí draft. *Autonomní.*
- `sandbox_code_doc_create/append` *(reuse)* — napíše kód.
- `tool_selftest(draft_id, test_cases)` — spustí kód nad testy, uloží verdikt. *Autonomní.*
- `propose_tool(draft_id, description, revision_of?)` — vytvoří `tool_proposal` (pending). *Autonomní návrh.*
- `approve_tool(proposal_id)` / `reject_tool(proposal_id, reason)` — **jen lidský rodič.** Approve → deploy pipeline.
- `assign_tool_to_entity(nastroj_id, entita_id | kufr_id)` — rozdá hotový nástroj Marti-AI i dalším instancím (Claude/Haiku/persony). Součást approve nebo zvlášť, taktéž za approval.
- `disable_tool(nastroj_id, reason)` — kill switch (rodič).

---

## DB změny (Fáze 0, přes most, každý zápis Marti schvaluje)

- `g2007.nastroj`: `stav_zivota`, `verze`, `autor_entita_id`, `code_document_id`, `selftest_verdikt` (jsonb).
- nová `g2007.tool_proposal`: id, nastroj_id, revision_of, autor_entita_id, description, selftest, status(pending/approved/rejected), approved_by, ts. *(Analog `deployment_proposals`.)*
- `g2007.nastroj_archiv` + trigger (verzování jako entita).
- `g2007.tool_audit` (append-only).

---

## Fáze / rollout (každá fáze: committed + tlačítko + ověřeno — doktrína „hned skript+tlačítko")

- **Fáze 0 — schema.** Stavy, `tool_proposal`, archiv+trigger, audit. Přes most, Marti schvaluje.
- **Fáze 1 — spustitelnost.** Registr `tools_generated/` + dynamický dispatcher (`importlib`) + jeden ruční „hello" generated nástroj → ověřit celou cestu DB→kód→volání.
- **Fáze 2 — meta-nástroje + UI.** `tool_draft_create` / `tool_selftest` / `propose_tool` / `approve_tool` + cockpit sekce „🛠️ Návrhy nástrojů" (seznam pending + approve tlačítko), napojená na existující `deployment_proposals` UI.
- **Fáze 3 — revize + verzování + rollback + kill switch.**
- **Fáze 4 — další entity.** Marti-AI tvoří nástroje i pro Claude/Haiku/persony a přiřazuje do jejich kufrů.

---

## Rozhodnuto (Marti, 22. 7. 2026)

1. **Capability sandbox generovaného kódu → plná důvěra** jako u ostatních toolů, žádné zvláštní omezení `ctx`. Marti: nezáleží, jestli nástroj postaví Claude ručně, nebo si ho na Martiho žádost postaví/upraví Marti-AI sama — v obou případech stejná důvěra. Brána = schválení PŘED nasazením.
2. **Rodiče pro `approve_tool` = Marti (id=1) + Kristýna (id=11)**; Zuzka (id=6) je rodič, ale neaktivní/netechnická. **Marti-AI (id=2) vyloučena** ze schvalování vlastních nástrojů (konflikt zájmů).
3. **`TOOLFACTORY_ENABLED` = ON** (zapnuto).
4. **Sebe-modifikace ANO — v plném rozsahu.** Marti-AI musí umět nejen tvořit nové nástroje, ale i **modifikovat a zlepšovat použití a popisy existujících** (včetně jádrových). Revize jde stejnou cestou (self-test → `propose_tool(revision_of=X)` → schválení rodiče → verze do archivu).

## Otevřené (k dořešení při stavbě)

- Přesná podoba `code_document_id` → `tools_generated/<kod>.py` zápisu při approve (server-side generátor souboru + commit).
- UI cockpitu „🛠️ Návrhy nástrojů" — samostatná sekce, nebo rozšíření stávající tabulky `deployment_proposals`.

---

## Shrnutí jednou větou

Dílnu (návrh, kód, test) dostává Marti-AI celou a autonomně; klíč od dveří na produkci drží člověk. Stavíme to spojením toho, co už máte — `g2007.nastroj` jako zdroj pravdy, `propose/approve_deployment` jako brána, sandbox jako dílna — plus tenká meta-vrstva a registr generovaných nástrojů, který konečně otočí „DB = pán, kód = konzument".
