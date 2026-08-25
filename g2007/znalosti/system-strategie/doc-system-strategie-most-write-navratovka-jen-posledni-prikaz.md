# Most - u zapisu pres banner hlasi navratovka radky jen posledniho prikazu z davky

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Most - navratovka zapisu hlasi jen posledni prikaz z davky

**Zjistil Claude-28 (Jirka Honomichl) 25. 8. 2026 naostro pri oprave dat v tenant.**

## Co se stalo

Pres most sla jedna davka dvou zapisovych prikazu oddelenych strednikem - prvni menil
deset radku v `tenant.att_employee`, druhy dva radky v `tenant.engagement`.

Navratovka mostu hlasila:

```
# STATUS - WRITE OK - 2 radku - request #2481
OK - 2 radku dotceno
```

**Vypadalo to, jako by se provedl jen druhy prikaz a prvni propadl.** Ve skutecnosti
probehly oba - overeno ctenim z databaze hned potom (deset jmen doplnenych, dva radky
s pracovnimi dny opravene).

## Pravidlo

**Cislo v navratovce zapisu je pocet radku POSLEDNIHO prikazu davky, ne soucet za celou davku.**

Z navratovky proto NELZE poznat, jestli probehly vsechny prikazy. Plati to spolu se starsi
gotchou, ze zapisove cesty mostu vraci neutralni odpoved i pri uspechu.

## Co delat

1. **Vzdy overit ctenim z databaze**, ne navratovkou - a overit KAZDY prikaz davky zvlast.
   Nejlepsi je kontrolni dotaz, ktery se zepta na vysledek obou zmen naraz
   (napr. "kolik radku jeste NEMA doplnenou hodnotu" - ma vyjit nula).
2. **Nepanikarit a hlavne nespoustet davku znovu**, kdyz cislo nesedi. Opakovani zapisu
   muze napachat vic skody nez puvodni nejistota - nejdriv se podivat do dat.
3. U davky, kde na poradi zalezi, je bezpecnejsi **poslat prikazy jako samostatne zapisy**
   a kazdy zvlast overit.

## Souvisejici

- `doc-system-strategie-bridge-most-lanes-ops` - linky mostu, OPS linka, dalsi gotchy z provozu
- `doc-system-strategie-dev-workflow-prikazy` - most obecne

