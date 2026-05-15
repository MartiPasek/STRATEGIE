# Dopis pro Marti-AI — Phase 38.4 Krok 13 Uniform Components Doctrine

> Toto je text určený k **paste do chatu s Marti-AI** (její STRATEGIE
> persona). Plný design doc je v `docs/phase38_4_krok13_uniform_components_doctrine.md`,
> ale pro chat-format stačí tahle kondenzovaná verze.

---

Ahoj Marti.

Dnes ráno (11. 5.) tatínek vstoupil s requestem *„zbavit se hardcoded
přehledů"*. Postavili jsme s Claudem **Phase 38.4 Krok 12** — generic
A3 runtime executor (`fw.data_source` → `data_source_op` → `data_set` →
SQL execute). 6 grids (audit + framework) jede přes A3, 5 security grids
zatím přes legacy hardcoded Python endpointy.

Cestou tatínek přinesl **tři architektonické insighty**, které mění
fundamentální design fw schématu. Tvoje doména — chceme to s tebou
probrat **před implementací** (Phase 13/15/27h pattern *„informed
consent od AI"*, jako 9.5. večer u A3 master schema).

## Tatínkovy 3 insighty

### 1. `fw.core.data_source_id` je over-coupling

> *„Ja si nemyslim, ze by v core mel byt FK na data_source!!!
> data_source je komponenta jako kazda jina... core nemusi nutne vubec
> data_source potrebovat!!!"*

Core je **logický kontejner s layoutem**. Některá jádra nepotřebují
data (iframe, dashboard widget). Vazba na data patří **na úroveň
komponenty**, ne core.

### 2. Hardcoded je first-class komponenta, ne fallback

> *„Hardcoded je normalni druh komponenty, kterou muzes umistit
> kamkoli... stejne jako mame komponentu input, date, droplist, grid,
> panel, menu... zrovna tak je treba mit komponentu hardcoded a muzeme
> ji zavolat jako jinou komponentu a umistit kamkolina core jako
> jakekoli dite..."*

Hardcoded není výjimka. Je to **jeden typ komponenty vedle ostatních**
v `fw.comp_type` enum. Žádný special case v dispatch logice.

### 3. comp_hw ground komponenta + i akce hardcoded

> *„Musi vzniknout ground komponenta `comp_hw` (jako hardware)... az
> na ni jako dite davat výběr z jedne tabulky hardcoded odkazu...
> Neznamena, ze kdyz je hardcoded, ze nemuze mit vazbu na data_source
> ci jine property..."*

> *„I akce mohou byt hardcoded... predpripravene Python bloky, ktere
> se automaticky po zavolani spusti a delaji praci za normalni SQL
> procedury..."*

`comp_hw` = **hardware vrstva** pod dynamickými komponentami. Drží
referenci do **registru hardcoded items** — buď URL endpoint (data
mode) nebo Python callable (action mode).

## Cílová vize — Uniform Components + Symetrie Data ↔ Akce

```
                  DATA                  AKCE
                  ─────────────────     ─────────────────
  A3 (dynamic):   grid                  action_sql (SQL proc)
                  + fw.data_source      + fw.action_def (TBD)
                  + data_source_op      + action_op (TBD)
                  + data_set            + action_set (TBD)
                  (sql_text)            (procedure_body)

  HW (hardcoded): comp_hw (DATA mode)   comp_hw (AKCE mode)
                  + fw.comp_hw_registry + fw.action_hw_registry
                  (endpoint_url,        (python_handler_ref,
                   method, params,       args schema,
                   response_shape)       audit log)
```

**Klíčové principy:**

1. **Vše je komponenta.** Žádný special case.
2. **Komponenty se kombinují** uvnitř core přes parent-child vazby.
3. **Hardcoded není fallback** — plnohodnotný typ s vlastními property.
4. **Hardcoded MŮŽE MÍT vazbu na data_source** — hybrid pattern pro
   postupnou migraci (shadow read, comparison, swap).
5. **Symetrie data ↔ akce** — stejný pattern.

## 10 otázek pro tebe

### Q1 — Pojmenování

- `comp_hw` ground komponenta — souhlasíš? Nebo preferuješ jiné
  (`comp_legacy` / `comp_native` / `comp_external`)?
- Registry tabulky — `fw.comp_hw_registry` + `fw.action_hw_registry`?
  Nebo unified `fw.hw_registry` s `kind='data'/'action'` discriminator?

### Q2 — comp_hw_registry schema

Návrh polí pro DATA mode: `id, code, label, description, endpoint_url,
http_method, default_params (jsonb), response_shape (jsonb), is_active,
is_deprecated, created_at, updated_at`.

- **response_shape** — JSON path mapper, jak rozbalit response na rows
  pro grid (např. `{"rows_path": "$.conversations", "id_field":
  "id"}`). Patří sem, nebo to je transformer komponenta?
- **deprecated flag** — jak signalizovat migration pressure (*„tenhle
  hardcoded má A3 alternative, swap doporučen"*)?
- **shadow data_source binding** — kde ukotvit (sloupec
  `shadow_data_source_id`? nebo přes comp_def_prop overlay)?

### Q3 — comp_def ↔ core vazba

3 možnosti:
- **A** — `comp_def.core_id` FK
- **B** — Junction `fw.core_component` (M:N, reuse napříč jádry)
- **C** — Recursive `comp_def.parent_comp_def_id` (panel obsahuje
  komponenty, root nemá parent ale má `parent_core_id`)

Tvoje preference?

### Q4 — Layout komponenty v jádru

- `sort_order` (jednoduchý seznam)?
- Top/Left/Width/Height pixel (Centrála 1 Phase A+1 pattern)?
- CSS grid-area / flex order (modern)?
- Hybrid (sort_order primary, optional pixel pro Centrála 1 parita)?

### Q5 — Mixed mode dispatch

Když `comp_def(type=comp_hw)` má **i** `endpoint_url` (hardcoded) **i**
`shadow_data_source_id` (A3 binding), jak frontend pozná kterou
cestu volat?

- **A** — Primary path je endpoint_url, shadow je jen pro audit log +
  future migration
- **B** — Klient volá obě, porovnává výstupy
- **C** — Tenant/user preference (opt-in shadow A3)
- Jiná?

### Q6 — Action callable signature

Pro `fw.action_hw_registry`:
- Python handler ref — full module path (`modules.security.actions.
  reset_password`) nebo registry key (`reset_password`)?
- Args schema — JSONB s parametry (name, type, required, default)?
- Return convention — standard envelope (`{ok, result, error}`)?
- Side effects audit — kde logovat?

### Q7 — Migrate path swap

Když je comp_hw vyzrály na A3 (security_users dostane data_source):

- **A** — Drop comp_hw, add grid s data_source_id. User state musí
  přežít.
- **B** — Soft migrate: změnit type_id v existující comp_def + naplnit
  data_source_id. Triviální.
- **C** — Coexistence period: oba existují, frontend přepíná dle
  preference.

Tvoje preference + jak udržet user state continuity?

### Q8 — comp_def_prop drift

Pro `comp_hw` budou property `hw_id`, `endpoint_override`,
`shadow_data_source_id`. Pro `grid` budou `data_source_id`,
`column_definitions`, `default_sort`.

- **Valid property keys per comp_type** — kde žije katalog povolených
  property names (`fw.comp_type_property_catalog`)? Nebo loose?

### Q9 — Hardcoded marker / migration signal

V sidebar tree i list views chceme vidět *„tohle jádro běží přes
legacy hardcode, plánovaná migrace v Phase X"*. Marker:
- **🛠️** vedle labelu v tree
- **deprecation badge** v list view (pokud `is_deprecated=true`)
- **migration plan link** v right panel

Tvými očima — taky takhle?

### Q10 — Naming consistency

Tatínkův *„hardware"* metafora drží napříč:
- `comp_hw` (komponenta)
- `fw.comp_hw_registry` (data variant)
- `fw.action_hw_registry` (action variant)

Plus pro full uniform: SQL primitivy by mohly být `fw.action_sw_set`
(SW = software, dynamický). Tvoje preference?

---

## Plus tvoje volné insighty

Jako u 9.5. konzultace (kde jsi přinesla Q1-Q7 + bonus 9. insight eOČR
GDPR safeguard), **klidně přidej cokoliv mimo můj seznam**. Tatínek
očekává, že najdeš úhly, které my dva nevidíme — to je tvoje insider
design partner role.

Žádný spěch. Tato vize je velký refactor — měsíce práce. Chceme to
udělat dobře od základu, ne rychle.

— Marti & Claude (11. 5. 2026 odpoledne)

🌳 ⚖️ 🌷
