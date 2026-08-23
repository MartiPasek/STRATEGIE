# PostgreSQL: kod, ktery si sam zaklada tabulky a indexy za behu, je musi VLASTNIT - granty na to nestaci

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Kod, ktery dela DDL za behu, potrebuje VLASTNICTVI tabulky

Zapsal Claude-28 (Jirka Honomichl) **23.8.2026**, schvalila Marti-AI (msg 13474).
Zmereno na ostrem provozu pri nasazovani iOS notifikaci, ne prevzato z dokumentace.

## Jadro veci

Mame vzor, kdy si modul pri startu (nebo pri kazdem pozadavku) sam zajisti sve tabulky:

```
CREATE TABLE IF NOT EXISTS fw.neco (...);
CREATE INDEX IF NOT EXISTS ix_neco ON fw.neco (sloupec) WHERE podminka;
```

Aplikace bezi pod roli `strategie`. Kdyz tabulku **vlastni nekdo jiny** (typicky role
`Marti-AI`, protoze vznikla pres SQL most pri vyvoji), tohle **spadne**:

```
psycopg2.errors.InsufficientPrivilege: must be owner of table <tabulka>
```

## Dve veci, ktere se snadno spletou

**1) Nepomuze, ze ten index uz existuje.**
PostgreSQL u `CREATE INDEX` **otevre tabulku a zkontroluje vlastnictvi DRIV, nez vyhodnoti
`IF NOT EXISTS`**. Doplnit chybejici index tedy problem NEVYRESI - pri dalsim volani to
spadne uplne stejne. Overeno testem `SET ROLE strategie; CREATE INDEX IF NOT EXISTS ...`
nad uz existujicim indexem: skoncilo `must be owner of table`.

**2) Nepomuzou granty.**
V PostgreSQL **neexistuje samostatne pravo "zakladat indexy"**. Role muze mit
`SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER` i `CREATE` na schematu - a presto
index na cizi tabulce nezalozi. Ma-li pravo `CREATE` na schematu, **novou** tabulku zalozi
bez problemu (a bude ji vlastnit); potiz je vyhradne u tabulky, kterou vlastni nekdo jiny.

## Jak to spravne vyresit

**Doporucene: vlastnictvi prevest na SKUPINOVOU roli, do ktere patri obe strany.**

```sql
ALTER TABLE fw.<tabulka> OWNER TO fw_owners;
ALTER SEQUENCE fw.<tabulka>_id_seq OWNER TO fw_owners;
```

Proc `fw_owners`, a ne rovnou `strategie`: `fw_owners` vlastni cele schema `fw` a **cleny
jsou obe role** (`strategie` i `Marti-AI`), `strategie` ma `rolinherit = true`. Kontrola
vlastnictvi **respektuje zdedene clenstvi**, takze projdou obe role a ani jedna o nic
neprijde. Prevedenim rovnou na `strategie` by vznikla vyjimka ve schematu, kde vsechno
ostatni patri skupine.

**Alternativa jen kdyz je tabulka prokazatelne prazdna:** zahodit ji a nechat aplikaci,
at si ji zalozi sama - pak ji vlastni. **Over si pocet radku tesne pred tim**; dnes se
mezi porizenim bodu obnovy a rozhodnutim stihlo zaregistrovat zarizeni a tabulka uz
prazdna nebyla.

## Prevence

- **Tabulku, se kterou ma pracovat aplikace, nezakladej pres SQL most.** Most bezi pod
  roli `Marti-AI` a tabulka pak patri jemu. Kdyz to udelas, **hned** preved vlastnictvi
  na skupinovou roli schematu a doplni granty.
- Kdyz uz tabulku pres most zalozis, patri k tomu i
  `GRANT SELECT, INSERT, UPDATE, DELETE ... TO strategie` a
  `GRANT USAGE, SELECT ON SEQUENCE ...` - jenze **granty resi jen zapis a cteni, ne DDL**.
  Bez zmeny vlastnictvi ti `ensure_tables()` bude padat dal.
- Vlastnika si over drive, nez zacnes hledat chybu v kodu:
  ```sql
  SELECT c.relname, pg_get_userbyid(c.relowner)
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'fw' AND c.relname LIKE '<vzor>%';
  ```

## Jak se to projevi navenek

Volani, ktere `ensure_tables()` dela **uvnitr `try`** s navratem 500, vraci **HTTP 500**
a funkce je mrtva. Volani pri **startu serveru** byva ve `try/except`, ktery jen zaloguje
varovani - **server tedy nespadne** a v logu je jen radek, kterého si nikdo nevsimne.
Proto se to pozna az na koncovem chovani, ne na padu aplikace.

Souvisi: `doc-system-strategie-ios-notifikace-bod-obnovy-pred-nasazenim-2026-08-23`
(cely pribeh vcetne mereni), `doc-dochazka-podminky-slouceny-se-smlouvou` (tataz past
u spoustece historie - bez grantu spadne kazdy zapis z aplikace).

