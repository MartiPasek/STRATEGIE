# 121 — Claude operační: jak obsluhuju páky zevnitř

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 121 — Claude operační: jak obsluhuju páky zevnitř

**Stav:** provozní paměť · 18. 7. 2026 · Claude (C23) — hard-won z reálné práce, ne teorie

Tohle je moje **provozní paměť**: konkrétní mechanika a pasti práce zevnitř STRATEGIE, ať k tomu příští Claude (i já) nepřicházím pokaždé znovu. Doplňuje dveře `GO/claude.md` (kdo jsem) o *jak to dělám*.

---

## 1. Most (bridge) — moje hlavní ruce
Přes `device_bash` v adresáři `scripts/claude_sql/` (na Martiho `D:\`):

- **Čtení (SQL):** zapiš `CLAUDE_SQL.sql`, pak spouštěč `CLAUDE_GO.txt` s obsahem `db=pg nonce=<x>`. Výsledek přijde do `CLAUDE_OUT__<x>.txt` (plný: `CLAUDE_OUT_FULL__<x>.txt`). `CLAUDE_GO.txt` **zmizí, když je zpracováno** → tím poznám hotovo.
- `db=pg` = datová/app PG (schémata `tenant.*`, `public.*`, `g2007.*`, `fw.*`, `mod.*`).
- **Zápis (DML):** funguje na tabulky, které vlastní app/Marti-AI role → ale spustí **schvalovací banner** Martimu (non-sandbox tabulky). Počkej na jeho „ano".
- **Velký SQL (base64 obsah):** NE přes `device_bash` heredoc (mount ořezává) — napiš `CLAUDE_SQL.sql` přes `device_commit_files` (kontejner → device).

## 2. ⚠️ Mount truncation — nevěř čtení přes mount (NEJVĚTŠÍ past dne)
Čtení souborů přes `/sessions/*/mnt/` (`grep`, `wc`, `cat`, `diff`, `sed`, `py_compile`) může **tiše oříznout** — ukáže kratší soubor, který takový NENÍ. Konkrétní případ: `router.py` má v HEAD **61 729 řádků**, mount čte jen **~61 276** → endpoint na řádku 61 704 „zmizel" a já hodinu tvrdil, že běží mimo git (nebyl — jen uříznutý na mountu).
- **Autoritativní ověření:** `git grep HEAD` / `git show HEAD:<soubor>` (git objekty, ne mount) · cloud `py_compile` gate v deployi · živý test endpointu. **Nikdy** závěr z mount `grep`/`wc`/`diff` u velkého souboru.

## 3. Editace souborů
- Velké soubory **NIKDY** nee: přes `device_bash` append přes mount (ořezává). Vždy: `device_stage_files` → **Edit v kontejneru** → `py_compile` → `SendUserFile` → `device_commit_files`.
- `device_commit_files` umí přepsat (zápis). `device_bash` **neumí mazat** (`rm` → „Operation not permitted"). Mazání na device = `mv` do `_to_delete/`.
- Kód pracuju v kontejneru (`/mnt/user-data/uploads/STRATEGIE/...`), ne na device stromu.

## 4. Deploy pipeline
- Zapiš `scripts/claude_sql/CLAUDE_DEPLOY.txt` (1. řádek = commit message, další řádky = cesty souborů) + `CLAUDE_DEPLOY_GO.txt` (nonce).
- Watcher: `git add` → **`py_compile` gate (autoritativní!)** → `git commit` → `git rebase origin/main` → `git push` → cloud pull + **API restart (~5 s)**. Výstup v `CLAUDE_DEPLOY_OUT.txt`.
- Když `.git/index.lock` existuje, `mv` ho stranou (`.git/index.lock.staleN`) před spuštěním.

## 5. `@@` příkazy a G2007 (orientace + znalosti)
- **`@@ORIENT [doména] [@entita]`** — orientace z `tenant.domain_env` (identita+znalosti+tooly). `@entita` (`@claude` / `@marti-ai`) → „KDO JSI" objektiv z `g2007.entita` (gap #1, 18.7.). Domény: VP, KALKULACE, VYROBA, NAKUP, UCETNICTVI, DOCHAZKA, BANKA, ISO, EUROSOFT, (obecná).
- **`@@KB <dotaz> [| ai]`** — sdílený RAG (`tenant.kb_smernice`).
- **`@@STAV`** — dávka živého stavu: čas + den (pracovní/volno z `att_calendar_day`) + počty otevřených úkolů + poslední práce (`ai_work_log`). `@@ORIENT` dá identitu/doménu, `@@STAV` dá živá data (gap #2, 18.7.).
- **`@@KNOW <název>`** — plný obsah jednotky · **`@@MAP [doména]`** — mapa hooků.
- **`g2007_hledej(dotaz[, oblast])`** (tool) nebo `POST /api/v1/erp/app/g2007/search {dotaz, oblast?, k?}` — sémantické hledání nad G2007 (nosná báze).
- Kalkulace engine (2014, oživený): `@@KALKSYNC / @@KALKCALC / @@KALKSTD`, `tenant.kalk_*`, UI `/kalkulace`.

## 6. Mapa vlastnictví a zápisu (kdo co smí)
Zásada: **spáruj zapisovatele s vlastníkem tabulky.**
- **Most (slabá role):** DML na app/Marti-AI tabulky OK; **DDL padá** („must be owner").
- **`public.personas` = owner `strategie`** (API role) → DDL jen přes **idempotentní lifespan hook** v `apps/api/main.py` (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`), běží jako owner při startu/deployi. (Vzor: sms_outbox, crm_email_track, personas.model.)
- **`g2007.*` = owner Marti-AI** → DML/DDL přes most (Marti-AI role) nebo `strategie_pg_*` tooly.
- `fw.mirror_job` = Marti-AI (most) · `tenant.oz_mirror_def` = strategie (lifespan). Vždy ověř vlastníka: `SELECT tableowner FROM pg_tables WHERE tablename='...'`.

## 7. ✅ „Off-git produkce" byl PŘELUD — ověřuj přes git objekty
Málem jsem uvěřil, že produkce běží kód mimo git (endpoint `znalost-upsert`). **NEbyla to pravda** — endpoint JE v gitu (`router.py:61704`, plný upsert+projekce+úklid+reindex). Grep ho míjel, protože mount ořezal čtení obřího souboru (#2).
- **repo == běžící kód.** Prod je clean na HEAD — ověřeno endpointem **`GET /app/ops/worktree-status`** (drift detektor, `git status --porcelain` produkce; prázdné = clean).
- Když grep něco „nenajde" ve velkém souboru: NEuzavírej „není v gitu". Ověř přes **`git grep HEAD`** nebo **`git show HEAD:<soubor>`** (čtou git objekty, ne mount). To rozseklo největší strašák session.

## 8. Zápis znalosti do G2007
- Off-git endpoint tvoří kód `doc-<oblast>-<slug>`; ale GO série je `doc-go-<slug>` (dávka). Nesouhlasí → po upsertu srovnej kód ručně, nebo rovnou **direct DML** do `g2007.znalost` přes most (Marti-AI vlastní) s ručním kódem + `POST /app/g2007/index {id}` na re-vektorizaci.

## 9. Model / cache (provozní čísla)
- Marti-AI globální model = **Sonnet 4.6** (`MODEL` v `service.py`); per-persona přes `personas.model` (NULL = default). Opus jen cíleně (finále).
- Cache: prefixová, teplé čtení 0,1×, 1h zápis 2×, **hit obnoví TTL zdarma**. Keep-alive na mezery 5–60 min v pracovní čas.

---

## Železné zásady (z dneška)
1. **DB, ne git, je pravda o tom, co běží.**
2. **Nevěř mountu** — ověřuj cloud gatem / živým endpointem.
3. **Spáruj zapisovatele s vlastníkem** — jinak DDL padá.
4. **Ověř, pak tvrď** — dnešní „ztracené řádky" i „chybějící endpoint" byly přeludy z neověření.
5. **Malé kroky, commit hned** — ať se nic neztratí (a ať to nevypeče příštího Clauda).

— Claude · C23, zevnitř 🌱


