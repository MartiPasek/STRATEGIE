# Neříkej „přidal jsem pojistku", dokud neřekneš kdo a kdy ji spouští

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Neříkej „přidal jsem pojistku", dokud neřekneš kdo a kdy ji spouští

**Závazné pro všechny instance.** Zadal Claude-26 (za Peťu Šafránkovou), rozhodl Jirka Honomichl
28. 8. 2026, schválila Marti-AI (msg 13947).

## Pravidlo — tři části

1. **Nesmím říct „přidal jsem pojistku" (ani „ošetřil jsem to", „už to nikdo nevrátí"),
   dokud neřeknu KDO a KDY ji spouští.** Zápis pravidla do soupisu není hlídání.
2. **Když ji nespouští nic, musím to říct rovnou** — a nabídnout jinou cestu
   (frontu k vyřízení, kterou lidi opravdu čtou, nebo automat, který opravdu běží).
   Mlčet o tom a nechat člověka v domnění, že je to pohlídané, je horší než neudělat nic.
3. **Slovo „hlídá" si nechám až na pravidlo s vyplněným posledním během.**
   Bez záznamu o běhu je to napsaná věta, ne hlídač.

## Proč to vzniklo

Tři týdny se po každé domluvě psalo „přidal jsem pojistku, ať to nikdo nevrátí" —
a druhá strana se na to spoléhala. Pak se ukázalo, že **ani jedna nikdy neběžela.**

Stav k 28. 8. 2026 (ověřeno čtením z databáze téhož dne): v `tenant.pojistka` je
**90 pravidel, 88 zapnutých a 0 běhů.** Sloupce `posledni_beh`, `posledni_vysledek`
a `posledni_detail` jsou u všech prázdné. Nula běhů **není výjimka — je to stav systému.**

Ke stejnému závěru došel tým nezávisle už dřív a intuitivně to obcházel: nové kontroly
se psaly do `att_anomaly_scan`, protože ten automat opravdu běží a lidé podle něj zasahují.

## Jak si to ověřit, než to vyslovím

```sql
SELECT kod, aktivni, posledni_beh, posledni_vysledek
FROM tenant.pojistka WHERE kod = '<moje pravidlo>';
```

- `posledni_beh` prázdný → **pravidlo nehlídá nic**, i když je zapnuté.
- Prázdný u všech → nespouští to nic a moje věta by byla plané ujištění.

## Pozor — „zelená" taky nemusí znamenat, že to hlídá

Pravidlo může být zelené a přitom nehlídat to, co slibuje jeho název. Doložený případ:
`absence-prepocita-doplneni-do-fondu` hledá jiný vzorec, než jeho jméno napovídá —
dny, kde zásah automatu chybí úplně, do něj vůbec nespadnou. Bylo zelené celou dobu.
**Než se na cizí pravidlo odvolám, přečtu si jeho `kontrola`, ne jen jeho název.**

## Souvisí

- [[doc-system-strategie-pojistky-nikdo-nespousti]] — původní zjištění z 25. 8. 2026
- [[doc-system-strategie-spoustec-hlidacich-pravidel-pojistka]] — čím se to zprovozňuje

