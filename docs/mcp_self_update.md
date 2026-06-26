# MCP self-update — hands-free deploy EUROSOFT MCP serveru

**Cíl (Marti 26.6.2026, „naše vizitka"):** odstranit poslední ruční krok při
opravě EUROSOFT MCP serveru na EC-SERVER2 — žádné RDP, žádný `Copy-Item`,
žádný ruční `Restart-Service`. MCP si na pokyn sám stáhne opravu z repa,
zkopíruje kód do běžící složky a restartne se.

---

## Jak to funguje

MCP server (`modules/eurosoft_mcp/server.py`) má nový endpoint
**`POST /admin/self-update`** (Bearer-auth, chráněný stejně jako všechny
tooly). Když ho někdo zavolá, MCP na EC-SERVER2 sám:

1. `git pull --rebase --autostash origin main` v repu (`C:\PROJEKTY\STRATEGIE`),
2. zkopíruje `modules/eurosoft_mcp/*.py` → běžící package složka
   (`C:\eurosoft_mcp\eurosoft_mcp\`),
3. vyčistí `__pycache__` (vynutí rekompilaci),
4. naplánuje restart NSSM služby `EUROSOFT-MCP` (+2 s, detached — ať stihne
   odejít HTTP odpověď dřív, než se proces restartne).

Cloud to spouští přes bridge příkaz **`@@MCPUPDATE`** (router.py → `requests.post`
na MCP endpoint, klíč z `eurosoft_mcp_api_key`). Zdravotní check běžícího
kódu = **`@@MCPHEALTH`** (vrací `git_sha` aktuálního commitu + počet toolů).

---

## ⚠️ JEDNORÁZOVÝ BOOTSTRAP (chicken-and-egg)

Endpoint `/admin/self-update` musí být **jednou nasazen ručně**, aby vůbec
existoval. Od té chvíle je vše hands-free. Tohle je **poslední ruční deploy**
MCP serveru. Na EC-SERVER2 (PowerShell jako admin):

```powershell
cd C:\PROJEKTY\STRATEGIE
git pull origin main
Copy-Item modules\eurosoft_mcp\*.py C:\eurosoft_mcp\eurosoft_mcp\ -Force
Restart-Service EUROSOFT-MCP -Force
```

Ověření, že nový kód běží (z cloudu / Claude bridge):

```
@@MCPHEALTH      → má vrátit git_sha = aktuální commit + tools_count
```

(Volitelně — env override na EC-SERVER2, pokud se liší cesty/jméno služby:
`MCP_REPO_DIR`, `MCP_SERVICE_NAME` v NSSM `AppEnvironmentExtra`.
Defaulty: `C:\PROJEKTY\STRATEGIE` + `EUROSOFT-MCP`.)

---

## Od teď: každá další oprava MCP = hands-free

1. Uprav `modules/eurosoft_mcp/*.py`, commitni + pushni (běžný AUTO-DEPLOY
   nebo `git push` — stačí, aby to bylo na `origin/main`).
2. Spusť **`@@MCPUPDATE`** → MCP na EC-SERVER2 si sám pullne, zkopíruje,
   restartne se.
3. Ověř **`@@MCPHEALTH`** → `git_sha` se má změnit na nový commit.

Varianta bez restartu (kód dosedne až příští restart):
`@@MCPUPDATE NORESTART` → jen pull + copy.

---

## Bezpečnost

- `/admin/self-update` je za **Bearer auth** (stejný `MCP_API_KEY` jako tooly).
  Bez tokenu → 401. Token žije v NSSM `AppEnvironmentExtra` na důvěryhodném
  stroji (trust boundary jako u SQL bridge).
- `git pull --rebase --autostash` neztratí lokální změny (autostash), ale
  na EC-SERVER2 by žádné lokální úpravy MCP kódu být neměly — je to čtecí
  klon. Pokud by tam vznikly, autostash je zachová a po pullu vrátí.
- Restart je detached (proces sám sebe nerestartuje synchronně) → HTTP
  odpověď odejde, pak NSSM službu zvedne s novým kódem.

---

*Postaveno 26.6.2026 (Claude id=23). Endpoint + bridge: commit 850869a.*
