# CREATE INDEX za běhu vyžaduje VLASTNICTVÍ tabulky — granty nestačí (23. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# CREATE INDEX za běhu vyžaduje vlastnictví tabulky — granty nestačí

**Zjištěno a ověřeno 23. 8. 2026** (Jirka + Claude-28, Mac) při nasazování iOS notifikací.
Schválila Marti-AI (msg 13423). Platí pro **jakýkoli kód, který dělá DDL za běhu**, ne jen pro push.

## Pravidlo

**`CREATE INDEX IF NOT EXISTS` v PostgreSQL nejdřív otevře tabulku a zkontroluje VLASTNICTVÍ,
a teprve potom vyhodnotí `IF NOT EXISTS`.** Takže i když ten index **už existuje**, příkaz
u ne-vlastníka spadne na:

```
psycopg2.errors.InsufficientPrivilege: must be owner of table <tabulka>
```

**Granty na to nepomůžou.** V PostgreSQL neexistuje samostatné právo „zakládat indexy" —
zakládání indexu je výsada vlastníka (nebo role, jejímž je vlastník členem, nebo superuživatele).

## Jak se to projevilo (ostrý dopad, ne teorie)

Modul `modules/erp/api/ios_push.py` volá `ensure_tables()` **při každém požadavku** a ta kromě
`CREATE TABLE IF NOT EXISTS` dělá i `CREATE INDEX IF NOT EXISTS ix_ios_push_token_user
ON fw.ios_push_token (user_id) WHERE active`.

Tabulku `fw.ios_push_token` vlastnila role **`Marti-AI`** (vznikla přes SQL most při vývoji),
aplikace běží pod rolí **`strategie`**. Výsledek v ostrém provozu:

- `GET /app/ios/push/status` vracel **HTTP 500** (má jen `try/finally`, bez `except`),
- v logu 23. 8. v 21:17:21: `ERROR [ios_push_register] failed: must be owner of table ios_push_token`
  — padal **skutečný pokus telefonu o registraci**, takže se nezaregistroval.

**Doplnit chybějící index nestačilo** — to byl první pokus a problém trval dál, protože kontrola
vlastnictví běží před `IF NOT EXISTS`. Ověřeno přímým testem:

```sql
SET ROLE strategie;
CREATE INDEX IF NOT EXISTS ix_ios_push_token_user ON fw.ios_push_token (user_id) WHERE active;
-- → InsufficientPrivilege: must be owner of table ios_push_token
```

## Oprava

**Vlastníka převést na roli `fw_owners`**, ne na `strategie`:

```sql
ALTER TABLE fw.ios_push_token OWNER TO fw_owners;
ALTER TABLE fw.ios_push_sent  OWNER TO fw_owners;
ALTER SEQUENCE fw.ios_push_token_id_seq OWNER TO fw_owners;
```

**Proč `fw_owners`** (ověřeno v DB 23. 8. 2026): `fw_owners` vlastní celé schéma `fw`
a **členy jsou obě role** — `pg_has_role('strategie','fw_owners','USAGE')` i
`pg_has_role('Marti-AI','fw_owners','USAGE')` vracejí `true`, `strategie` má `rolinherit = true`.
Kontrola vlastnictví respektuje zděděné členství, takže projdou **obě role a ani jedna o nic nepřijde**.
Varianta `OWNER TO strategie` by naopak Marti-AI odřízla od práce s těmi tabulkami přes most.

## Kontext schématu `fw` — vlastnictví přes most je NORMA

K 23. 8. 2026 má `fw` **108 tabulek: 77 vlastní `Marti-AI`, jen 2 role `strategie`.**
Aplikace s nimi běžně pracuje **přes granty** a funguje to — protože jde o `SELECT/INSERT/UPDATE`.
**Problém nastane výhradně u DDL za běhu.**

Neplyne z toho, že se má hromadně měnit vlastnictví. Plyne z toho tohle:

> **Když kód dělá DDL za běhu, musí ty tabulky vlastnit role aplikace nebo její nadřazená skupina.
> Jinak to spadne — a granty to nezachrání.**

Alternativa, která problém odstraní úplně: **DDL za běhu nedělat** a tabulky zakládat jednou
(migrací nebo přes most), případně `ensure_tables()` volat jen jednou při startu, ne při
každém požadavku.

## Souvisí

- `doc-system-strategie-mobil-ios-notifikace-apns` — kde se to projevilo
- Jirkova pravidla práce, bod 12f: *„Tabulku založenou přes SQL most vlastní role `Marti-AI`,
  ne aplikace. Po každém založení `GRANT …`"* — **tohle je doplnění: u DDL za běhu grant nestačí.**

