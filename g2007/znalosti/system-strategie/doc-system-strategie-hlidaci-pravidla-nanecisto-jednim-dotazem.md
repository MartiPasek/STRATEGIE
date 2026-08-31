# Jak pustit všechna hlídací pravidla nanečisto jedním dotazem (bez zápisu, bez automatu)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Jak pustit všechna hlídací pravidla nanečisto jedním dotazem

Ověřeno naostro **28. 8. 2026** (Claude-28 / Jirka Honomichl) na 88 zapnutých pravidlech
v `tenant.pojistka`. Postup **nic nezapisuje** — hodí se před zapnutím automatu, po zásahu
do tabulky, na kterou pravidla visí, nebo když chceš vědět, co by dnes svítilo.

## Dotaz

```sql
SELECT p.kod,
       btrim(array_to_string(
         xpath('//text()', query_to_xml(
           'SELECT (' || rtrim(btrim(p.kontrola), ';') || ') AS x', false, true, '')), '')) AS vysledek
FROM tenant.pojistka p
WHERE p.tenant_id = 2 AND p.aktivni = true AND COALESCE(p.kontrola,'') <> ''
ORDER BY 2, 1;
```

Vrátí ke každému pravidlu `true` / `false`. Celých 88 pravidel doběhlo za necelou vteřinu.

## Proč zrovna takhle

`query_to_xml` je **čtecí** funkce, která umí spustit dotaz uložený v textovém sloupci —
jinak by se každé pravidlo muselo kopírovat a pouštět ručně. Obalení
`SELECT (<kontrola>) AS x` je tam proto, aby výsledek dostal **známé jméno sloupce**;
bez toho se `xpath` nemá čeho chytit.

**Dvě věci, na kterých to napoprvé selhalo** (ať to nikdo nehledá znovu):

1. **`xpath('/row/x/text()', …)` vrátilo prázdno**, dokud kontrola nebyla obalená do `AS x` —
   pravidla mají výsledný sloupec pojmenovaný různě.
2. **`xpath('//text()', …)` vracelo samé mezery** — první textový uzel je odsazení mezi značkami.
   Proto `array_to_string(…, '')` + `btrim`.

`rtrim(…, ';')` je tam kvůli pravidlům, která mají na konci středník — bez něj by obalení
do závorky skončilo chybou.

## ⚠️ Omezení, se kterým počítej

Je to **jeden dotaz**, takže **jedno rozbité pravidlo shodí celý výpis**. Pro nanečisto přehled
to nevadí (chybová hláška rovnou řekne, které pravidlo to je — vyluč ho a pusť znovu),
ale **nenahrazuje to automat**: ten má každé pravidlo ve vlastním `try` se `SAVEPOINT`,
takže rozbité pravidlo označí a jede dál. Viz
[[doc-system-strategie-spoustec-hlidacich-pravidel-pojistka]].

## Kdy to použít

- **Před zapnutím** nebo změnou spouštěče — abys věděl, co první ostrý běh vysype.
- **Po zásahu do tabulky nebo pohledu**, na kterých pravidla visí — automat běží jen jednou denně
  a do té doby by ses o rozbitém pravidle nedozvěděl.
- **Když chceš jen nahlédnout** a nechceš přepsat sloupce `posledni_beh` a `posledni_vysledek`
  u všech pravidel.

