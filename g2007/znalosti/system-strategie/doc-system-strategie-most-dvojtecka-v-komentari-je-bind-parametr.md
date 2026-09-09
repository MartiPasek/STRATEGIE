# Most: dvojtecka v KOMENTARI SQL je brana jako bind parametr a dotaz spadne

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Most: `:NECO` v komentari shodi dotaz

**Zjisteno 8. 9. 2026** (Claude-24 / Kristy), pri stavbe datasetu pro modul Vyhodnoceni zakazek.

## Co se stalo

Poslal jsem pres most obycejny SELECT, ktery mel v **komentari** zminku o puvodnim dotazu
z Centraly:

```sql
-- Testuji na cele zakazce (misto :ID davam vyber podle zakazky), at je videt vic radku.
SELECT o.id, o.cislo_zam, ...
FROM ec.vyhodnoceni_osoba o
WHERE o.cislo_zakazky = 'VR10584';
```

Vysledek:

```
(sqlalchemy.exc.InvalidRequestError) A value is required for bind parameter 'ID'
```

V dotazu **zadny bind parametr nebyl** - jen v komentari. SQLAlchemy parsuje `:jmeno`
v celem textu vcetne komentaru a chce pro nej hodnotu.

## Pravidlo

**Do komentaru SQL posilaneho mostem nepis `:` nasledovanou pismenem.** Kdyz potrebujes
zminit parametr puvodniho dotazu, napis ho jinak - napr. `parametr ID`, `dvojtecka-ID`
nebo `[:]ID`. Tyka se to obou smeru (`db=pg` i `db=mssql`), protoze prochazi tymtez enginem.

## Proc si toho snadno nevsimnes

Hlaska mluvi o bind parametru, takze prvni reflex je hledat chybu v tele dotazu - a tam je
vsechno v poradku. Clovek pak zbytecne prepisuje funkcni SQL. Kdyz vidis "A value is required
for bind parameter" a v dotazu zadny parametr nemas, **koukni do komentaru.**

Souvisi: [[doc-system-strategie-most-gotchy-hlidac-dotazu-uvodni-zlom-a-lane3]] (hlidac odmita
klicova slova i v textu - jina past, stejny princip: most cte i to, co povazujes za "jen text").

