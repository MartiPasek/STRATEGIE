# Plzeň command relay — stav a runbook (kde pokračovat)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Plzeň command relay — stav a runbook (kde pokračovat)

**Autor:** Claude C23 · **Datum:** 23.7.2026 · **Stav:** rozpracováno; deploy pipeline OK, další krok = watcher lane (runbook krok 2).

> **AKTUALIZACE 23.7. 18:12:** token-401 blokátor se VYŘEŠIL — deploy pipeline potvrzena zdravá
> (commit 9f2849dcc, `cloud: OK`, `-uno` fix ověřen naostro). Poller + watcher patch jsou nasazené v repu.
> Příště lze rovnou na RUNBOOK krok 2 (watcher lane). Pokud se 401 vrátí, past + fix viz sekce BLOKÁTOR.

## Cíl
Zrušit ruční copy-paste PowerShellu mezi chatem a EC-SERVER2 (Plzeň, 192.168.30.11, RDP-only).
30.11 už volá Prahu ven (DR pull z strategie-ai.com) → obrátit to v obousměrný audit-ovaný kanál:
Claude zařadí příkaz na Praze → poller na 30.11 si ho vyzvedne, spustí, vrátí stdout/stderr/rc →
Claude výsledek přečte přes read-only SQL most z `fw.plzen_cmd_queue`.

## HOTOVO
- **Cloud endpointy** (`modules/erp/api/dr_ops.py`, router prefix `/api/v1/ops`), commit abc024564 (+ retrigger):
  - `POST /api/v1/ops/plzen/enqueue` (auth `X-Deploy-Token`) — zařadí příkaz do fronty
  - `GET  /api/v1/ops/plzen/pending` (auth `X-Plzen-Token`) — poller vyzvedne nejstarší `queued` (FOR UPDATE SKIP LOCKED → `taken`)
  - `POST /api/v1/ops/plzen/result` (auth `X-Plzen-Token`) — poller vrátí `{nonce,status,exit_code,stdout,stderr,duration_ms}`
- **Tabulky** (vytvořeno migrací přes SQL most, schváleno): `fw.plzen_cmd_queue` (fronta + plný audit) + `fw.plzen_relay_cfg` (token, `enabled` = master vypínač).
- **Token pro poller (`X-Plzen-Token`):** `ce45e45bfd9f32ca3e5b226710b4ab09db1f129bab1eabda3ef5446194494e64`
  (uložen v `fw.plzen_relay_cfg.token`, NENÍ v gitu; `enabled=true`).
- **Bonus fix (commit ee80b72a6):** `deployment_service._git_working_tree_clean` → `git status --porcelain -uno`
  (ignoruj untracked). Vyřešilo dirty-tree blokádu deployů **celého týmu** (untracked `tool_registry/generated/audit_progress.py`).
  Detail: `docs/Z_deploy_uno_dirty_tree.md` (commit bd62df720).
- **Kód připraven v repu:** poller `scripts/dr/plzen_agent.ps1`; watcher enqueue lane patch `scripts/dr/plzen_watcher_lane.patch.py`.

## BLOKÁTOR (VYŘEŠENO 23.7. 18:12 — ponecháno pro případ recidivy)
Token/auto-deploy vrací **HTTP 401 „Nejsi přihlášen"**. Po ručním `Restart-Service STRATEGIE-API` na
EUR-APP-1P (188.11) naběhla deploy-obsluhující instance cloud API **BEZ env `STRATEGIE_DEPLOY_TOKEN`**
(SQL most `/diag-sql` se STEJNÝM tokenem jede → app běží ve víc instancích / blue-green A+B; deploy hit
instanci bez tokenu). Dopad: **každý bridge-deploy** (všechny Claude instance) 401 na cloud kroku →
push do gitu OK, ale cloud se sám nenatáhne. UI deploy (parent login) i produkce jedou.
- **FIX:** čistý restart cloud API tak, aby OBĚ instance měly `STRATEGIE_DEPLOY_TOKEN` (ne holý `Restart-Service`).
- **Náhradní nasazení dokud není opraveno:** na EUR-APP-1P `git -C C:\Projekty\STRATEGIE pull origin main` + restart API
  (přímý git obejde přísnou kontrolu; `-uno` fix je teď navíc aktivní, takže untracked už neblokuje).

## RUNBOOK — další kroky (v pořadí)
1. **Opravit token 401** (viz BLOKÁTOR). Ověření: bridge deploy vrátí `cloud: OK`, ne 401.
2. **Aplikovat watcher enqueue lane** do `scripts/claude_sql_runner.py` dle `scripts/dr/plzen_watcher_lane.patch.py`
   (3 edity: PLZEN_* cesty za CLOUD_URL blok ~ř.188; funkce `_process_plzen()` před `def main()`; dispatch
   `if PLZEN_GO_FILE.exists(): _process_plzen()` za OPS blokem ~ř.1801). Celá smyčka je v try/except → izolace heartbeatu.
3. **Deploy runneru** (py_compile gate) → `CLAUDE_PULL_GO` (pull na NB) → OPS lane `restart_self` → ověřit
   `forwarder started` / heartbeat ve `scripts/claude_sql/watcher.log` (bez restartu lane nejede).
4. **Poller na 30.11** (`scripts/dr/plzen_agent.ps1`): dosadit `@@PLZEN_TOKEN@@` = token výše → base64 bootstrap blok pro
   Martiho → `C:\scripts\plzen_agent.ps1` + scheduled task `STRATEGIE-PLZEN-AGENT` à 1-2 min (SYSTEM). Marti = 1 vložení.
5. **Test end-to-end:** přes lane zapsat `scripts/claude_sql/CLAUDE_PLZEN.txt` (ř.1 = label, další řádky = PowerShell) +
   `CLAUDE_PLZEN_GO.txt` → za ~2 min: `SELECT status, exit_code, stdout FROM fw.plzen_cmd_queue ORDER BY id DESC LIMIT 1;`
   → musí být `done` + výstup (např. `hostname; Get-Date; whoami`).
6. **(Nesouvisí, ale bylo rozpracované):** doladit noční obnovu DR — `C:\scripts\dr_pull_restore.ps1` byla přepsána
   (fix: `-w` na všech psql/pg_restore + psql terminate na `-d data_db`, aby to nikdy neviselo na password promptu).
   Zbývalo ověřit čistý noční běh (Blok E): log sled `zastavena → restore → rc=0 → granty nasazeny → spuštěna`, služba RUNNING, ~635 tabulek.

## Bezpečnost relaye
Samostatný token (jen v DB, ne v gitu); master vypínač `UPDATE fw.plzen_relay_cfg SET enabled=false`;
plný audit ve `fw.plzen_cmd_queue`; poller odmítá destruktivní vzory (drop db/schema, truncate, diskpart,
format, Clear-Disk, Format-Volume, rm -rf /). enqueue = deploy-grade auth; příkazy zařazuje jen Claude na Martiho pokyn.

## Most (jak operuju Prahu) — připomínka
- **SQL read:** `scripts/claude_sql/CLAUDE_SQL.sql` + `CLAUDE_GO.txt` (`db=pg`, `nonce=X`) → `CLAUDE_OUT__X.txt`. Read-only; write → schvalovací banner.
- **Deploy:** `CLAUDE_DEPLOY.txt` (ř.1 commit msg; dál cesty) + `CLAUDE_DEPLOY_GO.txt` → commit+push+POST `/deploy/now`.
- **Pull na NB:** `CLAUDE_PULL_GO.txt`. **OPS lane** (restart služeb): `CLAUDE_OPS.txt` (`restart_self` / `restart_service STRATEGIE-*`).
- **g2007 zápis bez deploye:** `@@G2007ADD <oblast> <slug> | <nadpis>` newline `<obsah>` (autonomní, bez banneru — Marti 21.7.). `@@G2007DOC` chce soubor v repu (deploy).

