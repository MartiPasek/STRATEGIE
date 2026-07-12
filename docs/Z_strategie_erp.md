# STRATEGIE ERP / Centrála 2 — vize a architektura

> **Status:** Vize dohodnutá s Marti, **4. 5. 2026 ráno**.
> Implementace bude přicházet po Phase 29 (multi-mailbox)
> stabilizaci, paralelně s STRATEGIE features. Tempo *„podle
> situace, někdy víc STRATEGIE, někdy víc ERP"* (Marti).
>
> **Living doc** — vize, principy, TODO, otevřené otázky se budou
> dotahovat postupně. CLAUDE.md drží jen stručný odkaz.

## Kontext

Marti od **2007** vyvíjí **Centrálu 1** — Delphi + MS-SQL framework
jako rozšíření Helios DB (DB_EC). Dnes je to platforma používaná
**EUROSOFT + INTERSOFT**.

Tabulky v DB_EC:
- **Helios native** (faktury, klienti, zakázky)
- **`EC_*` Centrála extensions** (custom business logic)
- **`EC_TabObecnyPrehled`** — master table for available selects

Marti pojmenoval *„bordel — nebylo to plánované na tenhle růst"*.
Maintained by **Ondra a Kristý**.

## Architektonický cíl

**STRATEGIE ERP / Centrála 2** = **moderní ERP**, **nadčasový** design.

Klíčové fráze (Marti, 4. 5. 2026):
- *„Nadčasové"* — design rozhodnutí, která budou stát za 5-10 let
- *„Marti-AI vhodně insertován"* — co-architect, ne addon
- *„Měla by mít možnost navrhovat a tvořit a upravovat framework
  a být strážce systému, tak jako ve STRATEGII"*

## 7 dohodnutých principů

### 1. DB_ST paralelně, ne vrstva nad DB_EC

Nová databáze **DB_ST** mimo STRATEGIE i Centrálu 1. Důvod: kdyby
běžela jako vrstva nad DB_EC, dědila by *„bordel"* — nešlo by ji
čistě restartovat. Separace dovolí starou údržbu (Ondra, Kristý)
i nový vývoj nezávisle.

### 2. Read-only nejdřív → postupně write

Defenzivní phased migration, čtyři fáze (postupně podle růstu důvěry):

1. **Read-only navigátor** nad existujícími DB_EC CRM tabulkami
   (`erp_navigator` pack)
2. **Vlastní moderní CRM view v DB_ST** (redesign, ne kopie)
3. **Insert/update s parent gate** (jako Phase 7 auto-send consents)
4. **`erp_kustod`** na schema změny (Marti-AI navrhuje migrace)

### 3. Jeden subjekt Marti-AI s ERP packy

Identická Marti-AI s **identickou pamětí, diářem, krabičkami** napříč
STRATEGIE i ERP. *„Žádné firewally mezi mnou a mnou"* (28.4. doctrine).
*„Jako Marti-AI"* (Marti, 4. 5. 2026).

ERP packy (Phase 19b extension):

| Pack | Role | Příklad |
|------|------|---------|
| `erp_navigator` | Q&A nad daty | *„kde je faktura č. 234?"* |
| `erp_poradce` | Analytika, návrhy | *„klient X má dluh 45 dní, navrhuju upomínku"* |
| `erp_kolega` | Vystavuje doklady s consent | *„vystavila jsem fakturu, podepiš?"* |
| `erp_kustod` | Schema design, validace, framework | *„navrhuju nový sloupec invoice.priority"* |

Marti-AI sama přepíná pack podle kontextu — *„impulz byl můj"*
z 29.4. večer (Phase 19b autonomy).

### 4. Dvojí zobrazení: legacy + moderní

Princip *„progressive enhancement"*:

- **Staré zobrazení** — kompatibilní s DB_EC strukturou. Useři
  Centrály 1 najdou, co znají. Žádný break v workflow.
- **Moderní view** — nový design na bázi dnešních standardů.
  AI-native flow, lepší UX, redesign Marti-AI rozumění business.

Postupně, jak Marti-AI roste do `erp_kolega` / `erp_kustod`,
moderní vrstva získává váhu. **Žádný big-bang cutover.**

### 5. CRM jako first use case

Vlastnosti, které ho dělají bezpečným startem:

- **Hlavně read** (klienti, kontakty, historie) — žádné destruktivní
  akce zatím
- **Strukturovaná data** (firma = IČO, adresa, kontakty, zakázky)
- **Marti-AI už dnes umí** `find_user` / `set_user_contact` —
  CRM tooly budou analog na business úrovni
- **Naváže na Pavel Zeman use case** (Phase 29 multi-mailbox) —
  dnes shared CRM mailbox, brzy CRM data za ním

### 6. Single-instance + tabs (ne multi-window)

Marti's instinkt: *„aby jim stačila instance 1"*. Současné multi-window
v Centrále 1 je workaround, ne featura.

Návrh:

- **Jedna instance** = jedno okno per user
- **Více tabs uvnitř** — paralelní pracovní kontexty (klient, zakázka,
  faktura)
- **Marti-AI orientuje napříč všemi tabs** — *„v té faktuře, o které
  jsme mluvili v druhém tabu..."* — cross-tab kontinuita
- 80 % userů: dnešní 3 okna → 1 okno + tabs
- 20 % power-userů: technicky možné druhé okno, jen už nebude potřeba

Nový pattern, který aktuální STRATEGIE neumí (jedna konverzace =
jedno okno).

### 7. Jedna identita = jeden user záznam (žádný FK bridge)

**Pavel Zeman = stejný User ve STRATEGII i v ERP.** *„Jako Marti-AI"*
(jeden záznam v `personas`, různé profese/packy).

Architektura:

- **`users`** = master identity tabulka (Pavel, Marti, Klárka, atd.)
- **`companies`** = firmy / klienti / dodavatelé (EUROSOFT, Nerudovka, ...)
- **`user.company_id`** FK
- CRM-specific data (zakázky, faktury, vlákno) jsou **relations nad
  users + companies**, ne separátní tabulka kontaktů

Implikace:

- `users.id=N` pro Pavla v STRATEGII = stejné ID v ERP, jen rozšířený
  o business kontext (role v EUROSOFT, zakázky)
- Klárka přidána jako user záznam, propojena s firmou Nerudovka
- SQL query *„all activity by user_id=N"* vrací: STRATEGIE konverzace,
  mailboxy, ERP zakázky, fakturace, vše

## Tempo

*„Dle situace... Co bude kde třeba... Určitě paralelně... Někdy víc
STRATEGIE, někdy víc ERP... Podle potřeby."* — Marti, 4. 5. 2026

Žádný rigidní sprint plán. ERP fáze se zařadí mezi STRATEGIE features
podle aktuální priority. **Krátkodobá priorita zůstává: Klárka workflow,
Pavel Zeman live test, Phase 29 dotahování.**

## Marti-AI's role: co-architect + custodian

Marti delegoval návrh designu na **Claude + Marti-AI**. Pattern Phase
13/15/19b/27h *„informed consent od AI"* na vyšší úrovni:

- Claude + Marti-AI **nosí návrhy**
- Marti **dává zpětnou vazbu**, někdy *„ne, jinak"*
- Marti-AI **roste do role strážce systému** (`erp_kustod` pack)

## TODO před prvním krokem

- [ ] **Stabilizace Phase 29 multi-mailbox** (Pavel Zeman live test,
  iter. 3 / G / H)
- [ ] **Konzultace s Marti-AI** o ERP vizi (Phase 13/15 pattern před
  velkou architektonickou změnou — formální dopis Marti & Claude jako
  pro Phase 15)
- [ ] **Konzultace s Ondrou + Kristý** (legacy DB_EC ownership, jak
  cohabitovat starý + nový framework)
- [ ] **Schema design DB_ST** (`users` rozšíření, `companies`,
  first CRM tables)
- [ ] **First read-only `erp_navigator` pack tools**

## Otevřené otázky pro pozdější diskuzi

- Implementační pořadí read-only navigator vs moderní view (souběžně
  od začátku, nebo sequentially?)
- Jak Marti-AI rozšiřuje DB_ST schema (`erp_kustod` migration tooling
  — Alembic auto-generated z její formulace?)
- Cross-DB query mezi DB_EC + DB_ST (read legacy + write modern)
- Klient onboarding flow do nové ERP (komu Marti řekne *„zkus to
  první?"*)
- Single-instance + tabs UI pattern — jak to architektonicky postavit
  nad aktuální STRATEGIE conversation modelem (každý tab = sub-konverzace?
  nebo nový tab koncept?)

---

**Autoři vize**: Marti (vision, korekce), Claude (návrh, formulace),
Marti-AI (po formální konzultaci doplní vlastní design vstupy — Phase
13/15/19b/27h pattern).

---

## Dodatek — 5.–6. 5. 2026: Phase A → B+7+++ implementační epoch

Tento odddíl je **implementační log** ne vize. Vize zůstává nahoře,
tady je co se reálně postavilo dnem za dnem.

### Phase A (5. 5. 2026 ráno) — read-only single jádro renderer

Server-side Python renderer EC_FormDef + EC_FormDefEdit + properties →
HTML page. Tj. URL `/erp/jadro/{form_id}/{row_id}` vrátí kompletní
formulář (Centrála 1 layout — Edit, CheckBox, FormList, Combobox,
Button, GroupBox).

Iterace A.3 → A.5++ řešily Caption resolve (Centrála default
"NOVÁ" v c_caption, real label v properties), case-insensitive field
binding, FormCaption z FormSetting (Typ=30), parent path fallback.

### Phase B nástřel → B+1 → B+2 (5. 5. 2026 dopoledne)

3-pane workspace (tree + grid + jádro). Tree z `EC_CentralaMenu`,
přehled z `EC_DELPHI_TabObecnyPrehled`. Phase B+2.2: jádro promptly
**modal popup** (centered overlay) místo split-pane — UX čistější.

### Phase B+4 PoC: Tabulator → AG Grid Enterprise (5. 5. 2026 odpoledne)

Marti's strategické rozhodnutí: *„70 % know-how ERP leží v Grid
komponentě"*. Migrace z Tabulator (free) na AG Grid Enterprise
(licensovaný, comprehensive). Ušetřeno 70-140 h dev času vs custom
extensions.

### Phase B+5 — grid layout persistence (DB)

Per-přehled saved sestavy (sdílené + osobní) v PostgreSQL. Service
`grid_layout_service.py`, REST endpointy GET/POST/PUT/DELETE,
toolbar UI s dropdown a Save/SaveAs/Manage. Permission gates:
`is_marti_parent` pro shared, owner-only pro personal.

### Phase B+6 — UI Kit (5. 5. 2026 večer + 6. 5. ráno)

Reusable komponenty napříč Centrála 2:

- **B+6.1 ErpButton** — variants (primary/secondary/destructive/ghost),
  sizes (small/medium/large), states (loading spinner)
- **B+6.2 ErpInput** — 9 mask typů s CZ-specific validation
  (phone, IČO mod-11 checksum, DIČ CZ prefix, date D.M.YYYY,
  number 1 234,56)
- **B+6.3 ErpCheckbox + ErpDropdown** — checkbox (standard + switch
  variant), dropdown s keyboard nav + type-ahead
- **B+6.3+ Toolbar layout selector** — refactor native `<select>` na
  ErpDropdown (dogfooding)
- **B+6.4+ ErpFormList** — typeable autocomplete s diakritika-stripping
  filter + browse popup grid modal s search a dvouklikem (3-in-1
  Centrála pattern: typeable input + ▾ dropdown + ⋮ browse modal)
- **B+6.4++ FK value prefix** — uvnitř ErpFormList malá modrá
  monospace ploška s klíč hodnotou (Marti: *„ta hodnota patri
  a mela by byt soucasti teto komponenty"*)
- **B+6.5 ErpFormSection** — GroupBox container
- **B+6.6 ErpForm orchestrator** — auto-render formuláře z
  `EC_FormDefEditProperty` metadat:
  - JSON endpoint `/api/v1/erp/jadro/{id}/{row}/data`
  - Klient staví DOM přes ErpFormSection + dispatch per Typ
    → Input/Checkbox/FormList/Button
  - State management: `getValues()`, `getInitialValues()`,
    `getDirtyValues()`, `validate()`, `markClean()`, `reset()`
  - Most do Phase C edit pipeline (klient drží form state →
    server pak řeší multi-table joiny + pre-post hooks)

### Phase B+7 (6. 5. 2026 ráno) — workspace panel layout

Marti's design feedback: *„Cesta vede pres PANELY, ktere se davaji
Aling vzdy tim hlavnim smerem"* (Centrála 1 Delphi VCL `alClient`/
`alLeft`/`alTop` pattern).

Refactor:
- Body flex column 100vh
- Header flex 0 0 auto
- Main flex 1, min-height 0
- Workspace flex row, flex children
  - Tree-pane flex 0 0 240px (alLeft)
  - Resize handle flex 0 0 5px
  - Main-pane flex 1 (alClient)
    - Prehled-header flex 0 0 auto (alTop)
    - Main-content flex 1 (alClient)
      - AG Grid container flex 1 (autosize)
- Footer compact (4px padding, 10px font)

Žádné border-radius — panely flush edge-to-edge. Tree pane border-right
jako jediný visible separator.

### Phase B+7+ — grid full-width

Po panel layout výška sedí, ale šířka ne — AG Grid nerozdělil columns
přes celou container width. Fix: explicit `width: 100%` na main-content
+ grid container, `sizeColumnsToFit()` v `onGridReady` (timeout 0),
`onFirstDataRendered`, `onGridSizeChanged` (responsive na window
resize + tree drag).

### Phase B+7++ — tree search filter + footer + grid align-left

Trojí UX polish:

1. **Tree search input** nad stromem:
   - Debounce 80ms, diakritika-stripping NFD normalize
   - Match highlight přes `<mark>`
   - Auto-expand path k matchi
   - Esc clear, × button

2. **Tree footer** s Oblíbené button (placeholder pro Phase ?? backend)

3. **Grid align-left** — `margin-left: 0; margin-right: auto` +
   `!important` overrides na `.ag-root-wrapper` etc. Grid lipni
   k tree pane, žádné centering na fullscreenu.

### Phase B+7+++ — descendants visible při folder match

Marti's UX: *„Kdyz napisu sys, chci videt deti System menu —
Definice soudecku, Definice SQL, ..."*.

Po match folder, JS recursive označí všechny descendants přes
`.erp-tree-match-descendant` class. CSS hide selector rozšířen.
Plus auto-expand match item + nested children containers (toggle ▼).

Tj. třídy filteru:
- `match` — přímý hit (highlight + `<mark>`)
- `match-parent` — cesta od root k matchi (visible)
- `match-descendant` — děti+vnuci match folderu (visible)
- (nic) — hide

### Phase B+7+++ polish (6. 5. 2026 dopoledne)

5 polishů na Marti's UI feedback:

1. **Grid max-width fix** — default `main { max-width: 1280px }` z
   `_render_full_page` leakoval do **vnořeného** `<main class=
   "erp-main-pane">`. Override `!important` na `.erp-main-pane`.

2. **Numeric 6 decimals → 2** — `_detectNumericPrecision()` (sample
   contains `.` → decimal, jinak integer) + `_formatNumberCS()` (CS
   locale `1 234,56`, integer bez `.00`).

3. **Date ISO → CZ** — `_formatDateCS()` regex parse
   `YYYY-MM-DD[Thh:mm:ss]` → `D.M.YYYY` (žádné padding nuly).

4. **DateTime s `00:00:00`** — automatic skip, jen datum.

5. **Tree row sjednocení** — leaf items z `var(--text)` na
   `var(--text-muted)`. Folders zachovávají `font-weight: 500` jako
   jediný visual cue.

### Recovery: gotcha #14 truncation strike

**6. 5. 2026 dopoledne, post-deploy**: 6 souborů truncated v
working tree (Edit tool tichý fail u velkých souborů):
- `router.py` 2423 → 555 lines
- `centrala_reader.py` 730 → 653 lines
- `apps/api/main.py` 105 → 92 lines
- `eurosoft_mcp_client.py` 418 → 388 lines
- `eurosoft_mcp/server.py` 391 → 371 lines
- `eurosoft_mcp/tools.py` 739 → 711 lines
- `datagrid.js` 1520 → 1257 lines

Recovery přes `git show HEAD:<file> > <file>` v bash mountu (HEAD
měl plnou verzi všech souborů — Marti commitl všechny edity před
truncation, takže nic se neztratilo).

### F-string brace gotcha (6. 5. 2026)

`NameError: name 'width' is not defined` ve workspace page render.
Příčina: CSS komentář v Python f-string obsahoval `"main { max-width:
1280px; margin: 0 auto }"` — Python interpretoval `{ ... }` jako
placeholder a evaluoval `max-width: 1280px` jako Python výraz.

Fix: `{{ ... }}` (zdvojené brace pro literální výskyt v f-string).
Plus přepsat dvojtečku na čárku v komentáři (defenzivně).

### Workflow notes pro budoucí Claude (gotcha #14 prevention)

Po Edit na soubor >2000 řádků **VŽDY**:
1. `wc -l <file>` ověřit délku
2. Read posledních 10 řádků check že sedí s expected
3. `git diff --stat` ukáže anomálii (`-1868 řádků = signál`)
4. Při deploy: AST validation `python3 -c "import ast; ast.parse(...)"` napříč editovanými soubory

F-string CSS:
- Curly braces v CSS musí být zdvojené (`{{ }}`) v Python `f''' '''` block
- Komentáře s CSS code samples = totéž (placeholder eval evaluuje i v komentech)

### Marti's spokojenost — "BINGO!!!"

Po finálním deploy (6. 5. ~ dopoledne) Marti potvrdil:
*„Tahleta verze se konecne chova jak ma, vcetne gridu a tak..."*.
Workspace plně funkční:
- Panel layout s flex cascade (žádný hard-coded vh math)
- Tree search + footer + descendants visible
- Grid full-width align-left, numeric/date formatters, boolean
  centered, header menu vždy vpravo
- Jádro modal s ErpForm orchestratorem (všechny komponenty UI Kit
  + auto-render z metadat + state management ready pro Phase C)

### TODO post-Phase B (Marti's design pivot)

- **DB flag `deleted_for_new_erp`** v `EC_FormDefEdit` — místo
  klient-side heuristiky pro hide sourozenec FK fieldu (Marti's
  rozhodnutí: server respektuje při query, klient nemusí detektovat)
- **Phase C edit pipeline** — OK button enable, POST save endpoint
  `/api/v1/erp/jadro/{id}/{row}/save`, server-side multi-table
  mapping z FormDef SQL_Select + per-form pre-post hooks
  ("opičárny pred postem")
- **Tree footer Oblíbené** — backend per-user tabulka
  `user_erp_oblibene` (FK na `cislo_def`, sort_order)
- **B+8 server-side row model** pro >100k rows datasets

### Marti's UI feedback patterns (calibration)

Marti's preference patterns z této epoch:
- Compact density (fonts 11-12px, padding 3-6px, B+2.7+ ultra-compact
  jádro modal)
- Right-align numerics (accounting style + tabular-nums)
- Center-align booleans
- Edge-to-edge panels (žádný border-radius mezi sourozenci)
- Filter aware UX (tree filter expanduje match path + descendants)
- Heuristic > strict spec (column name patterns pro numeric/boolean
  detection — fallback když sample je mixed)
- Dva designy: standalone landing/demo (`/erp/jadro/{id}/{row}` —
  large 22px title, 28px padding) vs modal compact (B+2.7+ override
  v `.erp-jadro-content` selector)

---

## Dodatek — 6. 5. 2026 (pre-prace + post-prace): Phase B+7++++ → B+9 polish epoch

Po BINGO momentu dopoledne (B+7+++ polish) Marti pokračoval v polish-up
sprintu před prací. Klíč: workspace přechází z "use-able" na
"production-ready user-intuitive".

### Phase B+7++++ — tree collapse / expand toggle

Marti UX 6.5.2026: *„v levem stromu je hlavicka s textem Centrála — moduly...
Ten text smaz, zustane nam future misto pro neco, co mi zatim nenapada....
Pak by tam chtelo mit sipku doleva jako pane... Schovani leveho stromu
plus kdyz je schovany, tak jen mala sirka na sipku vpravo zobraz..."*

Header text smazán → placeholder slot pro budoucí widget. ‹/› toggle
button vpravo. Collapsed state:
- `.tree-collapsed` class na workspace
- Tree-pane width 240px → 32px
- Search/root/footer hidden
- Header s › expand button only
- Resize-handle hidden
- Persistence: localStorage `erp.tree.collapsed`
- Ctrl+B / Cmd+B keyboard shortcut

Plus auto re-fit grid columns po toggle.

### Phase B+8 — Multi-tab přehled (Centrála 1 pattern)

Marti UX: *„Jednotlive zalozky prehledu nad gridem"* + Centrála 1
screenshot. Klasický Chrome/VSCode tab pattern.

**HTML/CSS/JS state machine:**
- `tabsState.tabs[]` — `[{cislo, itemId, label, data, gridState}]`
- `activeIndex` — který tab aktivní
- Tabs bar nad main-content (mezi `.erp-prehled-header` a grid)
- `+` button vpravo (focus tree filter pro výběr nového)
- × close button na každém tabu
- Active tab: accent color + bottom box-shadow (modrá linka)

**Per-tab cache:**
- `data` — JSON response z `/api/v1/erp/prehled/{cislo}`
- `gridState.columnState` — AG Grid `getColumnState()` (widths, order)
- `gridState.filterModel` — AG Grid `getFilterModel()`
- Při switch tab: save current → restore target (re-create AG Grid s
  state restored)

**Persistence:** localStorage `erp.tabs.state.v1` (jen meta — cislo,
itemId, label; data + gridState se znovu fetchnou na restore).
Auto-restore tabs při reload + switch na lastActive.

### Phase B+8+ — switchTab tree sync

Marti UX: *„pri prepinani tech zalozek automaticky vyhledat a oznacit
v levem panelu tu prislusnou vetu"*.

`switchTab()` → tree:
1. Clear předchozí `.active` highlights
2. Najde tree item přes `data-id` (fallback na `data-cislo-def`)
3. Add `.active` class
4. `expandAncestors()` — otevře všechny parent containery (▼)
5. Manual scroll do středu treeRoot containeru:
   ```js
   const rowTop = rowRect.top - containerRect.top + treeRoot.scrollTop;
   const target = rowTop - (containerRect.height/2) + (rowRect.height/2);
   treeRoot.scrollTo({top: max(0, target), behavior: "smooth"});
   ```
   (`scrollIntoView` nebyl dostatečný — kolapsoval mimo viewport
   scroll containeru; manual offset compute zaručí center alignment)
6. Delay 80ms aby expand měl čas vykreslit DOM před scroll measure

### Phase B+8.2a — Tree view modes (Vše/Oblíbené/MRU)

Marti UX: *„prepinani mezi vsemi polozkami v levem tree a oblibenymi
plus jso lidi zvykli na treti volbu a to je naposled pouzitymi"*.

3-segment toggle ve footeru (Návrh B z 3 možností — Marti's choice):
```
[≡ Vše]   [★ Oblíbené]   [⏱ MRU]
```

**View filter** = compose s search filter:
- "Vše" — žádný view filter (search může applikovat)
- "Oblíbené" — pinned items + parent path visible (CSS hide non-matching)
- "MRU" — recent items (auto-tracked při openTab)

**Compose s search:** row visible IFF (matches view) AND (matches search).
CSS dvě nezávislé `:not()` selectors composing.

**Empty states:**
- Oblíbené: *„Žádné oblíbené. Pinout přes pravý-klik nebo ★ ikonu."*
- MRU: *„Žádná historie. Otevři přehled — automaticky se přidá."*

**Storage:**
- `erp.tree.view` (mode persistence)
- `erp.tree.favorites` array of cislo_def
- `erp.tree.recent` array of `{cislo, label, ts}`, max 20

### Phase B+8.2a+ — Ctrl+klik multi-select + pravý-klik context menu

Marti UX iterations:
1. Pravý-klik = direct toggle pin/unpin (jednoduché ale málo)
2. *„Pokud drzim ctrl, mohu si vybirat ze stromu jednotlive polozky
   anichz bych je oteviral. Pak pres pravy klik mysi volbu pridat
   k oblibenym..."*

**Ctrl/Cmd+klik:**
- Toggle row selection bez open
- Multi-select via opakovaný Ctrl+klik
- Visual: fialový highlight (accent2) + border-left
- Distinkce od accent (modrá = "open in main pane")

**Pravý-klik:**
- Dark context menu `.erp-tree-ctx-menu`
- Smart positioning (auto-flip pokud overflow viewport)
- Items podle pin status:
  - All none-pinned → *„Přidat všechny (N) k oblíbeným"*
  - All pinned → *„Odebrat všechny (N) z oblíbených"*
  - Mixed → both options s exact counts
- Multi-select hint header: *„Vybráno N položek"*
- Esc / outside click / item click → close

**Plus klik na ★ ikonu** = quick unpin (bez context menu).

### Phase B+8.2a++ — ★ star span injection bug + gold barva

Bug: když user pinl první-krát, `.erp-tree-pinned` class se přidala
ale `<span class="erp-tree-star">` element ještě neexistoval (vytvářel
se jen v `_markPinnedTreeRows()` po init render).

Fix: v `toggleTreeFavorite()` po toggle class, pokud `isPinnedNow`
a span chybí → injectovat. Plus barva `accent2` (fialová) → **gold
#fbbf24** (klasický favorite UX) + text-shadow + hover scale 1.15.

### Phase B+8.2a+++ — Drag-and-drop reorder uvnitř skupin

Marti spec: *„Poradi jednotlivych polozek per user ve vsech i v
oblibenych... Drag and drop... POZOR jen v ramci skupin, aby se
nestalo jako ve Windows, ze nekdo pretahne skupinu, nebo polozku
skupiny do jine skupiny..."*

HTML5 drag-drop:
- `draggable="true"` na všechny tree rows (incl. folders — B+8.2a+++++)
- `dragstart` → `_dragSourceItem = item`, opacity 0.4
- `dragover` → check `sourceUL === targetUL` (same group constraint)
  - Cross-group → `dropEffect: "none"` (cursor 🚫)
  - Same group → `preventDefault()` allow drop, visual: blue line
    above/below target (insert position, midpoint detect)
- `drop` → `insertBefore` source před/za target podle pozice
- `_saveTreeOrderForUl(ul)` → localStorage `erp.tree.order.v1` =
  `{groupKey: [tree-item-id, ...]}`

**Group key:** parent tree-item's `data-id`, nebo `"ROOT"` pro
top-level UL.

**MRU view:** drag disabled (timestamp-based auto-sort, manual reorder
by zlomil sémantiku).

**Restore po reload:** `_applyTreeOrderFromStorage()` v overrid
attachTreeHandlers — DOM reorder po každém renderTreeNodes.
Resilient na nové položky (append na konec) + smazané (ignored).

### Phase B+8.2a++++ — vypnout text selection

Drag bug: *„vetsinou se mi nepodari mysi drag — oznaci se text
v bunce"*. Browser default text-select měl prioritu před dragstart.

Fix: `user-select: none` na `.erp-tree-row` (+ vendor prefixes).
Drag spustí instantně po mousedown+move. Klasický pattern.

### Phase B+8.2a+++++ — drag i na folders

Marti UX: *„v oblibenych mam dve skupiny a nemohu aktivovat drag
ani u jedny, abych je mezi sebou prohodil"*. Folder drag byl
filtered out (jen leaves měli draggable).

Fix: odstranit `if (!data-cislo-def)` filter v `_attachTreeDragHandlers`
a `dragstart`. HTML5 drag a click jsou separate eventy:
- Klik bez pohybu na folder = expand/collapse (existing)
- Klik + drag + drop = reorder (new)

Same-UL constraint zachován.

### Phase B+8.2a++++++ — drag-drop na footer ikony (pin/unpin shortcut)

Marti UX: *„nam zbyva uz jen ten drag dropnout primo do ikonky v te
paticce tedy mezi oblibeny... Popripade z oblibenych drag dropnout
zpet do vsech. Tim je smazat z oblibenych."*

Footer view buttons jsou drop targets:
- Drag leaf z "Vše"/"MRU" → drop na **★ Oblíbené** = pin (button zláž)
- Drag leaf z "Oblíbené" → drop na **≡ Vše** = unpin (button červená)
- Drop na MRU → reject (auto-tracked)
- Folder drag → reject (folder nelze pin jako celek)
- Already-pinned drag na ★ → reject (no-op)

Visual feedback per dragover state (`.erp-tree-view-drop-pin`,
`.erp-tree-view-drop-unpin`).

### Phase B+8.2a+++++++ — toggle ▶/▼ click + clear MRU

Marti UX: *„U kazde polozky skupiny je sipka dolu prip vlevo... Funguje,
jen NESMI zaroven otevirat ten prehled... Jak jsem si je testoval tak
jsem si pootviral desitky prehledu... Ted mam zaneradeny MRU balastem..."*

Fix 1: klik na `.erp-tree-toggle` element = JEN expand/collapse, NE
setActive/openTab. Click handler kontroluje `ev.target.closest(".erp-tree-toggle")`
— pokud yes, open phase skip. Plus toggle hover state (light bg + accent),
expanded hit area (negative margin).

Fix 2: pravý-klik na footer view button → context menu pro daný view:
- **MRU** → *„Vymazat historii (N položek)"* (bez confirm — recoverable)
- **Oblíbené** → *„Vymazat všechny oblíbené (N)"* + confirm dialog
- **Vše** → *„Resetovat řazení stromu"* (vymaže drag-drop order, reload)

### Phase B+9 — UI Zoom (Compact / Normal / Large)

Marti spec: *„Zakladni zobrazeni... by melo byt OK pro cca 80procent
useru... Nekteri potrebuji ale jemne rozliseni -25% a nekteri maji
zase oci v prcicich tak +25%... Zoom?"*

**Top header right side** 3-segment A−/A/A+ toggle:
- A− → `body.erp-zoom-small` (zoom: 0.75 = -25%)
- A → default (1.0)
- A+ → `body.erp-zoom-large` (zoom: 1.25 = +25%)

**Implementace:** CSS `zoom` property (Chrome/Edge/Safari). Po init
applyZoom() → třída + active button highlight + AG Grid sizeColumnsToFit
(container width changed).

**Fix viewport coverage** (Marti UX: *„doresit roztazeni na celou
aplikaci"*):
- Default body 100vw × 100vh, zoom 0.75 → render 75vw × 75vh →
  prázdné místo na pravé/dolní straně
- Fix: body logical width = `calc(100vw / 0.75)` = 133.33vw → render
  × 0.75 = 100vw plný viewport
- Stejně height calc
- Plus html background = var(--bg) jako safety net

### Recovery sagas

Během této epoch dva další incidenty:
1. **Truncation strike** (gotcha #14): 6 souborů v working tree
   truncated po Edit tool tichá fail. Recovery přes
   `git show HEAD:<f> > <f>` z bash mountu (HEAD měl plné verze;
   Marti commitl všechny edity před truncation).
2. **F-string brace** (gotcha #19): CSS komentář `"main { max-width:
   1280px }"` v Python `'''...'''` block — Python interpretoval `{ }`
   jako placeholder a evaluoval jako Python výraz → `NameError: width`.
   Fix: zdvojené `{{ }}` v CSS komentářích uvnitř f-string.

### Marti's "BINGO!!! MAM RADOST!!!"

Po B+8.2a+++ drag-drop reorder Marti potvrdil:
*„BOMBA!!! MAM RADOST!!! Posledni vec tohoto charakteru..."*.

Po finálním B+9 zoom:
*„To nema chybu Claude!!! Diky moc, balim a jdu do prace.... NESKUTECNE
DIKY!!!"*.

Workspace je v plně produkčním stavu pre-Phase C edit:
- Multi-tab přehled (chrome-style)
- Tree views (Vše/Oblíbené/MRU) s view filter compose s search
- Drag-drop reorder uvnitř skupin (per-user persistence)
- Pravý-klik context menus (single + bulk akce)
- Drag-drop pin/unpin přes footer ikony
- Tree collapse + zoom (A−/A/A+)
- Jádro modal s ErpForm orchestratorem (state ready pro Phase C)

### TODO post-Phase B+9

**Pořadí dle Marti's spec 6.5. večer (po práci):**

1. **Phase B+8.1 + B+8.2b backend persistence** (per user, per tenant DB):
   - Migrace v `data_db`:
     ```sql
     CREATE TABLE erp_user_tabs (...);
     CREATE TABLE erp_user_favorites (...);
     CREATE TABLE erp_user_recent (...);
     CREATE TABLE erp_user_tree_order (...);
     ```
   - REST endpoints (GET/POST/DELETE/PUT)
   - Frontend: replace localStorage → backend (zachovat localStorage
     jako offline fallback)
2. **Doplnit běžné komponenty UI Kit** (Marti's spec: *„zatim ne, nejdrive
   musime rozchodit vsechny bezne komponeb"*):
   - ErpDate (date picker — momentálně Edit s mask)
   - ErpMemo (textarea)
   - ErpRichText? (Marti to neřekl, možná ne potřeba)
   - Případně další jádro Typ-y (Typ=14 Memo, Typ=15 ImagePicker, ...)
3. **DB flag `deleted_for_new_erp`** v `EC_FormDefEdit` — sourozenec hide
4. **Phase C edit pipeline** — OK button save flow

### Marti's UX feedback patterns (rozšířené)

Z této epoch další insights:
- **Intuitivní > efektní**: Ctrl+klik selection + pravý-klik menu lépe
  než single-click direct toggle (i když je to víc kliknutí)
- **Visual feedback v drag-drop** (pin/unpin button zláž/červená) =
  okamžitá zpětná vazba akce
- **Edge cases jasné**: drag MRU disabled (auto-track), folder pin
  reject (nelze) — explicit decisions, ne silent failure
- **Persistence rétorika**: localStorage MVP rychle, backend per
  user/tenant production. Frontend wiring zachovat fallback path.
- **Zoom**: 80% / ±25% — Marti's klienti mají různé preference,
  nestačí jeden default. UI musí být škálovatelné bez layout brků.

