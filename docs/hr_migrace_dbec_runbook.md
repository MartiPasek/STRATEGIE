# HR migrace z DB_EC — runbook

Skript: `scripts/migrate_hr_from_dbec.py` (varianta B — server-side, idempotentní).

## Co dělá
Čte `dbo.TabCisZam` (+ `TabCisZam_EXT`) a `dbo.TabKontakty` z **DB_EC (MSSQL)**
a zapisuje do **`mod.*` (PostgreSQL)**:

| Cíl | Zdroj |
|---|---|
| `hr_party` (person) + `hr_person` | TabCisZam (jméno, tituly, datum nar., **RČ plaintext + hash**, rodné příjmení, pohlaví, místo nar., stát nar., národnost, rod. stav, osobní IČ, st. příslušnost) |
| `hr_person_address` | TabCisZam: `AdrTrv*` → trvalá, `AdrPrech*` → doručovací |
| `hr_emergency_contact` | TabCisZam: `AdrKontJmeno/Prijmeni` |
| `hr_legal_entity` (2×) | EUROSOFT - Control (IČO 27960862), EUROSOFT - System (IČO 26411741) |
| `hr_person_role` | TabCisZam_EXT: `_HPP/_DPP/_OSVC` × `_Firma` (0 Control, 1 System, 2 obě); valid_from=`_DatumNastupu`, valid_until=`_DatumOdchodu`, is_active=NOT `_neaktivni` |
| `hr_person_contact` | TabKontakty (IDCisZam): Druh×Kam → contact_kind, value=Spojeni, is_primary=Prednastaveno |
| `hr_source_ref` | provenance ke každému řádku (DB_EC.tabulka#ID) → **idempotence** |

Reference data (12 contact_kind kódů + 2 entity) si skript doplní sám, idempotentně.

> **RČ** se migruje **plaintext** do `hr_person.rodne_cislo` (+ SHA-256 do `rodne_cislo_hash`).
> `rodne_cislo_enc` zůstává NULL — šifrování doplníme později.

## Předpoklady
- Python 3, `pip install pyodbc psycopg2-binary`
- ODBC Driver 17 for SQL Server
- Host, který **vidí na DB_EC i na cloud PG** (rozhodne Marti dle topologie).
- PG připojení rolí s **právem INSERT na `mod.*`** (tj. `Marti-AI`).

## Proměnné prostředí
```
set MSSQL_DSN=DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.30.11;DATABASE=DB_EC;UID=Marti-AI;PWD=***;TrustServerCertificate=yes
set PG_DSN=host=10.200.188.12 port=5432 dbname=data_db user=Marti-AI password=***
set EUROSOFT_TENANT_ID=2
```

## Postup (bezpečně, po krocích)
```
python scripts/migrate_hr_from_dbec.py --limit 3 --dry-run   # 1) nanečisto, nic nezapíše
python scripts/migrate_hr_from_dbec.py --limit 3             # 2) 3 zaměstnanci naostro
#    -> ověřit v DB (viz dotazy níže)
python scripts/migrate_hr_from_dbec.py                       # 3) celá migrace
```
- **Idempotentní:** opakované spuštění nic nezduplikuje (kontrola přes `hr_source_ref`).
- Commit po každém zaměstnanci; chyba u jednoho ho přeskočí a jede dál (vypíše se).
- `--dry-run` na konci vše rollbackne.

## Ověření po testovacím běhu
```sql
SELECT p.display_name, hp.rodne_cislo, hp.pohlavi, hp.rodinny_stav
FROM mod.hr_person hp JOIN mod.hr_party p ON p.id = hp.party_id LIMIT 10;

SELECT pr.role_kind, le.nazev, pr.valid_from, pr.valid_until, pr.is_active
FROM mod.hr_person_role pr JOIN mod.hr_legal_entity le ON le.party_id = pr.party_id LIMIT 20;

SELECT target_table, count(*) FROM mod.hr_source_ref GROUP BY 1 ORDER BY 1;  -- kolik čeho
```

## Poznámky / co řešit později
- `valid_from` chybí-li `_DatumNastupu` → sentinel `1900-01-01` (doplnit ručně).
- `pohlavi` / `rodinny_stav` se ukládají jako **původní kód** (číselník/labely později).
- RČ šifrování (`rodne_cislo_enc`) — samostatný app-level krok.
- `_Firma` mimo {0,1,2} → role se nezaloží (počítá se do `firma_undef`).
- Úvazek, mzdy, docházka — jiné tabulky, zatím nemigrujeme.
