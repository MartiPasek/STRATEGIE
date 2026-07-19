# Záložní prostředí Plzeň — realizovaný stav (DR standby naostro)

**Datum:** 19. 7. 2026 (večer). **Kontext:** realizace plánu obnovy [[doc-go-dr_plan_obnovy]] — z PDF do běžícího stroje za jeden večer (Marti + Claude ID23). Plzeňský box = **EC-SERVER2** (tentýž server, kde běží EUROSOFT-MCP).

## Co je HOTOVO a běží
1. **PostgreSQL 16 v Plzni** + kompletní **restornutá `data_db`** (587 tabulek, pgvector, včetně vektorů). Ověřeno: 389 konverzací, 801 vektorů.
2. **Autonomní noční přenos dat Praha → Plzeň** (jede sám, bez člověka):
   - **3:00** noční záloha na 188.12 (postgres, kompletní dump = čistě ukončený DB den).
   - **3:15** task `STRATEGIE-DR-Push` (188.12) nahraje dump k cloud API (RAW stream, `POST /api/v1/ops/dr/upload`).
   - **3:30** task `STRATEGIE-DR-PullRestore` (Plzeň) stáhne (`GET /dr/download`) a `pg_restore` do lokální `data_db`. Ověřeno `rc=0`.
3. **Naběhlá STRATEGIE v Plzni** nad lokální restornutou DB (`uvicorn` na localhost:8080, přihlášení + včerejší data funkční).

## Architektura přenosu (endpoint `modules/erp/api/dr_ops.py`)
API běží na 188.11, `data_db` na 188.12, Plzeň = EC-SERVER2. Přenáší se HOTOVÝ noční dump (ne živý pg_dump — ten narážel na práva rolí). `POST /api/v1/ops/dr/upload` (188.12 push RAW — NE multipart, rozbil by archiv) · `GET /dr/meta` · `GET /dr/download` (FileResponse s Content-Length → proxy Caddy streamuje; chunked stream se dřív bufferoval a padal na 300 s). Token `DR_TRANSFER_TOKEN` (env / `dr_token.txt`, v .gitignore).

## 🔑 Bezpečnostní pojistka standby (KRITICKÉ)
Plzeňská appka MUSÍ běžet se `STRATEGIE_DR_STANDBY=1` (env; main.py commit bac9d39b). Vypne background schedulery (mirror docházky do EUROSOFT Centrály, plánovač zrcadel, automaty). **Bez toho by clone psal do PRODUKCE.** Log potvrdí `secondary — schedulery VYPNUTY`. Původní detekce sekundáru jen podle názvu složky s "prev"; `C:\projekty\strategie` ji nesplňuje → proto explicitní env přepínač.

## Prostředí Plzeň (EC-SERVER2)
Repo `C:\projekty\strategie` (git pull na aktuální). Python 3.12. Závislosti přes `poetry install --no-root` do in-project `.venv`. `.env` → `postgresql://postgres@localhost:5432/data_db`. pgvector zkopírován z 188.12 (`C:\Program Files\PostgreSQL\16\{lib\vector.dll, share\extension\vector*}`). `.pgpass` SYSTEM profil s reálným postgres heslem (pro noční SYSTEM restore).

## Co zbývá pro PERMANENTNÍ standby (leštění, jádro prokázáno)
- Role v lokální `data_db` (restore byl `--no-owner --no-privileges` → role Marti-AI/strategie/fw_owners neexistují; app jede jako postgres pro čtení, strategie_pg-závislé funkce padají) → založit role + granty.
- Autostart **služba** (NSSM STRATEGIE-API) místo foreground uvicorn.
- **Caddy** → `strategie-system.com` + **DNS A záznam** (Michal Šik).
- `ENCRYPTION_KEY` = pražský (dešifrování šifrovaných polí).

## Význam
Naplňuje plán obnovy: RPO ≤ 1 prac. den, RTO prakticky okamžité, geo oddělení Praha–Plzeň, nezávislost na jednotlivci. Důkaz pro ISO 27001 / TISAX (test obnovy s reálným během). Detailní provozní stav v paměti: dr-transfer-stav, dr-plzen-app-boot.
