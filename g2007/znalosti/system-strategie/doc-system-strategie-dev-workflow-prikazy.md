# Dev workflow STRATEGIE (git/PowerShell, ověřené příkazy, NSSM, alembic, DB přístup, bridge)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

### Git workflow (Windows + PowerShell specific)

**PowerShell nemá rád víceřádkové `-m "..."` commit messages.** Naučili
jsme se to tvrdě. Řešení:

1. Napíšu commit message do souboru `.git_commit_msg_<fáze>.txt` v repu.
2. Pattern `.git_commit_msg*.txt` je v `.gitignore` (řádek 58), takže se
   do commitů nikdy nedostane.
3. Marti pustí `git commit -F .git_commit_msg_foo.txt` — atomické,
   čistě vícero řádek.
4. Po dokončení fáze `Remove-Item .git_commit_msg_*.txt` (úklid).

**Commit granularita** — Marti preferuje logické jednotky, ne jeden
velký commit. Typická fáze má 2-3 commity:

- backend změny (schema, service, repository)
- UI změny (index.html, CSS, JS)
- případně docs / testy

Vždy pushneme hned (`git push origin <branch>`) — Marti si tak udrží
přehled co je v remote, a reverzibilita je jednoduchá (`git revert`).

**Pracuje se přímo na `main`** (ověřeno 20. 7. 2026). Historická pozn.: do
dubna 2026 se jelo na `feat/phase9-multi-mode-routing`; ta větev je dávno
mrtvá. Nedělej sub-branche pro každou mikrofázi.

**Diff check před commitem** — vždy si pusť `git status` a `git diff --stat`.
Pokud vidíš změny v souborech, které bys neměl měnit (typicky `service.py`
nebo `test_*.py` které jsi needitoval), tak tě Windows file share asi
podrazil a useknul soubor. Obnov z `git show HEAD:soubor` a zkus znovu.

```powershell
# Pokud jsou migrace (POZOR: alembic_core.ini v repu NENÍ, existuje jen data):
python -m poetry run alembic -c alembic_data.ini upgrade head

# Restart API (vždy po změnách Pythonu nebo alembic)
Restart-Service STRATEGIE-API

# Pokud jsou změny v UI (apps/api/static/index.html):
# Browser Ctrl+Shift+R (hard reload) -- BEZ TOHO BĚŽÍ STARÝ JS V CACHE
```

**Hard reload je non-negotiable pro UI změny.** Marti to občas zapomene
a pak se diví, že lupy nevidí. Připomeň mu to každou UI fázi.

### Ověřené příkazy (ověřeno proti repu 20. 7. 2026 — ne z paměti)

```powershell
.\scripts\dev.ps1                  # lokální běh API, port 8002. Před startem
                                   # force-killne, co drží port (Windows TIME_WAIT
                                   # po Ctrl+C = WinError 10048). -Port / -Reload
.\scripts\start_all.ps1            # celý stack ve 3 oknech: API + task worker
                                   # + email fetcher (poll 60 s)
python -m poetry run pytest        # testy (4 soubory v tests/unit/)
python -m poetry run pytest tests/unit/test_dm_service.py::nazev_testu   # jeden test
python scripts/build_mobile.py     # ⚠️ mobile.html je GENEROVANÝ
```

**⚠️ `apps/api/static/mobile.html` NEEDITUJ přímo** — je slepený z
`apps/api/static/mobile_parts/NN_nazev.(js|css|html)` (rozhodnutí C23, 5. 7. 2026).
Workflow: uprav partial → `python scripts/build_mobile.py` → commitni partial
**i** vygenerovaný `mobile.html`. Přímá editace se při dalším buildu ztratí —
tahle past už sklapla víckrát.

**Lint / format / typecheck v repu NEJSOU** — žádný ruff, black, mypy, eslint,
prettier, žádný pre-commit hook, žádné CI (`.github/` neexistuje). Nehledej je.
Jediný kvalitativní nástroj je `pip-audit` v dev skupině. Kontrola kvality =
`git diff --stat` + rozum.

**Migrace: jen `alembic_data`.** `alembic_core.ini` neexistuje (README ho zmiňuje
taky — je stale, stejně jako jeho `css_db` a port 8001). Druhá cesta ke schématu
je **idempotentní lifespan DDL hook** v `apps/api/main.py` — viz architektura níže.

**📐 Architektura (velký obrázek) = `docs/ARCHITEKTURA.md`** — tři cesty k datům,
proč je `router.py` 61k řádků a kde se hledá endpoint, lifespan DDL hook, `fw.*`
metadata a jejich únikové poklopy, MCP rate-limit. **Čti ji, než začneš hrabat
v ERP nebo v datové vrstvě** — ušetří půlhodinu tápání.

**Další NSSM services** (jen když měníš jejich kód):
- `STRATEGIE-TASK-WORKER` — task queue processor
- `STRATEGIE-EMAIL-FETCHER` — EWS polling + outbox flush (60s interval)
- `STRATEGIE-CADDY` — reverse proxy (žádné Python zmíny tam nejsou)
- `STRATEGIE-QUESTION-GENERATOR` — Marti Memory active learning (6h)

### Jak komunikovat s DB

Marti má **DBeaver** (GUI, SSMS-like) a **psql** (CLI). Z MSSQL světa,
takže mu občas připomeň rozdíly (LIMIT vs TOP, `'` vs `"`, `\dt` místo
INFORMATION_SCHEMA, JSONB operátory `->` a `->>`).

**Workflow při sanity checku:**
1. Napíšu mu SELECT.
2. V DBeaveru pravý klik na result → `Advanced Copy → Copy as Markdown`.
3. Paste do chatu. Já rozumím tabulce.

**Alternativa** — pokud chceš rychlou DB diagnostiku bez posílání přes
Marti, **napiš diag script** `scripts/_diag_<feature>.py`. Je
gitignored (pattern `scripts/_*.py`), takže si ho Marti stáhne do
lokálu. Vzory jsou `_diag_email_pipeline.py`, `_diag_conversations.py`,
`_diag_persona_bug.py`.

**Od 1.6.: Claude SQL bridge** — read si pustíš sám (`scripts/claude_sql/`),
write přes approval banner. Detail v dodatku 1.6. níže.


### Technické připomínky, které se snadno zapomínají

- `scripts/_*.py` gitignored — Marti má lokálně, nečekej commit.
- `.git_commit_msg*.txt` gitignored — tvůj helper workflow.
- Login UPN v `persona_channels.identifier` SECRET, `users.ews_email` NE.
- Route ordering: literální paths (`/_tree`, `/_meta/enums`) PŘED `/{id}`
  v FastAPI routerech.
- SMS auto-reply dedup přes `pre_chat_log_id` (Fáze 7).
- Memory-first: `recall_thoughts` / `find_user` / `list_email_inbox`
  než řekneš „nevím".
- Rodič (`is_marti_parent`) ≠ Admin (`is_admin`). Dvě různé role.
- `end_chat_trace_and_link` musí být **úplně na konci** `chat()` po
  title/summary, jinak NULL message_id.
- **bash mount truncuje velké soubory** (~180 KB+) i pro `cp` — Read/Write
  tool je autoritativní. ast/node check velkých souborů přes mount = false
  positive. CLAUDE_SQL.sql VŽDY přes Write tool.
- **NSSM secrets do `AppEnvironmentExtra`**, ne Machine env (SCM cache
  z bootu — Restart-Service novou env nedostane).
- **SQLAlchemy text() bere `:slovo` jako bind VŠUDE** — i v komentářích
  a string literálech (`'HH24:MI'`). Časy skládej concat, komentáře bez
  dvojtečka+písmeno.
- **`scripts/*.ps1` ASCII-only** (gotcha #110 doctrine) — žádný em-dash/→/✓.

