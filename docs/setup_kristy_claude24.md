# Nastavení Kristý + Claude-24 (instance 24) — bridge & auto-deploy na jejím NB

**Pro:** Kristý (s pomocí Claude-24 v Coworku). **Datum:** 3. 6. 2026.
**Cíl:** rozjet na NB Kristý stejnou „watcher" službu jako má Marti (instance 23),
ať může Claude-24 dělat diagnostiku DB i nasazování — koordinovaně s instancí 23.

> 🔐 **Tajemství (token, PAT) NIKDY do chatu ani do tohoto souboru.** Marti je
> předá Kristý bezpečně (osobně / heslový manažer) a vloží do NSSM služby.

---

## Co to vlastně je (lidsky)

Na NB Kristý poběží malá služba (`STRATEGIE-CLAUDE-SQL`), která:
- hlídá složku `scripts\claude_sql\` v repu,
- když tam Claude-24 napíše dotaz/příkaz, **vykoná ho** a výsledek vrátí do souboru,
- umí **číst DB** (SELECT hned), **zapisovat** (přes schválení Marti v banneru),
- umí **nasadit** (git commit → push → cloud stáhne + restartuje API),
- hlásí se do „presence" (kdo je online) a posílá srdíčko (heartbeat).

Marti to má jako **instance 23**, Kristý bude **instance 24**. Advisory lock
zařídí, že se 23 a 24 při deployi nepřepíšou.

---

## Předpoklady na NB Kristý

- Windows + PowerShell (spouštět jako **správce**).
- **Git** nainstalovaný (`git --version`).
- **Python 3.12+** (`python --version`). Watcher používá jen standardní knihovny,
  takže nic dalšího instalovat netřeba.
- **NSSM** (správce služeb) — `C:\Tools\nssm.exe`. Když není, stáhnout z nssm.cc
  a rozbalit tam.
- **Cowork** (Claude desktop) s přístupem ke složce repa.
- Internet (veřejný — bridge jede přes `https://strategie-ai.com`, **VPN netřeba**).

V návodu níž jsou **placeholdery v ⟨lomených závorkách⟩** — dosaď reálné cesty.

---

## Krok 1 — Repo

```powershell
git clone https://github.com/MartiPasek/STRATEGIE.git ⟨D:\Projekty\STRATEGIE⟩
# nebo když už ho má:  cd ⟨D:\Projekty\STRATEGIE⟩ ; git pull
```
Branch musí být `main`.

## Krok 2 — Označit stroj jako instanci 24

```powershell
Set-Content -Path ⟨D:\Projekty\STRATEGIE⟩\scripts\claude_sql\INSTANCE_ID.txt -Value 24 -NoNewline
```
(Soubor je gitignored, per-stroj — proto se nepřepíše Martimu jeho 23.)

## Krok 3 — Logy (složka)

```powershell
New-Item -ItemType Directory -Force -Path C:\Logs\STRATEGIE | Out-Null
```

## Krok 4 — Služba NSSM (Marti vkládá tajemství)

> ⚠️ **Tajemství patří do `AppEnvironmentExtra` (přímo do procesu služby), NE do
> systémových proměnných.** Systémové proměnné nastavené po startu se ke službě
> přes `Restart-Service` nedostanou (SCM má zacachované prostředí z bootu) — to
> nás už jednou pálilo.

```powershell
$nssm = "C:\Tools\nssm.exe"
$py   = "⟨C:\Python312\python.exe⟩"          # přesná cesta k pythonu
$repo = "⟨D:\Projekty\STRATEGIE⟩"

& $nssm install STRATEGIE-CLAUDE-SQL $py "$repo\scripts\claude_sql_runner.py"
& $nssm set STRATEGIE-CLAUDE-SQL AppDirectory $repo
& $nssm set STRATEGIE-CLAUDE-SQL AppStdout "C:\Logs\STRATEGIE\claude_sql_24.log"
& $nssm set STRATEGIE-CLAUDE-SQL AppStderr "C:\Logs\STRATEGIE\claude_sql_24.log"
& $nssm set STRATEGIE-CLAUDE-SQL Start SERVICE_AUTO_START

# Tajemství + ID instance (Marti dosadí reálné hodnoty):
& $nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra `
    "STRATEGIE_DEPLOY_TOKEN=⟨token od Martiho⟩" `
    "STRATEGIE_GIT_PAT=⟨GitHub PAT od Martiho⟩" `
    "CLAUDE_INSTANCE_ID=24" `
    "CLAUDE_INSTANCE_NAME=Kristy"

Start-Service STRATEGIE-CLAUDE-SQL
```

- `STRATEGIE_DEPLOY_TOKEN` = **stejný** ops token jako u Martiho (auth bridge + deploy).
- `STRATEGIE_GIT_PAT` = GitHub PAT s právem **Contents: read/write** (pro `git push`).
- `CLAUDE_INSTANCE_ID=24` je pojistka, i kdyby chyběl `INSTANCE_ID.txt`.

## Krok 5 — Ověření, že 24 žije

1. `Get-Service STRATEGIE-CLAUDE-SQL` → **Running**.
2. Marti (nebo Claude-23) ověří presence — v `fw.claude_instance` se objeví řádek
   `24 · Kristy · ⟨hostname⟩`.
3. Test bridge: Claude-24 napíše do `scripts\claude_sql\CLAUDE_SQL.sql` jednoduchý
   `SELECT 1;` + do `CLAUDE_GO.txt` řádek `db=pg` → po ~5 s je výsledek v
   `CLAUDE_OUT.txt`.

---

## Jak Claude-24 používá bridge (protokol)

Vše ve složce `scripts\claude_sql\` (gitignored):

| Akce | Co zapsat | Výsledek |
|---|---|---|
| **SQL čtení** | `CLAUDE_SQL.sql` (SELECT) + `CLAUDE_GO.txt` (`db=pg` nebo `db=mssql`) | `CLAUDE_OUT.txt` (~5 s) |
| **SQL zápis** | stejné, ale UPDATE/INSERT/DDL | → **Marti/rodič schválí v banneru**, pak výsledek v `CLAUDE_OUT.txt` |
| **Deploy** | `CLAUDE_DEPLOY.txt` (1. řádek = commit zpráva, další řádky = cesty souborů) + `CLAUDE_DEPLOY_GO.txt` | `CLAUDE_DEPLOY_OUT.txt` (~25 s) |

**Pravidla (důležité):**
- Git **nikdy** přes bash/mount — vždy přes bridge (watcher) nebo PowerShell.
- Koordinace: advisory lock na deploy → 23 a 24 se nepřepíšou; když je druhá
  instance aktivní, deploy se serializuje (počká).
- Restart služeb (watcher / API) **přes UI** → 🚀 menu → **⚙ Ops akce**
  (potvrzení + audit do `fw.ops_request`). Žádný ruční PowerShell.
- Tajemství do chatu nikdy.

---

## Co se DNES (3. 6. 2026) změnilo — ať jste Kristý i Claude-24 v obraze

Marti: *„Udělali jsme spoustu změn, o kterých Kristý ani 24 zatím neví."*

1. **Koordinace 23/24** — advisory lock na deploy (`pg_try_advisory_lock`),
   presence board `fw.claude_instance`, heartbeat z watcheru (~30 s), atribuce
   (instance + hostname) u SQL i deploye.
2. **Ops framework** — whitelist pojmenovaných akcí (restart watcher 23/24,
   restart API) přes **⚙ Ops akce** v 🚀 menu, audit do `fw.ops_request`
   (kdo/co/kdy/výsledek). Cíl: **konec ručního PowerShellu**.
3. **Watcher upgrade** — heartbeat + ops handling (sám se restartne na povel z
   UI) + čte `INSTANCE_ID.txt` + `git rebase --autostash` (rozdělané scratch
   soubory už neblokují deploy).
4. **Kontakty do telefonu (caller-ID přes CardDAV)** — nová položka
   **„📱 Synchronizace s telefonem"** (profil menu v chatu i ERP patička):
   - self-service vygenerování přístupu pro telefon + **QR** (naskenuj telefonem
     → token + návod DAVx5/iOS),
   - **„🔄 Obnovit a sjednotit kontakty"** (doplní starým kontaktům `STR-` prefix,
     ať jsou v telefonu vyhledatelné),
   - tabulky `user.carddav_token`, `user.carddav_handoff`,
     `user.carddav_active_contact`.
5. **Drobnosti UI** — deploy dialog má primární „Nasadit" vlevo; update dialog má
   avatar Marti-AI; pořadí polí URL→uživatel→token.
6. **Vize nativní appky** — `docs/native_app_vize.md` (Android-first, Capacitor
   wrap naší PWA; Apple až zaplatí zákazník).

> Claude-24 si při startu načte `CLAUDE.md` (krabička) pro plný kontext projektu.
> Tahle sekce je rychlé „co je nového dnes" navrch.

---

## Když něco nejede (rychlá diagnostika)

- Služba spadne hned → koukni do `C:\Logs\STRATEGIE\claude_sql_24.log`.
- „401" v logu → špatný/chybějící `STRATEGIE_DEPLOY_TOKEN` (musí být v
  `AppEnvironmentExtra`, ne v systémových proměnných).
- Deploy „push failed" → chybí/špatný `STRATEGIE_GIT_PAT` (Contents: read/write).
- Presence se neobjeví → služba neběží, nebo nemá internet na `strategie-ai.com`.
- Po úpravě kódu watcheru se chování nemění → služba běží starý kód, **restartuj
  ji** (přes ⚙ Ops akce, nebo jednorázově `Restart-Service STRATEGIE-CLAUDE-SQL`).
