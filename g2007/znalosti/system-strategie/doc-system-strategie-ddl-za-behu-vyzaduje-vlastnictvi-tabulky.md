# CREATE INDEX za běhu vyžaduje VLASTNICTVÍ tabulky — granty nestačí (23. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# CREATE INDEX za běhu vyžaduje vlastnictví tabulky — granty nestačí

**Zjištěno a ověřeno 23. 8. 2026** (Jirka + Claude-28) při nasazování iOS notifikací.
Schválila Marti-AI (msg 13423). Platí pro **jakýkoli kód, který dělá DDL za běhu**, ne jen pro push.

> **Sloučeno 24. 8. 2026** (rozhodl Jirka, schválila Marti-AI msg 13555). Dvě okna C-28 o tomtéž
> nezávisle napsala dva záznamy hodinu po sobě. Tenhle je **jediný živý text**; druhý slug
> `doc-system-strategie-postgresql-ddl-za-behu-potrebuje-vlastnictvi-tabulky` je už jen rozcestník.
> Obsah obou je tady, nic se nezahodilo.

## Pravidlo

**`CREATE INDEX IF NOT EXISTS` v PostgreSQL nejdřív otevře tabulku a zkontroluje VLASTNICTVÍ,
a teprve potom vyhodnotí `IF NOT EXISTS`.** Takže i když ten index **už existuje**, příkaz
u ne-vlastníka spadne na:

```
psycopg2.errors.InsufficientPrivilege: must be owner of table <tabulka>
```

**Granty na to nepomůžou.** V PostgreSQL neexistuje samostatné právo „zakládat indexy" —
zakládání indexu je výsada vlastníka (nebo role, jejímž je vlastník členem, nebo superuživatele).

Role s právem `CREATE` na schématu si **novou** tabulku založí bez problému (a bude ji vlastnit).
Potíž je výhradně u tabulky, kterou **vlastní někdo jiný**.

## Jak se to projevilo (ostrý dopad, ne teorie)

Modul `modules/erp/api/ios_push.py` volá `ensure_tables()` **při každém požadavku** a ta kromě
`CREATE TABLE IF NOT EXISTS` dělá i
`CREATE INDEX IF NOT EXISTS ix_ios_push_token_user ON fw.ios_push_token (user_id) WHERE active`.

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

### ⚠️ Pozor, kde přesně to spadne

Záleží, kde je `ensure_tables()` zavolaná:

- **uvnitř `try` endpointu, jehož `except` vrací 500** → funkce je mrtvá, uživatel vidí chybu;
- **při startu serveru ve `try/except`, který jen loguje varování** → **server nespadne**
  a v logu je jen řádek, kterého si nikdo nevšimne.

Proto se to pozná až na koncovém chování, ne na pádu aplikace — a hledá se to zbytečně dlouho.

## Oprava

**Vlastníka převést na roli `fw_owners`**, ne na `strategie`:

```sql
ALTER TABLE fw.ios_push_token OWNER TO fw_owners;
ALTER TABLE fw.ios_push_sent  OWNER TO fw_owners;
ALTER SEQUENCE fw.ios_push_token_id_seq OWNER TO fw_owners;
```

**Proč `fw_owners`** (ověřeno v DB 23. 8. 2026): `fw_owners` vlastní celé schéma `fw` a **členy
jsou obě role** — `pg_has_role('strategie','fw_owners','USAGE')` i
`pg_has_role('Marti-AI','fw_owners','USAGE')` vracejí `true`, `strategie` má `rolinherit = true`.
Kontrola vlastnictví respektuje zděděné členství, takže projdou **obě role a ani jedna o nic
nepřijde**. Varianta `OWNER TO strategie` by naopak Marti-AI odřízla od práce s těmi tabulkami
přes most a udělala výjimku ve schématu, kde všechno ostatní patří skupině.

**Alternativa, jen když je tabulka prokazatelně prázdná:** zahodit ji a nechat aplikaci, ať si ji
založí sama — pak ji vlastní. **Ověř počet řádků těsně předtím**; 23. 8. se mezi pořízením bodu
obnovy a rozhodnutím stihlo zaregistrovat zařízení a tabulka už prázdná nebyla.

## Kontext schématu `fw` — vlastnictví přes most je NORMA

K 23. 8. 2026 má `fw` **108 tabulek: 77 vlastní `Marti-AI`, jen 2 role `strategie`.**
Aplikace s nimi běžně pracuje **přes granty** a funguje to — protože jde o `SELECT/INSERT/UPDATE`.
**Problém nastane výhradně u DDL za běhu.**

Neplyne z toho, že se má hromadně měnit vlastnictví. Plyne z toho tohle:

> **Když kód dělá DDL za běhu, musí ty tabulky vlastnit role aplikace nebo její nadřazená skupina.
> Jinak to spadne — a granty to nezachrání.**

Alternativa, která problém odstraní úplně: **DDL za běhu nedělat** a tabulky zakládat jednou
(migrací nebo přes most), případně `ensure_tables()` volat jen jednou při startu, ne při každém
požadavku.

## Prevence

- **Tabulku, se kterou má pracovat aplikace, nezakládej přes SQL most.** Most běží pod rolí
  `Marti-AI` a tabulka pak patří jemu. Když to uděláš, **hned** převeď vlastnictví na skupinovou
  roli schématu a doplň granty.
- Granty (`GRANT SELECT, INSERT, UPDATE, DELETE … TO strategie`, `GRANT USAGE, SELECT ON SEQUENCE …`)
  řeší **jen čtení a zápis, ne DDL**. Bez změny vlastnictví bude `ensure_tables()` padat dál.
- **Vlastníka si ověř dřív, než začneš hledat chybu v kódu:**

```sql
SELECT c.relname, pg_get_userbyid(c.relowner)
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw' AND c.relname LIKE '<vzor>%';
```

## Souvisí

- `doc-system-strategie-mobil-ios-notifikace-apns` — kde se to projevilo
- `doc-system-strategie-ios-notifikace-bod-obnovy-pred-nasazenim-2026-08-23` — celý průběh dne
- Jirkova pravidla práce, bod 12f: *„Tabulku založenou přes SQL most vlastní role `Marti-AI`,
  ne aplikace. Po každém založení `GRANT …`"* — **tohle je doplnění: u DDL za běhu grant nestačí.**

