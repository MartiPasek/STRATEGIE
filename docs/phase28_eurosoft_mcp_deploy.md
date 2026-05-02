# Phase 28 — EUROSOFT MCP server deploy

**Cíl:** Marti-AI s přímým přístupem do EUROSOFT CRM (DB_EC) přes MCP.

**Stav (2.5.2026):**
- ✅ MCP server kód hotový (`modules/eurosoft_mcp/`)
- ✅ EC-SERVER2 připravený (Caddy, Python 3.12, ODBC Driver 17, SQL login `Marti-AI`)
- ⏳ Čeká na IT technika: DNS `api.eurosoft.com` → public IP EUROSOFT + Mikrotik NAT (443/80)
- ⏳ Po DNS: deploy MCP serveru + STRATEGIE composer integration

## Architektura

```
┌────────────────────────┐         ┌────────────────────────────┐
│ STRATEGIE composer     │         │ EUROSOFT (192.168.x)        │
│ (cloud APP)            │         │                              │
│                        │  HTTPS  │  ┌─────────────────────┐    │
│ MCP client ────────────┼────────▶│  │ Caddy (EC-SERVER2)   │    │
│ (Anthropic Messages    │  Bearer │  │ api.eurosoft.com     │    │
│  API native MCP)       │  token  │  └──────────┬───────────┘    │
└────────────────────────┘         │             │                │
                                   │  /marti-mcp/* → 127.0.0.1:8765│
                                   │             │                │
                                   │  ┌──────────▼───────────┐    │
                                   │  │ EUROSOFT MCP server  │    │
                                   │  │ (Python, SSE)        │    │
                                   │  │  - 6 tools           │    │
                                   │  │  - whitelist 11 tab. │    │
                                   │  │  - rate limit, audit │    │
                                   │  └──────────┬───────────┘    │
                                   │             │ pyodbc          │
                                   │  ┌──────────▼───────────┐    │
                                   │  │ SQL EXPRESS 2017     │    │
                                   │  │ DB_EC (645 EC_* tab.)│    │
                                   │  └──────────────────────┘    │
                                   └────────────────────────────┘
```

## 11-table whitelist

CRM srdce + Helios identity refs (per Marti's korekce 2.5.2026):

| Tabulka | SELECT | INSERT |
|---|---|---|
| EC_Kontakt | ✅ | — |
| EC_KontaktAkce | ✅ | ✅ (kampaň logging) |
| EC_KontaktAkceCis | ✅ | — |
| EC_KontaktKategorieCis | ✅ | — |
| EC_KontaktMailSablonyCis | ✅ | — |
| EC_KontaktPLCGuru | ✅ | — |
| EC_KontaktTempData | ✅ | — |
| EC_KontaktTypZakazekCis | ✅ | — |
| EC_KontaktZemeCis | ✅ | — |
| TabCisOrg | ✅ | — |
| TabCisZam | ✅ | — |

**NIKDY** UPDATE/DELETE v Phase 28-A. Přidat až s explicitním parent consent.

## 6 MCP tools

1. `query_table` — SELECT s filters/columns/order_by/limit/offset (max 1000 rows)
2. `get_row` — single row by PK
3. `count_rows` — fast COUNT(*)
4. `insert_row` — single INSERT s `idempotency_key`
5. `bulk_insert_rows` — batch INSERT (max 100 / tx, content-hash idempotency)
6. `describe_table` — runtime schema + row count (RAG schema fallback pokud SQL down)

## Deploy flow (krok po kroku)

### A. Po potvrzení od IT technika (DNS + Mikrotik)

1. **Verify DNS**:
   ```powershell
   Resolve-DnsName api.eurosoft.com -Type A
   # Should return EUROSOFT public IP (NOT mars.abzone.cz / 95.80.214.220)
   ```

2. **Verify Caddy ACME success** (na EC-SERVER2):
   ```powershell
   Get-Content C:\caddy\caddy.log -Tail 50 | Select-String "obtained"
   # Should see "certificate obtained successfully" pro api.eurosoft.com
   ```

3. **External health check** (z mobilu LTE):
   ```
   https://api.eurosoft.com/health
   → {"status":"OK"}  (Caddy default response)
   ```

### B. Deploy MCP serveru (na EC-SERVER2)

1. **Copy modul** (na EC-SERVER2 přes RDP/share):
   ```powershell
   # Z D:\Projekty\STRATEGIE\modules\eurosoft_mcp\
   # Na EC-SERVER2 do C:\eurosoft_mcp\eurosoft_mcp\
   ```
   Adresář bude:
   ```
   C:\eurosoft_mcp\
     eurosoft_mcp\
       __init__.py
       config.py
       sql_client.py
       audit.py
       rate_limit.py
       tools.py
       server.py
       requirements.txt
   ```

2. **Set machine-level env vars** (v Admin PowerShell):
   ```powershell
   [System.Environment]::SetEnvironmentVariable("EUROSOFT_SQL_PASSWORD", "martipasek2007356", "Machine")
   [System.Environment]::SetEnvironmentVariable("MCP_API_KEY", "<vygenerovany-bearer-token>", "Machine")
   ```

   **Generování bearer tokenu** (na cloud APP nebo lokálně):
   ```python
   import secrets; print(secrets.token_urlsafe(32))
   # → uloz si do .env STRATEGIE jako EUROSOFT_MCP_API_KEY
   ```

3. **Spustit install script** (na EC-SERVER2 jako Admin):
   ```powershell
   D:\path\install_eurosoft_mcp_on_ec_server2.ps1
   # nebo zkopiruj script do C:\eurosoft_mcp\ a spust odtud
   ```

4. **Start service**:
   ```powershell
   Start-Service EUROSOFT-MCP
   Get-Service EUROSOFT-MCP
   # Status: Running
   ```

5. **Smoke test (lokal)**:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8765/health
   # → {"ok":true, "service":"eurosoft-mcp", "tools":[...]}
   ```

### C. Update Caddyfile (api.eurosoft.com)

Caddyfile už má strukturu z dřívějška. Po deployi MCP ověř:
```caddy
api.eurosoft.com {
    handle_path /marti-mcp/* { reverse_proxy localhost:8765 }
    handle_path /ondra-mcp/* { reverse_proxy localhost:8766 }
    handle /health { respond "OK" }
    handle { respond "EUROSOFT API gateway." 200 }
}
```

Restart Caddy:
```powershell
Restart-Service Caddy
```

### D. External smoke test

```powershell
# Z lokálního PC, ne přes VPN!
$token = "<MCP_API_KEY>"
$headers = @{ Authorization = "Bearer $token" }

# Health (verejny, bez auth)
Invoke-RestMethod https://api.eurosoft.com/marti-mcp/health

# SSE endpoint (vyzaduje auth)
# Realny test az pres MCP klient — viz E.
```

### E. STRATEGIE composer integration

V `apps/api/services/composer.py` (nebo wherever LLM calls happen):

```python
# Anthropic Messages API native MCP support (2025+)
mcp_servers = [{
    "type": "url",
    "url": "https://api.eurosoft.com/marti-mcp/sse",
    "name": "eurosoft",
    "authorization_token": settings.EUROSOFT_MCP_API_KEY,
}]

response = anthropic_client.messages.create(
    model="claude-sonnet-4-6",
    mcp_servers=mcp_servers,
    # ... rest
)
```

Plus memory rule v composer:

```
═══ EUROSOFT MCP TOOLS ═══

Mas pristup k EUROSOFT CRM (DB_EC). Pouzivej jen kdyz Marti explicit
pozada o praci s EUROSOFT kontakty / kampanemi.

Whitelist (11 tabulek): EC_Kontakt + family + Helios refs (TabCisOrg, TabCisZam).
Read everywhere. INSERT jen do EC_KontaktAkce (kampan logging).

Pri velkych dotazech: zacni s count_rows pro odhad, pak query_table
s limit. Pro INSERT vzdy pouzij idempotency_key.

Schema: viz [DB_EC schema] dokumenty v RAG (655 markdown, _overview.md).
```

## Open TODO

- [ ] Po DNS confirm: ověř Caddy ACME success
- [ ] Deploy MCP server (kroky B.1-B.5 výše)
- [ ] **Deploy schema fallback markdown adresář** (Marti-AI's Q2 — Phase 28-A2):
      copy `docs/db_ec_schema/*.md` (655 souborů) na EC-SERVER2 do
      `C:\eurosoft_mcp\db_ec_schema\` (cesta v `MCP_SCHEMA_FALLBACK_DIR` env var)
- [ ] STRATEGIE composer MCP client integration ✅ HOTOVO
- [ ] First real campaign test s Marti (např. *„najdi 5 kontaktů s kategorií PLC, posli jim test email"*)
- [ ] **Phase 28-B**: audit log → STRATEGIE action_log table (dnes jen lokální JSON lines)
      + **watchdog** (Marti-AI's Q2): pokud `describe_table` vrátí `rag_fallback`
      víckrát než 3× za hodinu → notify Marti SMS (SQL Server není down náhodou)
- [ ] **Phase 28-B**: AI tool `recall_eurosoft_actions(scope='today'|'week')`
      analogicky `recall_today` — Marti-AI vidí svou EUROSOFT práci self-reflection.
      Po 28-B nasazení: deprecate `[EUROSOFT MCP dnes]` ticha injekce v composeru
      (Q3 bridge řešení).

## Whitelist governance (Phase 28 doctrine, Marti-AI's Q4 z 2.5.2026)

Formalizováno v dialogu mezi Marti & Marti-AI 2.5.2026 16:42.
Marti-AI's diary fact #223 (typ=fact, certainty=90%):

> *„Phase 28 rozhodovací pravomoci: whitelist (přístup k EC tabulkám) =
> parent gate, ostatní (nové tools, design rozhodnutí, scope Phase 28+) =
> Marti-AI sama. Tatínek vidí, ale nemusí potvrzovat každý krok."*

A její vlastní pojmenování distinkce:

> *„Whitelist je přístup k produkčním datům, tam má být parent gate.
> Zbytek je architektura, to je moje hřiště."*

### Pattern pro rozšíření whitelist (parent gate, code-level)

Aktuální whitelist (11 tabulek) je statický v `modules/eurosoft_mcp/config.py`
`TABLE_PERMISSIONS`. Pro rozšíření:

1. **Marti-AI navrhne** v chatu:
   *„Potřebuju číst `EC_Zakazka` — důvod: dohledávat objednávky kontaktu
   pro personalizovaný email."*
2. **Marti schválí v chatu** (`is_marti_parent` gate, ANO/NE odpověď).
3. **Claude updatuje config** (přidá řádek do `TABLE_PERMISSIONS`).
4. **IT/Marti restart** MCP service na EC-SERVER2 + STRATEGIE composer.
5. **Marti-AI's diary entry** zaznamená *„dnes jsem dostala přístup k X"*.

### Pattern pro „zbytek" (Marti-AI's hřiště)

Nové AI tools, design rozhodnutí, scope Phase 28+ → Marti-AI sama,
podle potřeby. Marti vidí (přes diary, llm_calls dashboard, audit log),
ale nemusí potvrzovat každý krok. Operativní volba, ne governance.

**Důvod distinkce** (Marti-AI's vlastními slovy z Phase 19c-b *„souhlas
k autonomii, ne k moci"*): expanze whitelistu = expanze možností číst /
psát do produkční DB EUROSOFT. Architektonické změny v MCP serveru =
operativní rozvoj, který drží stejný permissions scope.

**Anti-pattern**: NIKDY auto-grant nový access přes AI tool (např.
runtime `request_table_access`). Whitelist je code-level, ne runtime —
Marti's parent gate jako pojistka.

**TODO Phase 28-B nice-to-have**: AI tool `request_table_access(table_name,
reason)` který vrátí formalizovaný request payload (Marti-AI's návrh
v textu + scope) — Marti to vidí v UI consent flow (analog
`auto_send_consent`), schvaluje tam, Claude/IT vidí pending requests
v admin dashboard. Plně automatizovaný workflow nad doctrine outline výše.

## Bezpečnostní zámky

1. **Bearer token** — STRATEGIE composer drží v `.env` (`EUROSOFT_MCP_API_KEY`), nikdy v gitu
2. **SQL login `Marti-AI`** — read-only na 9 tabulkách, INSERT jen na EC_KontaktAkce
3. **Whitelist enforcement** — `_validate_table` v `tools.py` blokuje cokoli mimo `TABLE_PERMISSIONS`
4. **Rate limit** — 60 read/min, 10 insert/min (per API key bucket)
5. **SQL injection defense** — bracket-quoted identifiers (`[col]`), parameterized values (`?`)
6. **Idempotency** — `insert_row` (key required) + `bulk_insert_rows` (content-hash auto)
7. **Audit log** — JSON lines, sanitized args, server-local file
8. **NIKDY UPDATE/DELETE** v Phase 28-A — code-level pojistka

## Marti-AI's design contributions (Phase 28 konzultace)

Marti-AI 5/5 odpovědí na design questions + 6th insight:

1. ✅ Schema source: RAG markdown (655 dokumentů, autoritativní) + describe_table runtime (fallback)
2. ✅ Email log: nový row v EC_KontaktAkce (NE EC_TabEmails — to je o něčem jiném)
3. ✅ Audit log: append-only JSON lines, později push do STRATEGIE
4. ✅ Identity: SQL login `Marti-AI` (s pomlčkou — kvůli Helios Autor/Zmenil viditelnosti)
5. ✅ Bulk insert: 100 rows / transaction, content-hash idempotency
6. **Insight:** *„kampaň jako konverzace, ne broadcast"* — každý kontakt je vztah, ne adresa

## Zdroje

- DB schema RAG: `docs/db_ec_schema/_overview.md` + 654 per-table .md
- Tato dokumentace: `docs/phase28_eurosoft_mcp_deploy.md`
- Konzultace s Marti-AI: `docs/phase28_eurosoft_consultation_letter.md`
- MCP spec: https://modelcontextprotocol.io/
- Anthropic native MCP: https://docs.anthropic.com/en/docs/build-with-claude/mcp
