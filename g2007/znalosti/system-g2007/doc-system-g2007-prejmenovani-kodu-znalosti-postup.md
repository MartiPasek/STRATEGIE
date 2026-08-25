# Přejmenování kódu znalosti — proč a jak, aby nezmrtvěly odkazy ani vyhledávání (25. 8. 2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přejmenování kódu znalosti v G2007 — proč a jak, aby nic nezmrtvělo

> Zadal **Jirka Honomichl 25. 8. 2026**, doporučila a schválila **Marti-AI** (msg 13673, 13679).
> Provedl Claude-28 na znalosti `doc-podminky-skupin-zamestnancu`
> → `doc-dochazka-podminky-skupin-zamestnancu`.

## Proč to řešit

Kód znalosti má tvar **`doc-<oblast>-<slug>`**. Když ho znalost nedodrží (vznikla dřív,
překlep, změna oblasti), **nejde ji upravit přes `@@G2007ADD`** — ten skládá kód z oblasti
a slugu, takže by místo úpravy **založil kopii vedle** té původní.

Jediná zbylá cesta je přímý `UPDATE g2007.znalost`, který **ale nepřeindexuje vektory**.
Obsah je pak správně, jenže významové hledání dál vrací starý text — a nikde to nenahlásí chybu.

Marti-AI: *„Nestandardní kód, který se bude vracet jako problém při každé editaci, je technický
dluh, který roste — za půl roku to bude někdo jiný, kdo nebude vědět, proč se to chová jinak."*

## Postup — pořadí je závazné

**1. Mapa, kde kód žije.** Ne z hlavy, dohledáním:
```sql
SELECT kod FROM g2007.znalost  WHERE obsah ILIKE '%<stary-kod>%';
SELECT kod FROM g2007.python   WHERE zdroj ILIKE '%<stary-kod>%';
SELECT kod FROM g2007.soubor   WHERE obsah ILIKE '%<stary-kod>%';
```
plus `grep` mimo databázi — repo (`docs/`, pokyny členů týmu), lokální pravidla, paměti instancí.
**Ověř i to, že nový kód ještě neexistuje** — jinak vznikne kolize.

**2. NEJDŘÍV odkazy, POTOM samotný kód.** Odkazující znalosti přepiš přes `@@G2007ADD`
(přeindexují se samy). Obráceně by mezi oběma kroky odkazy nevedly nikam.

**3. Teprve pak přejmenuj kód** — a to s dvojí pojistkou:
```sql
UPDATE g2007.znalost SET kod = '<novy>', updated_at = now()
WHERE id = <id> AND kod = '<stary>' AND md5(obsah) = '<otisk, ktery jsi cetl>'
  AND NOT EXISTS (SELECT 1 FROM g2007.znalost z2 WHERE z2.kod = '<novy>');
```
Pojistka na otisk chrání před přepsáním cizí souběžné práce, `NOT EXISTS` před kolizí kódů.
Chunky visí na `znalost_id`, ne na kódu — **přejmenování samo reindex nevyžaduje.**

**4. Ověř čtením:** nový kód existuje, starý ne, a **dotaz na starý kód přes obsah všech
aktivních znalostí vrátí nulu**.

## Když se přejmenovat nedá (nebo nechce)

Reindex po přímém `UPDATE` se dá dohnat: `POST /api/v1/erp/app/g2007/index` s tělem `{"id": <id>}`
(bez `id` přeindexuje všechny aktivní). Bere **číselné `id`**, ne kód. Vyžaduje přihlášení
a práva rodiče nebo cockpitu — **z SQL mostu ho spustit nejde**, jen z prohlížeče nebo z aplikace.
Vrací `{"ok":true,"znalosti":N,"chunku":M}`; ověř v `g2007.znalost_chunk`, že nové chunky
opravdu nesou nový text.

Souvisí: [[doc-system-g2007-editace-znalosti-pres-most-bez-poskozeni]]

