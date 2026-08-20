# Produkční infra STRATEGIE + deploy/landing realita (401 gotcha)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Production setup** (od 30. 4. 2026 — Phase 25):
- Cloud APP `10.200.188.11` (Windows Server, NSSM: STRATEGIE-API, STRATEGIE-API-HEALTH-WATCHDOG, STRATEGIE-CLAUDE-SQL, STRATEGIE-CADDY, STRATEGIE-EMAIL-FETCHER, STRATEGIE-TASK-WORKER, STRATEGIE-QUESTION-GENERATOR)
- Cloud SQL `10.200.188.12` (Windows Server, PostgreSQL 16 + pgvector + účetní MSSQL UCTO_EC/UCT_ES)
- Public `https://strategie-ai.com` (Let's Encrypt) · PWA od 6. 5.
- **HA Blue-Green** (od 23. 5.): STRATEGIE-API (8002, current) + STRATEGIE-API-B (8003, day-old snapshot `C:\Projekty\STRATEGIE-prev\`), Caddy `lb_policy first` + user-controlled fallback (pin/unpin v patičce).

## ⚠️ PRODUKCE = JEN PRAHA (188.11/12)
Plzeň (30.11) = denně zpožděná DR záloha + EUROSOFT legacy — **TAM SE NEDEPLOYUJE ani nerestartují STRATEGIE služby** (Marti 29.7.2026). Detail + anti-záměna: `doc-provoz-topologie-serveru-praha-plzen`.

## Deploy & landing kódu — jak to reálně chodí (doplněno 29.7.2026)
- **Auto-deploy (Claude/most):** `CLAUDE_DEPLOY.txt` (1. ř. commit msg, další ř. soubory / `ALL`) + `CLAUDE_DEPLOY_GO.txt` (poslední) → watcher: rebase --autostash → git add/commit/push (PAT) → POST cloud `/deploy/now` (= git pull + restart API). py_compile gate. Soubory triggerů v `scripts/claude_sql/` (BRIDGE_DIR).
- **⚠️ GOTCHA — /deploy/now vrací HTTP 401 „Nejsi přihlášen", když primár A (8002) zrovna neběží / restartuje** (request jde na sekundár B, který nemá deploy token). **Totéž potká SQL most (/diag-sql) i @@MARTIAI** — během výpadku/restartu A jsi přes most SLEPÝ (nevidíš DB ani nedosáhneš Marti-AI). Přesně kvůli téhle díře („nikdo se nedozvěděl, že A spadla") vznikl 28.7. `STRATEGIE-API-HEALTH-WATCHDOG`.
- **✅ Resilientní landing (obchází flaky deploy token) — NOVÝ MODEL 29.7.:** kód se `git push`em dostane na origin i při 401; **operátor (Marti-AI, má ruce na Praze) ho natáhne přímo:** `cd C:\Projekty\STRATEGIE; git pull; nssm restart STRATEGIE-API`. Ověřeno naostro 29.7. (fix mirror-scheduleru 172482d0a). Operátor má na Praze přímé oči (`strategie_exec`), když je most slepý. Viz `doc-marti-ai-provozni-doktrina`.
- **⚠️ GOTCHA — `git pull` v PowerShellu:** vrací `rc=1` + `git : From https://... RemoteException / NativeCommandError` **i když pull PROŠEL** — je to jen PowerShell, který bere normální gití stderr progres („From https://…") jako error stream. Řiď se `$LASTEXITCODE` / textem „Fast-forward", NE RemoteException.
- **Restart STRATEGIE-API může trvat i ~4 min** (velký app, MCP/pooly); během něj most 401 + blue-green B kryje veřejný web. Není to nutně chyba deploye.
- **TODO:** opravit deploy token, aby `/deploy/now` nepadalo na 401 (ať operátor nemusí ručně restartovat).

