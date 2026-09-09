# ČEKÁ NA ZÁPIS DO G2007 (most hlásí 401)

Připravil Claude‑26, 29. 7. 2026. Odeslat přes `@@G2007ADD`, jakmile most zase funguje.
Oblast: `system-strategie`, slug: `most-401-ztrata-deploy-tokenu`

---

# Most vrací 401 „Nejsi přihlášen" — cloud ztratil STRATEGIE_DEPLOY_TOKEN

> Incident 28.–29. 7. 2026. Odstavil **celou síť Claudů** naráz (C23, C26, C28).
> Diagnostika Claude‑26 (Peťa) + Marti‑AI.

## Příznak

- `HTTP 401 {"detail":"Nejsi přihlášen."}` na `/api/v1/erp/diag-sql` (PG i MSSQL).
- **Zároveň tiše padá heartbeat** na `/api/v1/erp/instance/heartbeat` — `_send_heartbeat()`
  má `except Exception: pass` a loguje jen když `others` není prázdné. **V logu proto
  není po výpadku ani stopa.**
- Watcher běží normálně, `forwarder started` v logu, restart nepomůže.
- Cloudová aplikace jede úplně normálně (ERP, přihlášení, docházka).

## Jak poznat, že padá i heartbeat (a nejde jen o SQL)

Sleduj **čas změny `scripts/claude_sql/OTHER_CLAUDE_WORK.txt`** — přepisuje se při každém
úspěšném heartbeatu (~30 s). Když je starší než pár minut a watcher běží, cloud odmítá
token **plošně**, ne jen na jednom endpointu. Rychlejší než hledat v logu.

## Root cause (ověřeno v kódu + na cloudu)

`router.py`, `diag_sql` (~ř. 41623) i `instance_active` (~ř. 45461) dělají prosté
porovnání: `X-Deploy-Token` z watcheru vs. `os.environ["STRATEGIE_DEPLOY_TOKEN"]`
na cloudu. **Při neshodě NEBO chybějící hodnotě spadne na `_get_uid()` + `_require_parent()`**
— a protože watcher nemá uživatelskou session, vrátí `401 Nejsi přihlášen`.

⚠️ **Hláška je zavádějící: „Nejsi přihlášen" ve skutečnosti znamená „token nesedí".**
Nehledej problém v přihlášení ani na notebooku.

**Co se stalo:** na cloud APP proměnná `STRATEGIE_DEPLOY_TOKEN` **chybí úplně**
(nebyla změněná — prostě zmizela ze systémových proměnných Windows). Podle Marti‑AI
kolem toho proběhl restart NSSM služby `STRATEGIE-CADDY` (~21:46); poslední úspěšný
kontakt 28. 7. 22:22, první 401 ve 22:50.

## Poučení — token nepatří do Machine env

Na cloudu byl token v **systémových proměnných Windows** a restart o něj přišel. Přitom
`docs/setup_claude27.md` to má zapsané: *„Token do **AppEnvironmentExtra** (NE Machine env
— SCM cache!)"*. Na noteboocích (23/24/25/26/28) je v `AppEnvironmentExtra` a drží.

➡️ **Na cloudu patří token do `AppEnvironmentExtra` služby `STRATEGIE-API`, ne do Machine env.**

## Postup obnovy

1. Hodnotu má kterýkoli notebook ve službě `STRATEGIE-CLAUDE-SQL` (registr,
   `HKLM:\SYSTEM\CurrentControlSet\Services\STRATEGIE-CLAUDE-SQL\Parameters`,
   klíč `AppEnvironmentExtra`). **Nový token se NEGENERUJE** — jedna sdílená hodnota
   pro 23/24/25/26/28 i cloud (`docs/setup_sarka_tokeny_pro_marti.md`).
2. Na cloud APP (185.219.169.86, RDP): `C:\Tools\nssm.exe get STRATEGIE-API AppEnvironmentExtra`
   → **opsat stávající proměnné**, `set` přepisuje celý seznam a co nevypíšeš, to smažeš.
3. `nssm set STRATEGIE-API AppEnvironmentExtra "<stávající…>" "STRATEGIE_DEPLOY_TOKEN=<hodnota>"`
4. `Restart-Service STRATEGIE-API`

## Poznámky k oprávněním

- Token **není nikde v repu** — `setup_sarka_tokeny_pro_marti.md` obsahuje jen návod,
  jak ho opsat, a zákaz ukládat tajemství do gitu. Kdo tam hodnotu hledá, hledá marně.
- Zápis do systémových env má Marti‑AI za 🟡 bránou (schválení rodiče). Cesta přes
  `.env` (je v `.gitignore`) je pro ni průchodnější, ale **správné místo je NSSM**.
- Peťa (C26) nemá na cloudu ani `is_admin` — `/instance/active` jí vrací 403. Bridge je
  ještě přísnější (`_require_parent`), takže most nejde obejít přes prohlížeč.

## Vedlejší nález (28. 7., stejný stroj)

Neúspěšný `git stash pop` po autostash nechal v indexu tři nedořešené trigger soubory
(`CLAUDE_DEPLOY.txt`, `CLAUDE_DEPLOY_GO.txt`, `CLAUDE_PULL_GO.txt`) → **každý další pull
padal na `fatal: Cannot autostash`** a lokál tiše zůstával 8 commitů pozadu.
Fix: `git checkout --ours -- <ty tři>` + `git add` → pull projde. Obsah trigger souborů
je bezvýznamný, řeší se tedy bez rozmýšlení, ale **je potřeba si toho všimnout** —
hlavní příznak je hláška „TVUJ LOKAL JE POZADI" v `CLAUDE_OUT.txt`.
