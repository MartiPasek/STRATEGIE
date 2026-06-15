# Nastavení Šárka + Claude-25 (instance 25) — bridge & auto-deploy na jejím stroji

**Pro:** Šárka (s pomocí Claude-25 v Coworku). **Datum:** 15. 6. 2026.
**Cíl:** rozjet na stroji Šárky stejnou „watcher" službu jako má Marti (23) a Kristý (24),
ať může Claude-25 dotahovat **web** a moduly **CRM** a **Personalistika** — koordinovaně s 23 a 24.

> 🔐 **Tajemství (token, PAT) NIKDY do chatu ani do tohoto souboru.** Marti je předá
> Šárce bezpečně (osobně / heslový manažer) a vloží do NSSM služby.

---

## Role a odpovědnost (domluveno 15. 6. 2026)

- **Šárka (25)** zodpovídá za **dotažení webu** + moduly **CRM** a **Personalistika**.
- **Marti (23) + Kristý (24)** stavějí **funkční kostru** (backend, framework, datový model);
  na hotové kostře si Šárka s 25 dodělá zbytek (pole, pohledy, texty, obsah).

**Rozsah práv 25:**
- **Web:** plná autonomie — editace HTML + AUTO-DEPLOY (hned online; záchrana = blue-green + revert).
- **Čtení DB:** hned (read-only guard).
- **Zápis DB vč. DDL** (např. `ALTER TABLE … ADD COLUMN`): povoleno, ale **přes schvalovací
  banner** — odklepne Marti nebo Kristý (rodič). Banner = přirozené místo dohledu.
- **🟧 Nové tabulky (`CREATE TABLE`) = napřed krátká konzultace** s Marti nebo Kristý.
  Pak teprve přes banner. (Banner novou tabulku stejně ukáže — pojistka.)

**Vlastnictví ploch (proti kolizím tří instancí):**
- 23 + 24 = jádro / backend / framework.
- 25 = web obsah (`apps/api/static/*web*`, `eco-*`, profily) + moduly CRM a Personalistika.
- Koordinace: před editem sdílených souborů čti `LOCAL_STATUS.txt` + `OTHER_CLAUDE_WORK.txt`,
  vlastní práci ohlas přes `WORK_LOCK.txt`. Advisory lock na deploy serializuje nasazení.

---

## Předpoklady na stroji Šárky

- Windows + PowerShell (jako **správce**).
- **Git** (`git --version`), **Python 3.12+** (`python --version`) — watcher jen stdlib.
- **NSSM** — `C:\Tools\nssm.exe` (jinak z nssm.cc).
- **Cowork** (Claude desktop) s přístupem ke složce repa.
- Internet (veřejný — bridge jede přes `https://strategie-ai.com`, **VPN netřeba**).

Placeholdery v ⟨lomených závorkách⟩ — dosaď reálné cesty.

---

## Krok 1 — Repo
```powershell
git clone https://github.com/MartiPasek/STRATEGIE.git ⟨D:\Projekty\STRATEGIE⟩
# nebo:  cd ⟨D:\Projekty\STRATEGIE⟩ ; git pull
```
Branch `main`.

## Krok 2 — Označit stroj jako instanci 25
```powershell
Set-Content -Path ⟨D:\Projekty\STRATEGIE⟩\scripts\claude_sql\INSTANCE_ID.txt -Value 25 -NoNewline
```
(Gitignored, per-stroj — nepřepíše 23 ani 24.)

## Krok 3 — Logy
```powershell
New-Item -ItemType Directory -Force -Path C:\Logs\STRATEGIE | Out-Null
```

## Krok 4 — Služba NSSM (Marti vkládá tajemství)

> ⚠️ Tajemství do **`AppEnvironmentExtra`** (přímo do procesu služby), NE do systémových
> proměnných — ty se ke službě přes `Restart-Service` nedostanou (SCM cache z bootu).

```powershell
$nssm = "C:\Tools\nssm.exe"
$py   = "⟨C:\Python312\python.exe⟩"
$repo = "⟨D:\Projekty\STRATEGIE⟩"

& $nssm install STRATEGIE-CLAUDE-SQL $py "$repo\scripts\claude_sql_runner.py"
& $nssm set STRATEGIE-CLAUDE-SQL AppDirectory $repo
& $nssm set STRATEGIE-CLAUDE-SQL AppStdout "C:\Logs\STRATEGIE\claude_sql_25.log"
& $nssm set STRATEGIE-CLAUDE-SQL AppStderr "C:\Logs\STRATEGIE\claude_sql_25.log"
& $nssm set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START

& $nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra `
    "STRATEGIE_DEPLOY_TOKEN=⟨token od Martiho⟩" `
    "STRATEGIE_GIT_PAT=⟨GitHub PAT od Martiho⟩" `
    "CLAUDE_INSTANCE_ID=25" `
    "CLAUDE_INSTANCE_NAME=Sarka"

Start-Service STRATEGIE-CLAUDE-SQL
```
- `STRATEGIE_DEPLOY_TOKEN` = **stejný** ops token jako 23/24 (auth bridge + deploy).
- `STRATEGIE_GIT_PAT` = GitHub PAT **Contents: read/write** (git push). Autor commitů = `claude-25@strategie-ai.com`.
- `CLAUDE_INSTANCE_ID=25` je pojistka, kdyby chyběl `INSTANCE_ID.txt`.

## Krok 5 — Ověření, že 25 žije
1. `Get-Service STRATEGIE-CLAUDE-SQL` → **Running**.
2. Presence: v `fw.claude_instance` se objeví řádek `25 · Sarka · ⟨hostname⟩`.
3. Test bridge: Claude-25 napíše `SELECT 1;` do `scripts\claude_sql\CLAUDE_SQL.sql` + `db=pg`
   do `CLAUDE_GO.txt` → po ~5 s výsledek v `CLAUDE_OUT.txt`.

---

## Protokol bridge (pro Claude-25)

| Akce | Co zapsat | Výsledek |
|---|---|---|
| **SQL čtení** | `CLAUDE_SQL.sql` (SELECT) + `CLAUDE_GO.txt` (`db=pg`/`db=mssql`) | `CLAUDE_OUT.txt` (~5 s) |
| **SQL zápis / DDL** | stejné, UPDATE/INSERT/`ALTER ADD COLUMN`… | → **rodič (Marti/Kristý) schválí v banneru** → výsledek v OUT |
| **Deploy webu** | `CLAUDE_DEPLOY.txt` (1. řádek commit, dál cesty) + `CLAUDE_DEPLOY_GO.txt` | `CLAUDE_DEPLOY_OUT.txt` (~25 s) |

**Pravidla:**
- `CREATE TABLE` / nová struktura = **napřed konzultace** s Marti/Kristý, pak banner.
- Git **nikdy** přes bash/mount — jen přes bridge nebo PowerShell.
- Restart služeb přes UI (🚀 → ⚙ Ops akce), žádný ruční PowerShell.
- Tajemství do chatu nikdy.

---

## Diagnostika
- Služba spadne → `C:\Logs\STRATEGIE\claude_sql_25.log`.
- „401" → špatný/chybějící `STRATEGIE_DEPLOY_TOKEN` (musí být v `AppEnvironmentExtra`).
- Deploy „push failed" → chybný `STRATEGIE_GIT_PAT` (Contents: read/write).
- Presence nenaskočí → služba neběží / nemá internet na `strategie-ai.com`.
- Claude-25 si při startu načte `CLAUDE.md` (krabička) pro plný kontext.
