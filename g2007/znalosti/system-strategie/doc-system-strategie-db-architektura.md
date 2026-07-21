# Databáze STRATEGIE — data_db, schémata, DB_EC/DB_ST, GRANTy

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Databáze (aktualizováno 9. 5. 2026)

**Single PostgreSQL database `data_db`** (Phase 18 consolidation 29. 4.):
- Před Phase 18: `css_db` (core) + `data_db` (operational) — dvě DB, cross-DB
  joiny nešly, FK constraints nešly.
- Po Phase 18: vše v `data_db`. css_db deprecated/dropped. Hybrid alias
  strategy v `modules/` (BaseCore = Base, get_core_session = get_session).
- Backup: jen `data_db` (Phase 18 + 25/38.4 default `C:\Backup` na cloud APP).

**Pak (Phase 35-E.1, 8. 5.):** Marti-AI má vlastní role `"Marti-AI"` na
PostgreSQL cloud SQL (10.200.188.12) s 4 schémata `AUTHORIZATION "Marti-AI"`:
- `master.*` — system framework (entity_def, framework_jadro, framework_komponenta,
  framework_property, komponenta_typ, menu_node, data_set, data_source,
  data_source_operation)
- `tenant_group.*` — sdílené per group (EUROSOFT + INTERSOFT spolu)
- `tenant.*` — per-firma data
- `"user".*` — per-user identity (diář, kotvy, osobní config) — 4. vrstva
  od Marti-AI

Strategie user (API process) má GRANT USAGE/SELECT/EXECUTE na master/
tenant_group/tenant/user schémata + ALTER DEFAULT PRIVILEGES FOR ROLE "Marti-AI"
pro budoucí tabulky.

**MSSQL legacy** (EC-SERVER2 192.168.30.11):
- `DB_EC` — Centrála 1 EUROSOFT, read-only přes EUROSOFT-MCP server (cloud
  APP composer-side klient od Phase 28-C). 11-table whitelist (kontakty,
  zakázky, akce, číselníky). Pozn.: CRM write od 31.5. přes MCP insert/update
  (master-detail CRM_Kontakt + CRM_Kontakt_Akce IDakce=16).
- `DB_ST` — Marti-AI's owned doména (db_owner role) na MSSQL. První DDL
  akt = `master.entity_def` (12. dárek-scéna 8.5. odp.). Sandbox pro
  non-framework práci.
- **Long-term endgame** (Marti's vize 8.5. ráno): single PostgreSQL framework,
  MSSQL DB_EC migruje postupně per-jádro do PostgreSQL master.*. DB_ST
  zůstane jako MSSQL sandbox.

