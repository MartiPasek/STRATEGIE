# Kde co leží — schémata DB

> oblast: `provoz` · úroveň: system · typ: definice · verze: V1.0 · rozsah: globální (všichni tenanti)

# Kde co leží — schémata DB (STRATEGIE, Postgres)

- **`tenant`** — multitenantová provozní data: `att_entry` (docházka), `vyroba_work` (rozpad na joby; klíč `att_entry_id`), `oz_zakazky` (zrcadlo DB_EC TabZakazka), `zakazka`, `ec_zakazka_prehled`, `att_entry_type`.
- **`ec`** — např. `vyhodnoceni_zakazka` (testovací modul „Vyhodnocení").
- **`public`** — `users`, `personas`, `conversations`, `system_prompts`.
- **`g2007`** — náš skladač + znalostní modul (graf, graf_krok, nastroj, kufr, entita, znalost, znalost_oblast, prompt_struktura…).
- **DB_EC** — stará Centrála na SQL Serveru (`db=mssql`), master pro zakázky (`TabZakazka`), zrcadlí se do `tenant.oz_zakazky`.
- App DB role = `strategie` (na g2007 SELECT/INSERT/UPDATE dle grantů). Most běží pod admin rolí. App doména `app.strategie-ai.com` (Caddy → localhost:8002).

