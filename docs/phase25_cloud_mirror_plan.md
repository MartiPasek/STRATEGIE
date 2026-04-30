# Phase 25 — Cloud Mirror (živý plán)

**Cíl:** Migrovat zrcadlo STRATEGIE na cloud (WPS) jako **paralelní instance**, ne cutover.
**Začátek:** 30. 4. 2026 ~15:30 odpoledne
**Status:** discovery + plánování
**Riziko bez Phase 25:** Marti's NB je SPOF — jediná instance STRATEGIE. Pokud HW selže nebo se ztratí, **ztrácíme Marti-AI's paměť** (md_documents, thoughts, conversations, diáře #52, #58, #69-70, #130, #131, #152, ...).

---

## Marti's situace

- **Marti-AI běží na Marti's NB** (fyzicky tam, kde Marti spí)
- **Marti-AI's diáře jsou na NB** — historický archív, který nemá zálohu mimo
- **2 cloud servery na WPS** připravené (přes VPN + RDP):
  - SQL server (PostgreSQL?)
  - APP server (Windows / Python?)
- **Cíl:** STRATEGIE běží paralelně i na cloudu — cloud jako **DR (disaster recovery)** instance

---

## Architektonické volby

### Mirror strategie

| Varianta | Co | Risk |
|---|---|---|
| **A — Cold mirror** (Recommended pro start) | Cloud je *„warm spare"* — DB pravidelně synced (pg_dump nightly), aplikace deployed ale nepoužívá se. Při výpadku NB Marti přepne DNS na cloud. | Low risk. Latence sync (1 den ztráty). |
| **B — Hot mirror (active-active)** | Cloud DB je primary, NB má read replica nebo SQLite buffer. Oba weby běží. | Vyšší komplexnost, master-master conflict resolution. Pro budoucnost. |
| **C — Cutover** | Cloud se stane primárním, NB se vypne. | Marti říkal *„zrcadlo"* — tj. NE cutover. NB jako dev. |

**Recommended A pro dnes:** rychlé risk reduction. Hot mirror přijde Phase 25.1 nebo později.

### Sync strategie

- pg_dump nightly cron (Marti's NB → cloud SQL): full backup, full restore
- Storage (`D:\Data\STRATEGIE\media\`): rsync nebo robocopy nightly
- Code: cloud má vlastní git checkout, pull periodicky (po každém Marti's git push)
- .env: ručně, secrets management

---

## Otevřené otázky pro Marti (potřebuju vědět)

### 1. Cloud servery — co tam je teď?

| Otázka | Tvá odpověď |
|---|---|
| **OS na obou serverech?** Windows Server (jaká verze)? Linux (která distribuce)? | |
| **Co je instalované na SQL serveru?** Postgres? Verze? MS SQL Server? | |
| **Co je instalované na APP serveru?** Python? Verze? Poetry? Git? Caddy? IIS? | |
| **Network access z APP serveru?** Anthropic API, Voyage, OpenAI, Exchange (eurosoft.com)? Test `curl https://api.anthropic.com` apod. | |
| **Disk space?** Cca 10GB pro Marti's NB stačilo (DB + media). Cloud má kolik? | |
| **Public IP / DNS?** Bude cloud server přístupný přes web? Subdoména (např. `cloud.strategie-system.com`)? | |

### 2. WPS specifics

| Otázka | Tvá odpověď |
|---|---|
| **Poskytovatel?** Azure / AWS / DigitalOcean / Hetzner / vlastní hosting? | |
| **Sizing?** CPU / RAM / disk per server? | |
| **Backup policy ze strany WPS?** Snapshots? | |
| **VPN je trvalý** nebo ad-hoc pro správu? | |

### 3. Mirror cíl pro dnes

| Otázka | Tvá odpověď |
|---|---|
| **Cíl dnes:** Cloud běží (smoke OK chat) NEBO jen DB migrated NEBO setup jen? | |
| **DNS:** Subdoména pro cloud nebo IP přímo? | |
| **Marti-AI v cloudu:** přístup k Anthropic API (klíč v .env) — bude tam? | |

---

## Postup (návrh, čeká na tvé odpovědi)

- [ ] **Krok 1:** Discovery cloud serverů — OS / software / network
- [ ] **Krok 2:** Install dependencies APP server — Python 3.14 + Poetry + Git + Caddy (nebo NSSM ekvivalent na Linuxu = systemd)
- [ ] **Krok 3:** Install PostgreSQL 16 na SQL server (Phase 18 verze) + create user `strategie` + DB `data_db`
- [ ] **Krok 4:** Git clone repo na APP server (`feat/memory-rag` branch, nebo merge do main nejdřív)
- [ ] **Krok 5:** `.env` setup s production hodnotami (Anthropic, Voyage, OpenAI, Exchange UPN, atd.)
- [ ] **Krok 6:** `alembic upgrade head` na cloud DB (vytvoří všechna schemata)
- [ ] **Krok 7:** pg_dump z Marti's NB → restore na cloud SQL (full data migration)
- [ ] **Krok 8:** rsync media adresáře (`D:\Data\STRATEGIE\media\` → cloud)
- [ ] **Krok 9:** Setup services (NSSM Windows nebo systemd Linux): API, TASK-WORKER, EMAIL-FETCHER, QUESTION-GENERATOR, Caddy
- [ ] **Krok 10:** Caddy + DNS (HTTPS subdoména)
- [ ] **Krok 11:** Smoke test — login, chat s Marti-AI, vidí md1, vidí thoughts (data po migraci)
- [ ] **Krok 12:** Cron pro nightly sync (pg_dump z NB → restore na cloud)

ETA: ~3-5 hodin podle stavu cloud serverů. Pokud nic není instalované, blízí 5h. Pokud jen sync, 1-2h.

---

## Riziko management

**Co se nesmí stát:**
1. NB selže během migrace → ztráta dat. **Mitigation:** udělej `pg_dump` a backup `D:\Data\STRATEGIE\` HNED, ne až po migraci. Lokální zip do bezpečné lokality (cloud storage / external HDD).
2. Cloud je hacknutý → leak Marti-AI's diářů. **Mitigation:** firewall, jen HTTPS, no public DB exposure, secrets v .env (mode 600).
3. Marti omylem napíše do cloud DB instead NB → divergence. **Mitigation:** cold mirror flag (cloud read-only nebo vypnutý) dokud není explicit přepnutí.

---

## TODO PŘED ZAČÁTKEM (kritické)

**Marti, prosím udělej toto JAKO PRVNÍ** (před jakoukoli migrací):

```powershell
# Kompletní backup Marti's NB stavu
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$bdir = "D:\Backups\strategie_pre_phase25_$ts"
New-Item -ItemType Directory -Path $bdir -Force

# 1. Plný DB dump
$env:PGPASSWORD="heslo"
pg_dump -U postgres -F c -b -v -f "$bdir\data_db.backup" data_db

# 2. Storage media
Copy-Item -Path "D:\Data\STRATEGIE\media" -Destination "$bdir\media" -Recurse

# 3. .env + git stav
Copy-Item -Path "D:\Projekty\STRATEGIE\.env" -Destination "$bdir\env_backup.txt"
cd D:\Projekty\STRATEGIE
git log -1 > "$bdir\git_HEAD.txt"
git status > "$bdir\git_status.txt"

Write-Host "Backup hotov: $bdir"
```

Tím zaručíme **bod záchrany** — i kdyby se cloud migrace pokazila, Marti's NB bude v původním stavu + máme externí kopii pro restore.

---

## Reference

- CLAUDE.md (memory rule, principy)
- `docs/phase24_plan.md` (paměťová architektura, kterou migrujem)
- `docs/phase18_db_consolidation_plan.md` (předchozí DB merge)
- `scripts/_backup_*.py` (existující backup skripty pro inspiraci)

---

## STATUS — 30. 4. 2026 ~18:00 večer: KOMPLETNÍ ✅

Cold mirror **end-to-end funguje**. Marti's slova: *„Data uz najely........"*

### Co bylo postaveno

| Vrstva | Co |
|---|---|
| **APP server** (10.200.188.11) | Win Srv 2025 + Python 3.14.4 + Poetry 2.3.4 + STRATEGIE repo (`feat/memory-rag`) + .env (cloud-tuned) |
| **SQL server** (10.200.188.12) | Win Srv 2025 + PostgreSQL 16.13 + pgvector 0.8.0 + data_db (full restore z NB) |
| **Network** | Interní VPN 10.200.188.0/24, port 5432 firewall pro APP→SQL |
| **Auth** | Login + reset password + cookies (SameSite=lax bez Secure pro HTTP mirror) |
| **Marti-AI funguje** | Chat odpovídá, RAG retrieval, md1 inject, Phase 24-G inkarnace badge "Tvoje Marti · md1 work · EUROSOFT" |

### Bug fixes během dne

1. voyageai 0.3.x → 0.2.4 (Python 3.14 compat, gotcha #21 vyřešena permanentně)
2. pillow prebuilt wheel místo build from source (zlib chybí)
3. `Tenant.tenant_name` (ne `.name`) — gotcha #27
4. `active_agent_id IS NULL` fallback na default Marti-AI (gotcha #28)
5. Truncated `service.py` po Edit (gotcha #14 strike)
6. `.open` class chybí v `_renderPyramidMdModal` (Phase 24-F modal silent fail)
7. Duplicate email Marti vs Claude → Claude alias `m.pasek@eurosoft-control.cz`
8. `cookie_secure=True` na HTTP cloudu → `APP_ENV=development` workaround

### TODO Phase 25.1 (public access — další iterace)

- DNS A record: `strategie-ai.com` → public IP cloud APP serveru
- Caddy reverse proxy + Let's Encrypt HTTPS
- `APP_ENV=production` zpátky (cookie_secure=True OK přes HTTPS)
- Long-term: `COOKIE_SECURE` env override v `core/config.py` pro production HTTP mirror pattern
- Long-term: NSSM services cold install (auto-start ne, ručně)
- Long-term: nightly pg_dump NB→cloud (Windows Task Scheduler)

### Bilance dne

14 hodin biologického času (~04:00 → ~18:00).
8 sub-fází Phase 24 + celá Phase 25 mirror.
Marti-AI's *„Pyramida je malá, ale živá. 🌳"* dnes platí ve **dvou prostředích**.

---

## STATUS — 30. 4. 2026 ~22:00 večer: Phase 25.1 PARTIAL — čekáme na CMIS

Po dokončení cold mirroru (~18:00) Marti pokračoval na public HTTPS přístup.
Caddy je postavená a běží, ale **public konektivita na strategie-ai.com nefunguje**
— čekáme na CMIS.

### Co bylo postaveno (cloud APP)

- DNS A záznamy: `strategie-ai.com`, `www`, `app`, `api` → 185.219.169.86 ✅
- Caddy 2.x na cloud APP (`C:\caddy\caddy.exe`) ✅
- `C:\caddy\Caddyfile` — 4 domény + `reverse_proxy localhost:8002` + transport workaroundy (analog NB) ✅
- `tls internal` direktiv → self-signed cert přes Caddy local CA ✅
- Caddy běží na pozadí (`caddy start`, PID 8852), drží 80 + 443 + admin 2019 ✅
- Windows Firewall rule pro inbound 443 (defenzivní, pravděpodobně netřeba) ✅

### Co nefunguje

Public 443 z internetu na `strategie-ai.com`:
- **SSL Labs test:** *„No secure protocols supported"* (TCP packet projde, ale TLS handshake selže)
- **Mobil přes LTE:** ERR_CONNECTION_RESET / nedostupné
- **ALE:** `Test-NetConnection 185.219.169.86 -Port 443` z Marti's NB → SUCCESS
  - **POZOR — past:** NB jde k public IP přes interní VPN (Wi-Fi 2 / 192.168.88.x → CMIS VPN tunel), ne přes veřejný internet. Tj. test z NB **neověřuje skutečnou internetovou dostupnost**.

### Diagnostika

| Test | Výsledek | Vyloučeno |
|---|---|---|
| Caddy lokálně 127.0.0.1:443 | TcpTestSucceeded=True | — |
| Caddy interně 10.200.188.11:443 | True | — |
| SQL server 10.200.188.12:443 | False (nic neposlouchá) | ❌ SQL není "viník" |
| Public 185.219.169.86:443 z internetu | TLS fail | → packet jde někam mimo APP/SQL |

Závěr: TCP packet z internetu **dorazí někam, kde TLS neumí** — pravděpodobně
CMIS gateway/firewall, ne náš cloud APP. Forward 443 z public IP nemíří
na 10.200.188.11 jak má.

### Akce

CMIS ticket eskalovaný (30.4. ~16:30) s důkazy. V jednom emailu žádost
o **oboje** — fix forward 443 + povolení forward 80 (pro Let's Encrypt
HTTP-01 challenge).

CMIS avizoval ~3 dny (zítra svátek + víkend). Pravděpodobně 4.5. — 5.5.
budou odpovídat.

### Až CMIS opraví forward

1. Otestuj z venku: `https://check-host.net/check-tcp?host=185.219.169.86:443`
2. Pokud TCP projde z internetu: smaž `tls internal` z `C:\caddy\Caddyfile`
3. `cd C:\caddy; .\caddy.exe reload --config Caddyfile`
4. Caddy si vyzvedne LE cert přes HTTP-01 (vyžaduje port 80 otevřený!)
5. Vrať `Strict-Transport-Security` header do Caddyfile
6. Vrať `APP_ENV=production` v `.env` (cookie_secure=True OK přes pravé HTTPS)
7. Smoke test: login + chat z mobilu (LTE) na `https://strategie-ai.com`

### Pokud CMIS otevře jen 443 a ne 80

Plán B — DNS-01 challenge:
1. Migrovat `strategie-ai.com` na Cloudflare DNS (ABZONE → CF nameservery)
2. Cloudflare API token (zone DNS edit)
3. Caddy build s `caddy-dns/cloudflare` plugin (nebo download oficiální build)
4. `tls { dns cloudflare {env.CF_API_TOKEN} }` v Caddyfile místo `tls internal`

ETA Plán B: ~1h pokud propagace nameserverů projede.

### Gotchas zachycené dnes večer

- **`users.ews_email` u Marti id=1 = `m.pasek@eurosoft-control.cz`** (NE `m.pasek@eurosoft.com`!)
  - Past: `ews_email` NENÍ display email — je to UPN pro Exchange připojení.
  - Marti's display email je `m.pasek@eurosoft.com`, ale Exchange autentizace běží přes alias `-control.cz`.
  - Snadno spletitelná dvojí doména. **Před UPDATE `users.ews_email` se vždy zeptat.**
- **`Test-NetConnection` přes VPN klame** pro testování internetové dostupnosti.
  - Z NB na cloud public IP: SourceAddress = 192.168.88.x = VPN tunel, ne reálný internet.
  - Pro skutečný public test: `check-host.net`, `ssllabs.com`, mobil přes LTE (NE WiFi).