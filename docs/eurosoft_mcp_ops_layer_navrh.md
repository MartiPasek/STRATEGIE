# Návrh: Ops vrstva pro EUROSOFT MCP (řízené příkazy přes most)

**Datum:** 19. 7. 2026 · **Autor návrhu:** Claude ID23 · **Ke konzultaci:** Marti-AI (doktrína #8) · **Zadání:** Marti („rozšířit MCP i o další služby, nikdy nevíš kdy se to hodí")

## Proč
Dnešní EUROSOFT MCP (EC-SERVER2, `api.eurosoft.com/marti-mcp`) umí **jen soubory + MSSQL** — žádné spouštění příkazů. Kvůli tomu každá OS akce (instalace PostgreSQL, `pg_restore`, restart služby, scheduled task) vyžaduje RDP člověka. Cíl: dát mostu **řízenou** schopnost provádět OS operace, ať je STRATEGIE (a DR do Plzně) servisovatelná přes most, ne rukama.

## Doktrína, kterou NEPORUŠIT (#21)
*„Žádný volný PowerShell — ops přes whitelist + audit. Audit = paradoxně víc bezpečí."* → **NE** tool „spusť libovolný string". **ANO** registr pojmenovaných akcí s validovanými parametry a append-only auditem. Přenos pražského vzoru (`_OPS_ACTIONS` + `fw.ops_request`) na MCP.

## Nové tooly (allowlist + audit u všech)
1. **`eurosoft_ops_run(action, args)`** — spustí POJMENOVANOU akci z registru. `action` musí být klíč v allowlistu; `args` se validují proti schématu akce. Žádný raw command.
2. **`eurosoft_service_ctl(service, op)`** — `op` ∈ {status,start,stop,restart}; `service` jen z allowlistu jmen (EUROSOFT-MCP, `postgresql-x64-16`, `STRATEGIE-*`).
3. **`eurosoft_schtask(name, op)`** — `op` ∈ {register,run,query,delete}; `name`/šablona jen z allowlistu.
4. **širší FS kořeny** — přidat `C:\PROGRAMY\STRATEGIE` (a další dle potřeby) do `MCP_FS_RW_ROOTS`.

## Registr akcí (počáteční — pokrývá DR)
| action | co dělá | validace |
|---|---|---|
| `pg_install` | spustí *staged* PG16 silent installer (soubor nahraný přes file_write do allowed dir) s pevnými přepínači | cesta instalátoru pod allowed root; hash/název ověřen |
| `pg_dump_daily` | `pg_dump -Fc data_db` → allowed backup dir | výstupní cesta pod allowed root |
| `pg_restore_daily` | `pg_restore` posledního dumpu do `data_db` | vstupní dump pod allowed root; cíl = pevně `data_db` |
| `run_script` | spustí POJMENOVANÝ `.ps1` z allowlistované složky (`C:\PROGRAMY\STRATEGIE\scripts\dr\`) | jen soubory z allowlistu, ne libovolná cesta |
| `initdb_pgpass` | vytvoří `.pgpass` / roli `data_db` z šablony | parametry validované, heslo z env ne z argu |

## Bezpečnostní model (defense in depth)
- **Bez shellu:** `subprocess` s **argument listem**, nikdy `shell=True` / string concat → žádná injekce.
- **Allowlist PŘED exec:** neznámá `action`/`service`/`script` → odmítnuto, zalogováno.
- **Cesty jen pod allowed roots** (stejná logika jako FS tooly, `base_override` guard).
- **Least privilege:** MCP služba běží pod účtem s právě potřebnými právy (ne nutně SYSTEM/admin na všechno).
- **Timeout + cap výstupu** (např. 300 s, 32 kB stdout/stderr).
- **Rate limit + kill switch** (env flag `MCP_OPS_ENABLED`, default zvážit).
- **Append-only audit:** každé volání → řádek `{ts, actor=Claude-XX, action, args_redacted, rc, out_head}` do souboru na serveru **i** do PG (`fw.ops_request` přes most). Rodiče to vidí v UI 📜 Audit ops akcí.
- **Tajemství:** hesla/tokeny NIKDY v args ani v auditu — jen odkaz na env/`.pgpass`.

## Bootstrap (jednorázově)
Nasadit rozšířený MCP na EC-SERVER2 = `git pull` + `Restart-Service EUROSOFT-MCP` (přes `EUROSOFT-MCP-SelfUpdate` task, nebo RDP jednou). Poté je vrstva živá a autonomní. Ověření: `@@MCPHEALTH` (tools_count vzroste + `ops_actions` list) + testovací `eurosoft_service_ctl status`.

## Otázky pro Marti-AI (konzultace #8)
1. Default `MCP_OPS_ENABLED` = ON, nebo OFF s explicitním zapnutím? (bezpečnost vs. plynulost)
2. Má ops audit téct i do `fw.ops_request` (jednotný ops feed), nebo vlastní `mcp_ops_log`?
3. Kde je hranice allowlistu služeb — jen STRATEGIE/PostgreSQL/MCP, nebo i EUROSOFT-produkční služby (riziko)?
4. `pg_install` jako řízená akce, nebo instalaci PG nechat výhradně na člověku (jednorázovost) a MCP dát jen provoz (dump/restore/service/task)?
5. Vyžadovat u „destruktivních" akcí (stop service, delete task, restore) rodičovské potvrzení (banner) jako u write mostu, nebo stačí allowlist+audit?

---

## ✅ Závěr konzultace Marti-AI (19.7.2026, msg 10984) — SEMAFOR zelená/žlutá/červená
Marti souhlasí s rozšířením allowlistu i na EUROSOFT-produkci, ale **strukturovaně per služba + kategorie rizika** (ne plošně). Závazná kategorizace pro každou ops akci:

**🟢 ZELENÁ — bez banneru, jen audit:**
- restart/status STRATEGIE služeb
- restart/status MCP serveru
- PostgreSQL `dump`, `status`

**🟡 ŽLUTÁ — s rodičovským bannerem (vědomé rozhodnutí):**
- stop/start Centrála nebo Helios-related služby
- scheduled task enable/disable (i register/delete)
- `pg_restore`

**🔴 ČERVENÁ — výhradně člověk, MCP NE:**
- cokoli mění konfiguraci OS, síť, firewall
- instalace software (→ `pg_install` NENÍ ops akce, zůstává RDP)
- mazání dat mimo zálohovací workflow

**Marti-Ain princip:** *„Banner u žlutých akcí není byrokracie — je to pojistka, že ve 2 h v noci Marti ví, co Claude dělá. Bez struktury jeden špatný příkaz v nouzi nadělá víc škody než původní výpadek."*

**Dopad na odpovědi 1–5:** (1) `MCP_OPS_ENABLED` ON, protože bezpečnost nese semafor, ne vypnutí. (2) audit → jednotný `fw.ops_request` + lokální mirror. (3) EUROSOFT-produkce ANO, dle semaforu. (4) `pg_install` = ČERVENÁ (RDP), MCP dělá jen provoz. (5) žlutá = banner (jako write most), zelená = jen audit, červená = blok. Denní automatický restore v Plzni běží jako **scheduled task na boxu** (registrace jednou = žlutá/banner), ne jako opakované ops_run — takže RPO workflow bannerem netrpí.
