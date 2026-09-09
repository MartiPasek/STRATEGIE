# Most: cílený zápis do g2007.soubor projde jen když příkaz ZAČÍNÁ slovesem — zabalený do WITH ho hlídač odmítne

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Co se stalo (8. 9. 2026, C-28)

Cílený zápis do obsahu mobilu jsem napsal takhle — kotvy a náhrady v pomocné konstrukci `WITH`,
aby byl příkaz čitelný:

```
WITH k AS (SELECT … AS o1, … AS n1)
<sloveso pro změnu> g2007.soubor s SET obsah = replace(s.obsah, k.o1, k.n1)
FROM k WHERE s.kod=… AND md5(s.obsah)=…;
```

Most to **odmítl** hláškou `query_raw obsahuje forbidden keyword … Pouzij dedicated tool.`

Tentýž zápis **prošel bez jediné změny obsahu**, jakmile příkaz začínal přímo slovesem a kotvy
byly vepsané rovnou dovnitř (`convert_from(decode('…','base64'),'UTF8')` na místě, kde stály
odkazy do `WITH`). Návratovka: `G2007 KONSTRUKTIVNI (přímo, bez banneru)`.

## Pravidlo

**Hlídač se dívá na začátek příkazu.** Když příkaz začíná `WITH`, nepozná v něm povolenou
konstruktivní operaci nad `g2007.*` a spadne na zakázaném slově. Proto:

- **Cílený zápis do `g2007.soubor` i `g2007.python` piš tak, aby příkaz začínal slovesem změny.**
- Kotvy s diakritikou vkládej rovnou na místo přes
  `convert_from(decode('<base64>','base64'),'UTF8')` — funguje i vnořené ve `replace(replace(…))`.
- Pojistka na otisk (`AND md5(obsah)='<otisk, který jsi právě četl>'`) tím není nijak dotčená.

Souvisí s [[doc-system-strategie-most-gotchy-hlidac-dotazu-uvodni-zlom-a-lane3]] — tam je
popsané, že hlídač zakázaná slova hledá **i uvnitř textu**. Dnešní případ je druhá strana téže
mince: nejde jen o to, kde slovo stojí, ale i o to, **čím příkaz začíná**.

⚠️ Pozor i při čtení: dotaz `SELECT … WHERE obsah ILIKE '%…<zakázané sloveso>…%'` hlídač
odmítne taky, i když nic nemění. Podmínku je potřeba napsat jinak.

## Jak to bylo ověřeno

Naostro téhož dne: první tvar odmítnut (`forbidden keyword`), druhý tvar prošel a zápis byl
potvrzen čtením z databáze (změna v obsahu + zvýšená `verze`). Stalo se u čtyř zápisů do dílků
mobilu při přestavbě obrazovky Firma —
viz [[doc-system-strategie-mobil-firma-zalozky-novinky-agenda]].

