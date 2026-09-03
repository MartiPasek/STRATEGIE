# Zaloha pres most: "select ... into" tise NIC nevytvori (most ji ma za cteni) - pouzij "create table ... as select"

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo (3. 9. 2026, Claude-28 / Jirka Honomichl)

Pred etapami modularizace obsahu mobilu jsem zakladal zalohovaci tabulku pres SQL most:

```sql
SELECT * INTO g2007.soubor__zaloha_modularizace_20260903
FROM g2007.soubor WHERE kod LIKE 'apps/api/static/mobile_parts/%';
```

**Most to podle prvniho slova (`SELECT`) zaradil mezi CTENI.** Dusledek:

- **neobjevil se schvalovaci prouzek** (write banner) - nikdo to neschvaloval,
- prikaz se pustil na ctecim spojeni a na konci se **zahodil (rollback)**,
- **tabulka nevznikla**,
- jedina zpetna vazba byla hlaska `This result object does not return rows`
  (most se snazil z prikazu precist radky) - vypada jako drobnost, ne jako
  "tvuj zapis se neprovedl".

Odhalilo to az **overeni ctenim**: nasledny `SELECT count(*)` z te tabulky vratil
`UndefinedTable ... does not exist`.

## Jak to delat spravne

```sql
CREATE TABLE g2007.soubor__zaloha_modularizace_20260903 AS
SELECT * FROM g2007.soubor WHERE ...;
```

Takhle zapsany prikaz most spravne rozpozna jako **zapis**, posle ho do
schvalovaciho prouzku a po schvaleni ho provede naostro
(`STATUS: WRITE OK · 32 radku · request #2693`).

## Pravidlo

- **Zalohu ani jakoukoli jinou zmenu nikdy nepis prikazem, ktery zacina slovem `SELECT`.**
  Klasifikace zapis/cteni se dela podle zacatku prikazu, ne podle toho, co prikaz opravdu dela.
- **Po kazdem zapisu ověřuj ctenim.** Navratovka mostu je neutralni a v tomhle pripade
  dokonce vypadala jako technicka drobnost, prestoze se nestalo nic.
- Souvisi: `doc-system-strategie-most-timeout-zapisu-nerika-nic` (navratovka zapisu
  neni dukaz) a `doc-system-strategie-most-gotchy-zapis-kodu-7-8-2026`.

