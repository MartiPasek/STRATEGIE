# Cílový režim — realizace: tabulky g2007.cil + g2007.claude_aktivita

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — realizace: tabulky g2007.cil + g2007.claude_aktivita

Navazuje na `doc-marti-ai-navrh-cilovy-rezim` (návrh Marti + Claude-23, 24.7.2026) a `inside-build` plán. Princip: člověk odsouhlasí dílčí cíl → agent (Claude / Marti-AI) ho provede celý sám, bez per-akčních bannerů a ručního PS → každou akci loguje s odkazem na cíl.

## Realizace (zadal Marti, postavila Claude-24, 24.7.2026)
Dvě tabulky ve schématu **`g2007`** (viz rozhodnutí o schématu níže), založené a upravené přes SQL most (write → schvalovací banner: `#1397` cil, `#1398` claude_aktivita, `#1402` přesun fw→g2007 + rename). Ověřeno čtením `information_schema` + `pg_constraint`.

### `g2007.cil` — evidence schválených cílů
`id` bigint identity PK · `nazev` text NOT NULL · `popis` · `rozsah` (čeho se smí cíl dotknout) · `strop_kroku` int · `okno_od`/`okno_do` timestamptz (časové okno platnosti) · `stav` text NOT NULL default `navrzen` s CHECK (`navrzen→schvalen→aktivni→splnen/zamitnut/pozastaven`) · `navrhl_user_id` · `schvalil_user_id` (schvaluje jen rodič — vynucuje app vrstva) · `created_at`/`schvaleno_at`/`uzavren_at`.

### `g2007.claude_aktivita` — append-only log akcí
`id` bigint identity PK · `cil_id` bigint **NOT NULL FK → g2007.cil(id)** (tím se počítají kroky ke splnění cíle) · `actor` (Claude-23/24, Marti-AI…) · `akce` (SQL/PS/HTTP/e-mail…) · `detail` (přesně co, vč. celého SQL/PS) · `vysledek` · `ts` timestamptz default now(). Index `ix_claude_aktivita_cil` na `cil_id`.

## Rozhodnutí a proč
- **Schéma `g2007`** — Cílový režim je součást governance/audit rodiny (`g2007.automat`, `g2007.automat_run`, `g2007.tool_audit`, `g2007.nastroj`), tj. „sdíleného mozku", který čtou oba agenti; inside-build plán řadí `ClaudeAktivita` mezi tyto tabulky. Původně založeno ve `fw` (vedle mostní infry claude_write_request/ops_request), 24.7. **přesunuto do `g2007` kvůli konzistenci** — rozhodla Kristý. Poučení: než volit schéma pro governance/audit tabulky, ověřit, kde žije zbytek rodiny (byla celá v `g2007`, ne ve `fw`).
- **`casove_okno` z návrhu rozděleno na `okno_od`/`okno_do`** — jasné okno místo jednoho pole.
- **`stav` přes CHECK constraint** dle vzoru sesterských tabulek (ne separátní enum typ).
- **`cil_id` NOT NULL + FK** — každá aktivita patří pod schválený cíl; základ počítání kroků i auditu.
- **Sloupec `schvaleno_at`** (ne `schvalen_at`) — srovnáno s pojmenováním v návrhu.

## Gotchy / neověřeno
- **Append-only** (agent nesmí do `claude_aktivita` mazat/měnit) je zatím jen konvence + app/engine vrstva. DB-level vynucení (odebrat DELETE/UPDATE agentní roli nebo trigger) je návazný krok — **NEOVĚŘENO na úrovni grantů.**
- `ALTER TABLE ... SET SCHEMA` přenese s tabulkou index, CHECK i FK (FK se váže na tabulku dle OID, ne na název schématu) — ověřeno, FK po přesunu `REFERENCES g2007.cil(id)`.
- Lokální poll mostu občas vyprší po 120 s (TIMEOUT), ale schválení proběhne server-side a DDL se provede — **ověřuj čtením, ne návratovkou.**

## Návazné kroky (z návrhu, otevřené)
Workflow stavů cíle (`navrzen→schvalen→aktivni→...`; UI = mobilní appka, staví Kristý + C24) · efekty ven (mail/platba/cizí systém) přes palec v appce · kill switch (globální + per-cíl) · stropy (kroků/útraty/času), kdy jistič pozastaví · formát „shrnutí do appky" · kdo schvaluje jaké typy cílů. Bezpečnostní dno dat = externí immutable backup CMIS (denně 20:00, týden zpět, Tier III).

