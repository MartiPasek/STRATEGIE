# Nerudovka — pravidla nasazování cizích jazyků do rozvrhu (od Marti/Klárky 21.6.2026)

> Závazná pravidla generátoru rozvrhu pro 2026/2027. **Cizí jazyky se nasazují JAKO PRVNÍ.**
> Vstup = jazykové skupiny tak, jak jsou v Bakalářích (přeneseno do `tenant.bakalari_skupina`).

## Základ (nedotknutelné)
- Použít jazykové skupiny **tak, jak jsou nyní nasazené v rozvrhu 2026/2027** (skupiny `TYP=V`
  v `skupina`, s `KOD_SPOJ` = spojení napříč ročníky).
- **Jsou to skupiny jazyků napříč ročníky (mezitřídní). Musí zůstat takto na sobě a NESMÍ se NIKDY rozpojit.**
  (KOD_SPOJ skupina = jeden blok, vždy ve stejném čase.)

## Označení jazyků (z názvu/kódu skupiny) — OVĚŘENO na datech 21.6.
Konvence zkratky skupiny: `<ročník><role><jazyk><číslo>` (jazyk: N=NJ, F=FJ, R=RJ, Š=ŠJ).
- **1. cizí jazyk = AJ** — zkratka začíná **`AJ`** (AJ1, AJ2).
- **2. cizí jazyk** — **`Z` na 2. pozici**: regex `^[1-4]Z[NFRŠ]\d` (1ZN1=NJ, 1ZF1=FJ, 1ZR1=RJ, 1ZŠ1=ŠJ).
- **3. cizí jazyk** — **`D` na 2. pozici**: regex `^[1-4]D[NFRŠ]\d` (2DN1, 3DR1, 4DŠ1), mezitřídní.
- ⚠ **POZOR na falešné `D`** — `Dív` (dívky), `DKr` (digitální kresba), `GD*` (grafický design) NEJSOU 3. CJ.
  Detekuj jen vzorem výše, ne pouhým „obsahuje D".
- Mezitřídní spojení drží **`KOD_SPOJ`** (skupiny se stejným KOD_SPOJ = jeden blok, nikdy nerozpojit).
- Data: `tenant.bakalari_skupina` (skolni_rok='2026/27', tenant 13): **477 skupin** — V(volitelné/jazyky)=390, T(celá třída)=30, F(dívky/chlapci)=57. Sloupce: zkratka, nazev, kod_skup, kod_trid, kod_spoj, kod_pred, kod_ucit, kod_cykl, typ, pocet_zaku, clenove, filtr, …

## Požadavky učitelů / rozložení hodin
1. **AJ ve 4. ročníku** — zachovat jednu **dvouhodinovku** AJ.
2. **Učební obory, AJ** — ideálně **1+1+1+1** nebo **2+1+1**.
3. **2. cizí jazyk (Z)** — může být **2+1+1**, příp. **2+2**.
4. **3. cizí jazyk (D)** — skupiny na sobě (mezitřídní), hodiny **1+1**.
5. **Ždimerová** — začínat **od 2. hodiny**.
6. **Šedová** — končit **7. hodinou**.
7. **AJ (1. cizí jazyk)** nesmí končit **později než 7. h**.
8. **2. a 3. cizí jazyk** může **výjimečně** končit **8. h**.
9. **Nesmí být za sebou** 1./2./3. cizí jazyk — mezi nimi musí být **jiný předmět**.
10. **4. ročníky** — 2 hodiny AJ za sebou jako **dvojhodinovka**, ostatní po hodině.
11. **Cizí jazyky se ve třídě musí učit ve 3 dnech.**
12. **3. cizí jazyk** se může učit **4. nebo 5. den**.
13. Jazyky nasazuj po hodině: **1+1+1** nebo **1+1+2**.

## Pořadí nasazování (engine)
1. Cizí jazyky (tato pravidla) — PRVNÍ, jako pevná kostra.
2. (Další podklady Marti pošle — ostatní předměty, učebny, ...)

## Pozn. k implementaci
- Skupiny v `tenant.bakalari_skupina` (TYP=V, KOD_SPOJ) = atomické bloky.
- Jazyk poznat z názvu/zkratky skupiny: AJ; „Z" v názvu = 2. CJ; „D" = 3. CJ.
- Tvrdá omezení (učitel start/end, max konec hodiny, 3 dny, ne za sebou) = constraints solveru.
- Výstup = varianty rozvrhu → `tenant.rozvrh_verze` + `rozvrh_bunka` (viz `nerudovka_rozvrh_verze.md`),
  Klárka porovná a vybere.
