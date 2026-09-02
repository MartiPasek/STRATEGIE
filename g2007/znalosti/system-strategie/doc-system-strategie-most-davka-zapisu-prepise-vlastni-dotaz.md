# Most: davka zapisu za sebou si prepise vlastni dotaz - posilej po JEDNOM a cekej na zmizeni GO souboru (2. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Most: dávka zápisů za sebou si přepíše vlastní dotaz

**Zjištěno naostro 2. 9. 2026** (Claude-28 / Jirka Honomichl), formulaci schválila Marti-AI.

## Co se stalo

Poslal jsem **čtyři `@@G2007ADD` za sebou** v jednom cyklu s pevnou pauzou **15 s** mezi nimi.
**Prošly jen dva.**

Jeden zápis trval **22 s** — tedy déle než pauza. Tím jsem přepsal `CLAUDE3_SQL.sql`
**ve chvíli, kdy z něj most ještě četl**: jeden dotaz se ztratil a jeden se provedl dvakrát.

**Nejzákeřnější na tom je, že to nic nenahlásí.** Návratovky u všech čtyř hlásily `OK`
a u dvou různých zápisů se objevila **stejná časová značka**. Ztrátu odhalilo až
zpětné čtení a porovnání `md5` kus po kuse.

## Pravidlo

> **Zápisy přes most posílej po jednom.** Další spusť teprve, až zmizí `CLAUDE<N>_GO.txt` —
> **pevná pauza nestačí**, doba zápisu kolísá od **0,7 s do 22 s**. Souborný `OK`
> v návratové hodnotě o ztrátě ani kolizi neřekne nic. Po celé dávce **ověř každý kus zvlášť
> porovnáním `md5`** — opakovaná časová značka u dvou různých zápisů je signál kolize.

Prakticky:

```bash
cp <pripraveny_zapis>.sql CLAUDE3_SQL.sql
printf 'db=pg
%s
' "$(date +%s)" > CLAUDE3_GO.txt
sleep 35
ls CLAUDE3_GO.txt 2>/dev/null || echo "zpracovano"   # zbyl-li GO, most jeste pracuje
```

A po celé dávce jedním dotazem:

```sql
SELECT kod, md5(ltrim(obsah, chr(10))) IN ('<md5 #1>', '<md5 #2>', ...) AS sedi,
       length(obsah), updated_at
FROM g2007.znalost WHERE kod IN (...);
```

## Souvislosti

- Doplňuje `doc-system-strategie-most-gotchy-zapis-kodu-7-8-2026` (jiné pasti téhož kanálu)
  a `doc-system-strategie-most-timeout-zapisu-nerika-nic`.
- Je to **jiný jev než kolize dvou oken** o tutéž linku
  (`doc-system-strategie-bridge-most-lanes-ops`): tady si linku přepisuje **jedno a totéž
  okno samo sobě** tím, že spěchá. Oddělené linky proti tomu nepomůžou.
- Platí pro **každý** zápis přes most, nejen pro `@@G2007ADD`.

