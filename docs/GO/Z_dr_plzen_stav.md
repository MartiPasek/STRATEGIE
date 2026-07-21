# Záložní prostředí Plzeň — realizovaný stav (DR standby NAOSTRO, permanentní)

**Datum:** 19.–21. 7. 2026. **Kontext:** realizace plánu obnovy [[doc-go-dr_plan_obnovy]]. Plzeňský box = **EC-SERVER2** (192.168.30.11, tentýž kde běží EUROSOFT-MCP + Caddy brána). K 21. 7. je Plzeň **permanentní živý standby** — ne jen test boot.

## Co běží (HOTOVO a autonomní)
1. **PostgreSQL 16 + restornutá `data_db`** (587+ tabulek, pgvector, vektory). Ověřeno: 390 konverzací, ~12–18 tis. vektorů.
2. **Autonomní noční přenos Praha → Plzeň** (bez člověka): **3:00** noční záloha na 188.12 (postgres, kompletní dump) → **3:15** `STRATEGIE-DR-Push` (188.12) nahraje k cloud API (RAW `POST /api/v1/ops/dr/upload`) → **3:30** `STRATEGIE-DR-PullRestore` (Plzeň) stáhne + `pg_restore` do lokální `data_db`. Ověřeno rc=0.
3. **STRATEGIE jako trvalá služba** — NSSM **`STRATEGIE-API`** (autostart, restart-on-exit): `uvicorn apps.api.main:app :8080` z `C:\projekty\strategie\.venv`. Nahradil foreground uvicorn z test bootu.

## 🔑 Bezpečnostní pojistka standby (kritické, ověřeno v logu)
Služba běží se **`STRATEGIE_DR_STANDBY=1`** (+ `STRATEGIE_INSTANCE_NAME=plzen-dr`). Log potvrzuje `secondary (strategie) — background schedulery (att_sync, mirror) VYPNUTY`. Bez toho by clone psal do PRODUKCE. Po každém (re)startu ověřit v `logs\strategie-api.out.log`.

## Deník obnov (samokontrola) — DŮKAZ PRO ISO/TISAX
Task **STRATEGIE-DR-SelfCheck** (3:45, SYSTEM) dotáže lokální `data_db` (DB online, stáří dat, počty tabulek/konverzací/vektorů, pgvector) → HTTPS `POST /api/v1/ops/dr/selfcheck` (X-DR-Token). Cloud spočítá verdikt **OK / NENÍ OK + důvod**, zapíše do **`fw.dr_selfcheck`** (strojově psaný deník obnov) a při chybě pošle **push**. V řídicím pultu karta **🛟 Obnova** (verdikt, stáří dat, počty, historie). Ověřeno OK 21. 7. (601 tab / 390 konv / 11 374 vek / data ~20 h).

## Permanentní standby — dodělávky HOTOVO (21. 7.)
- **Role + granty** v lokální `data_db`: 6 rolí 1:1 dle produkce (`strategie`,`Marti-AI`,`Marti`(super),`Kristy` + skupiny `fw_owners`/`mod_owners`), heslo `Marti-AI`=lokální postgres → hardcoded strategie_pg připojení funguje.
- **Restore drží granty**: z `dr_pull_restore.ps1` odebráno `--no-privileges` (role existují → granty se obnoví z dumpu každou noc).
- **Caddy**: do `C:\caddy\Caddyfile` PŘIDÁN (ne přepsán) site blok `strategie-system.com { bind 127.0.0.1 192.168.30.11; reverse_proxy 127.0.0.1:8080 }`. Validate+reload OK, `api.eurosoft.com`/MCP netknuté (ověřeno db=mssql po reloadu).

## Zbývá jediné
- **DNS A záznam `strategie-system.com`** → veřejná IP EC-SERVER2 (nejjednodušeji stejná jako `api.eurosoft.com` — port-forward 443 už existuje, Caddy routuje dle názvu; jinak nová IP + NAT 80/443 na Mikrotiku) = **Michal Šik**. Pak Caddy vytáhne Let's Encrypt cert a záloha je dostupná zvenku = „jeden krok obnovy" z plánu.
- Volitelně `ENCRYPTION_KEY` (pražský) do env služby — na dešifrování mailbox hesel/podpisů; na čtení netřeba.

## Význam
Naplňuje plán obnovy: RPO ≤ 1 prac. den, RTO prakticky okamžité, geo oddělení Praha–Plzeň, nezávislost na jednotlivci, **denně testovaná obnova s datovaným deníkem** (fw.dr_selfcheck). Detaily + gráble nasazení: paměť `dr-plzen-app-boot`, `dr-transfer-stav`.

---
*Aktualizoval Claude (C23) přes bridge, 21. 7. 2026 — z test bootu na permanentní standby. Nahrazuje verzi z 19. 7.*
