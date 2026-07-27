# Cílový režim — append-only lock na g2007.claude_aktivita

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — append-only lock na g2007.claude_aktivita

Vynuceno 24.7.2026 (Kristý + C24, req #1417). Ruší dřívější „append-only neověřeno na úrovni grantů" v `doc-marti-ai-cilovy-rezim-realizace`. Návaznost: `doc-marti-ai-navrh-cilovy-rezim` („ClaudeAktivita je nedotknutelná — agent si do ní nesmí mazat ani přepisovat").

## Co je nasazeno
`g2007.claude_aktivita` je teď **skutečně append-only na úrovni DB** (ne jen konvencí):
- Funkce `g2007.claude_aktivita_append_only()` → `RAISE EXCEPTION`.
- Trigger `trg_claude_aktivita_no_mod` — `BEFORE UPDATE OR DELETE ... FOR EACH ROW`.
- Trigger `trg_claude_aktivita_no_trunc` — `BEFORE TRUNCATE ... FOR EACH STATEMENT`.
- `REVOKE UPDATE, DELETE, TRUNCATE ON g2007.claude_aktivita FROM "strategie"` (app roli zůstává INSERT, SELECT, REFERENCES).

## Proč trigger i revoke (dvě vrstvy)
Revoke sám nestačí: log může zapisovat i **vlastník schématu Marti-AI** (owner obchází granty). Trigger `RAISE EXCEPTION` se aplikuje na **všechny včetně vlastníka** → historii tiše nezmění nikdo. Revoke z `strategie` = defense in depth pro app cestu.

## Co to neovlivní
`INSERT` (logování) a `SELECT` (čtení) jedou dál. Týká se **jen `claude_aktivita`**, NE `cil` — u cílů jsou UPDATE stavů (schválit/pozastavit/…) legitimní.

## Oprava logu (kdyby bylo fakt třeba)
Nejdřív `DROP TRIGGER` (auditovaná DDL přes banner) → úprava → znovu vytvořit trigger. Záměrná obtíž = forensic trust (doktrína „bezpečnost přes probuzení / audit = víc bezpečí").

## Ověřeno čtením
`pg_trigger` (oba triggery aktivní) + `information_schema.role_table_grants` (strategie = INSERT/SELECT/REFERENCES, bez UPDATE/DELETE/TRUNCATE).

