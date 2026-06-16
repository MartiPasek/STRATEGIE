# API D — handoff pro Kristý + Claude-24 (16. 6. 2026)

API D = izolovaná **testovací instance** na obnovené záloze. Postaveno 16.6. (Claude-23).
Slouží k testování na nezivych datech + k **obnově ztracených věcí** (např. omylem
přegenerované jádro). Marti nechal dotažení Kristý + C24.

## Co běží
- **Instance**: NSSM `STRATEGIE-API-D` na **.11**, port **8004**, poetry venv (jako prod).
  AppDirectory `C:\Projekty\STRATEGIE-apid` (kopie kódu). DEMAND start.
- **DB**: `data_db_test` na **.12** (PostgreSQL 16). Obnovuje se z denních záloh
  `E:\STRATEGIE\<datum>\data_db_030003.dump` přes `pg_restore`.
- **Pojistka**: env `STRATEGIE_ENV=apid` + `STRATEGIE_READONLY_OUTBOUND=1`
  (v NSSM AppEnvironmentExtra) → kód blokuje odchozí MCP zápis do Centrály,
  reálné maily i SMS. Test data NEMOHOU ven. (Guard v `eurosoft_mcp_client.call_tool_sync`,
  `email_service.send_email_or_raise`, `sms_service.queue_sms`.)
- **Routing**: Caddy `C:\caddy\Caddyfile` — (a) `handle_path /apid/*` → 8004 (přímý přístup),
  (b) cookie `strategie_env=apid` → VEŠKERY provoz na 8004 (plná izolace).
- **UI indikátor**: `/api/v1/api-info` hlásí `env`/`db`/`apid` → ERP pill „🧪 TEST · data_db_test"
  + žlutý pruh nahoře. Přepínač v patičce u výběru verzí (jen rodiče): cookie set/delete.
- **Restore z appky**: dlaždice Nastavení → STRATEGIE nástroje → Obnova DB do API D
  (`fw.apid_restore_req` → watcher `STRATEGIE-APID-WATCHER` na .12 → pg_restore + ověření).

## GOTCHA — granty po každé obnově (DŮLEŽITÉ)
`pg_restore` vytvoří tabulky bez práv pro roli `strategie` → API D padá na
`permission denied for table users` → `is_marti_parent` vrací False → 403 v ERP.
**Po každé obnově spustit na .12** (soubor `C:\Scripts\apid_grants.sql` už existuje):
```
GRANT na schema public + fw/tenant/tenant_group/"user" pro strategie (SELECT/INSERT/UPDATE/DELETE + USAGE + sequences).
```
**TODO (nechané vám):** přidat tento GRANT blok na konec `apid_watcher.ps1` (po pg_restore),
aby se práva nastavila automaticky.

## Obnova jádra 72 (původní důvod — pro Kristý)
Záloha 15.06 03:00 obsahuje jádro 72 **před** rozbitím (Kristý/C24 ho 15.6. omylem
přegenerovali). Postup:
1. V `data_db_test` přečíst řádky jádra 72: `fw.core`, `fw.comp_def` (WHERE core_id=72),
   `fw.data_source` + `fw.data_source_op` navázané na ds jádra 72.
2. Porovnat s aktuálním (rozbitým) stavem v ostré `data_db`.
3. Vrátit přes **approval banner** (bridge write) — INSERT/UPDATE chybějících comp_def
   řádků (root=1 pro form, parent pro děti; core_id dědí trigger).

## Re-sync kódu API D (po prod deployi)
API D má vlastní kopii kódu. Po prod deployi:
`robocopy C:\Projekty\STRATEGIE C:\Projekty\STRATEGIE-apid /MIR /XD .git .venv ... ` + restart služby.
DB (`data_db_test`) zůstává. **TODO:** zvážit auto-resync v deploy watcheru.
