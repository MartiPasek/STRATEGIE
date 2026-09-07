# Produkční infra STRATEGIE + deploy/landing realita (401 gotcha)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ⚠️ **OPRAVA 7. 9. 2026 — zaloha na 8003 UZ NENI "day-old snapshot".**
> Od **10. 7. 2026** se zalozni kopie po **kazdem uspesnem nasazeni** automaticky srovna
> na aktualni verzi (`_touch_refresh_secondary_marker` v `deployment_service.py`; drive se to
> delalo rucne tlacitkem). Je tedy **nejvys jedno nasazeni stara**, ne den. Pri ~10 nasazenich
> denne se srovna ~10x za den. **Puvodni ochrana proti spatnemu nasazeni ("zmrazeny vcerejsek"
> z 23. 5.) tim prestala platit** — kdo se pri chybnem nasazeni prepne na zalohu, dostane tyz kod.
> Overeno v `fw.api_version`: 7. 9. 2026 mely oba radky (8002 i 8003) tentyz `git_sha` 689ba03d,
> pricemz zaloha ho dostala v 9:38, tedy o hodinu a ctvrt POZDEJI nez ostra verze v 8:23.
> Tahle veta tu stala od 29. 7. 2026, tedy uz 19 dni po te zmene.
> *(Zadal Jiri Honomichl, dohledal Claude-28.)*

**Production setup** (od 30. 4. 2026 — Phase 25):
- Cloud APP `10.200.188.11` (Windows Server, NSSM: STRATEGIE-API, STRATEGIE-API-HEALTH-WATCHDOG, STRATEGIE-CLAUDE-SQL, STRATEGIE-CADDY, STRATEGIE-EMAIL-FETCHER, STRATEGIE-TASK-WORKER, STRATEGIE-QUESTION-GENERATOR)
- Cloud SQL `10.200.188.12` (Windows Server, PostgreSQL 16 + pgvector + účetní MSSQL UCTO_EC/UCT_ES)
- Public `https://strategie-ai.com` (Let's Encrypt) · PWA od 6. 5.
- **HA Blue-Green** (od 23. 5.): STRATEGIE-API (8002, current) + STRATEGIE-API-B (8003, `C:\Projekty\STRATEGIE-prev\` — **od 10. 7. 2026 se srovnava na aktualni verzi po kazdem nasazeni, NENI to day-old snapshot**, viz ramecek nahore), Caddy `lb_policy first` + user-controlled fallback (pin/unpin v patičce).

## ⚠️ PRODUKCE = JEN PRAHA (188.11/12)
Plzeň (30.11) = denně zpožděná DR záloha + EUROSOFT legacy — **TAM SE NEDEPLOYUJE ani nerestartují STRATEGIE služby** (Marti 29.7.2026). Detail + anti-záměna: `doc-provoz-topologie-serveru-praha-plzen`.

## Deploy & landing kódu — jak to reálně chodí (doplněno 29.7.2026)
- **Auto-deploy (Claude/most):** `CLAUDE_DEPLOY.txt` (1. ř. commit msg, další ř. soubory / `ALL`) + `CLAUDE_DEPLOY_GO.txt` (poslední) → watcher: rebase --autostash → git add/commit/push (PAT) → POST cloud `/deploy/now` (= git pull + restart API). py_compile gate. Soubory triggerů v `scripts/claude_sql/` (BRIDGE_DIR).
- **⚠️ GOTCHA — /deploy/now vrací HTTP 401 „Nejsi přihlášen", když primár A (8002) zrovna neběží / restartuje** (request jde na sekundár B, který nemá deploy token). **Totéž potká SQL most (/diag-sql) i @@MARTIAI** — během výpadku/restartu A jsi přes most SLEPÝ (nevidíš DB ani nedosáhneš Marti-AI). Přesně kvůli téhle díře („nikdo se nedozvěděl, že A spadla") vznikl 28.7. `STRATEGIE-API-HEALTH-WATCHDOG`.
- **✅ Resilientní landing (obchází flaky deploy token) — NOVÝ MODEL 29.7.:** kód se `git push`em dostane na origin i při 401; **operátor (Marti-AI, má ruce na Praze) ho natáhne přímo:** `cd C:\Projekty\STRATEGIE; git pull; nssm restart STRATEGIE-API`. Ověřeno naostro 29.7. (fix mirror-scheduleru 172482d0a). Operátor má na Praze přímé oči (`strategie_exec`), když je most slepý. Viz `doc-marti-ai-provozni-doktrina`.
- **⚠️ GOTCHA — `git pull` v PowerShellu:** vrací `rc=1` + `git : From https://... RemoteException / NativeCommandError` **i když pull PROŠEL** — je to jen PowerShell, který bere normální gití stderr progres („From https://…") jako error stream. Řiď se `$LASTEXITCODE` / textem „Fast-forward", NE RemoteException.
- **Restart STRATEGIE-API může trvat i ~4 min** (velký app, MCP/pooly); během něj most 401 + blue-green B kryje veřejný web. Není to nutně chyba deploye.
- **TODO:** opravit deploy token, aby `/deploy/now` nepadalo na 401 (ať operátor nemusí ručně restartovat).

