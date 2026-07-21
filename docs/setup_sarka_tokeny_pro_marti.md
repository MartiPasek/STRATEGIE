# Návod pro Martiho — získání tokenů pro Šárku (instance 25)

**Pro:** Marti. **Datum:** 16. 6. 2026.
**Cíl:** připravit dvě tajemství, která půjdou do NSSM služby `STRATEGIE-CLAUDE-SQL`
na stroji Šárky (Krok 4 v `setup_sarka_claude25.md`):

- `STRATEGIE_DEPLOY_TOKEN` — ops/bridge token (auth bridge + deploy)
- `STRATEGIE_GIT_PAT` — GitHub token pro `git push`

> 🔐 **Žádné tajemství NIKDY do chatu, do tohoto souboru ani do gitu.** Předej je
> Šárce bezpečně (heslový manažer / osobně) a vlož přímo do `AppEnvironmentExtra`
> NSSM služby na jejím stroji.

---

## Token 1 — `STRATEGIE_DEPLOY_TOKEN` (NEgeneruje se nový!)

Tohle je **stejný sdílený token jako u instancí 23 a 24** i jako na cloudu
(`STRATEGIE-API`). **Nesmí se vygenerovat nový** — jiná hodnota = `401` a rozbije
se bridge i deploy u všech. Jen ho **zkopíruj** ze svého stroje.

Na **svém NB (instance 23)** v PowerShellu:

```powershell
C:\Tools\nssm.exe get STRATEGIE-CLAUDE-SQL AppEnvironmentExtra
```

Ve výpisu najdi řádek `STRATEGIE_DEPLOY_TOKEN=…` a zkopíruj **přesně tu hodnotu**.
(Tahle hodnota musí být identická na 23, 24, 25 i na cloudu.)

➡️ Tahle hodnota jde do Šáriny služby jako `STRATEGIE_DEPLOY_TOKEN`.

---

## Token 2 — `STRATEGIE_GIT_PAT` (GitHub, pro `git push`)

Repozitář `github.com/MartiPasek/STRATEGIE` je pod **osobním účtem** (ne organizace).
To má jeden důležitý důsledek pro typ tokenu:

- **Fine-grained token** scoped na tenhle repo umí vytvořit **jen vlastník účtu (ty)**.
  Spolupracovník (Šárka) si fine-grained token na *cizí* osobní repo nenascopuje.
- Pokud chceš token na **Šárčině** účtu, musí to být **classic** token se scope `repo`.

### ✅ Doporučeně — fine-grained token z TVÉHO účtu (jeden na stroj)

Nejjednodušší a nejlíp ovladatelné: vyrobíš token ze svého účtu, omezený jen na
repo STRATEGIE, a dáš ho do Šáriny služby. Commity se i tak atribuují `claude-25`
(autora nastavuje watcher přes `user.email=claude-25@strategie-ai.com`), audit
v DB jede přes `INSTANCE_ID=25`. Tip: udělej **samostatný token pro každý stroj**
(23/24/25) s vlastním názvem → můžeš kterýkoli odvolat zvlášť.

Postup:

1. **github.com** → vpravo nahoře tvůj avatar → **Settings**.
2. Úplně dole v levém menu → **Developer settings**.
3. **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
4. **Token name:** `STRATEGIE bridge - NB Sarka (25)`.
5. **Expiration:** zvol (doporučuju max, např. 1 rok, a dej si připomínku na rotaci).
6. **Resource owner:** tvůj účet **MartiPasek**.
7. **Repository access:** **Only select repositories** → vyber **STRATEGIE**.
8. **Permissions** → **Repository permissions** → **Contents: Read and write**
   (Metadata se samo přepne na Read-only — nech být). Nic víc netřeba.
9. **Generate token** → zkopíruj hodnotu `github_pat_…` (**ukáže se jen jednou!**).

➡️ Tahle hodnota jde do Šáriny služby jako `STRATEGIE_GIT_PAT`.

### Alternativa — classic token na Šárčině účtu (per-osoba)

Když chceš, aby push autentizoval přímo Šárčin GitHub účet (čistší dělení):

1. Nejdřív přidej Šárku jako **collaborator** s právem **Write**:
   repo STRATEGIE → **Settings → Collaborators → Add people** → její username →
   role **Write**. Ona pozvánku přijme (mailem).
2. Šárka na **svém** účtu: **Settings → Developer settings →
   Personal access tokens → Tokens (classic) → Generate new token (classic)**.
3. **Note:** `STRATEGIE bridge`; **Expiration:** zvol; **Scope:** zaškrtni **`repo`**.
4. **Generate token** → hodnota `ghp_…` (ukáže se jen jednou).

> Pozn.: classic token se scope `repo` je širší (přístup ke všem jejím repo). Proto
> je doporučená varianta fine-grained z tvého účtu — užší a pod tvou kontrolou.

---

## Kam tokeny patří (Krok 4 setupu)

Na **stroji Šárky**, PowerShell jako správce, do `AppEnvironmentExtra` služby
(viz `setup_sarka_claude25.md`):

```powershell
& $nssm set STRATEGIE-CLAUDE-SQL AppEnvironmentExtra `
    "STRATEGIE_DEPLOY_TOKEN=<Token 1 - zkopirovany ops token>" `
    "STRATEGIE_GIT_PAT=<Token 2 - GitHub PAT>" `
    "CLAUDE_INSTANCE_ID=25" `
    "CLAUDE_INSTANCE_NAME=Sarka"
```

⚠️ Tajemství **do `AppEnvironmentExtra`**, ne do systémových proměnných (ty se ke
službě přes `Restart-Service` nedostanou — SCM cache z bootu).

---

## Ověření (po `Start-Service`)

- Log `C:\Logs\STRATEGIE\claude_sql_25.log`:
  - **žádné** `401` → `STRATEGIE_DEPLOY_TOKEN` sedí.
  - deploy „push failed" → špatný/chybný `STRATEGIE_GIT_PAT` nebo chybí Write přístup.
- Presence: v `fw.claude_instance` přibude `25 · Sarka · <hostname>`.
- Bridge test: `SELECT 1;` přes `CLAUDE_SQL.sql` + `db=pg` → výsledek v `CLAUDE_OUT.txt`.

---

## Rotace / odvolání

- **Deploy token:** měnit jen koordinovaně (musí sednout na 23, 24, 25 i cloud naráz).
- **GitHub PAT:** odvoláš v **Developer settings** → smažeš token → vygeneruješ nový →
  přepíšeš v `AppEnvironmentExtra` → `Restart-Service STRATEGIE-CLAUDE-SQL`.
  (Proto se vyplatí mít token pojmenovaný per stroj — odvoláš jen ten jeden.)
