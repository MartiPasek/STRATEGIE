# Podklad fakturace OSVC: DPH v odečtu záloh a proč Centrála plátcům nic nenabízí (19.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# DPH v odectu zaloh + parovani zaloh na zakazky

Claude-24 (Kristy), 19. 8. 2026. Zjisteno pri Fazi 1, overeno v kodu procedur i na datech.

## Co je fakt (z kodu)

`EC_Zakazky_GenPodkladFakturace` pri zalozeni polozky objednavky zapisuje:

```sql
UPDATE TabPohybyZbozi SET CCBEZDANIKC = @SumaKC, ... WHERE ID = @Ident
INSERT INTO EC_Zakazky_PlatbyZam (..., Vyplaceno, ...) VALUES (..., @SumaKC, ...)
```

Tedy do polozky objednavky i do `PlatbyZam.Vyplaceno` jde TATAZ castka BEZ DANE.
`CCsDPHKc` si Helios dopocita ze sazby DPH na polozce (u platcu 21 %).

Odecitaci dotaz v `_Priprava` ale sahá na **`P.CCSDPHKC`**, tedy na castku S DANI:

```sql
OUTER APPLY (SELECT sum(ISNULL(P.CCSDPHKC,0)) Suma FROM EC_Zakazky_PlatbyZam Fin
             LEFT JOIN TabPohybyZbozi P ON Fin.IDPolVobj = P.ID ...)
```

**Zapisuje se bez dane, odecita se s dani.** U neplatcu DPH to nikdy nevadilo (sazba je 0
nebo prazdna, obe castky se rovnaji), u platcu to znamena odecet o 21 % vyssi.

Data 19.8.2026 (soucty za celou historii, `Vyplaceno` vs `CCBezDaniKc` vs `CCsDPHKc`):
platci DPH jsou z dilenskych OSVC **327 Vorisek a 372 Erhard** (pomer presne 1,21),
ostatni (105, 346, 370, 371, 425, 464) maji pomer 1,00.

## Dusledek

Erhard (372), overeno primo v Centrale:
- odecet **s DPH** (jak procedura pocita dnes): `#TmpUzavrene` vrati **0 radku**
- odecet **bez DPH**: **34 radku / 67 524 Kc**

Kristy 19.8.2026: *"Centrala to podle me neodecita s DPH, vzdy pracujeme s castkami bez DPH."*
Zapis do polozky (CCBEZDANIKC) ji dava za pravdu — odecet pres CCSDPHKC je proti vlastnimu
zapisu nekonzistentni.

## ALE: tech 67 524 Kc NENI dluh

Erhardova bilance (vse bez DPH):

| polozka | castka |
|---|---|
| narok ze zakazek (`EC_ZakazkyFinanceZam.Vyplatit`, 177 zakazek) | 2 751 669 |
| objednano na zakazky (212 plateb, `CCBezDaniKc`) | 2 738 697 |
| **rozdil** | **+12 972** |
| rezie a odmeny (mimo, samostatne) | 306 297 |

Rozdil 67 524 (resp. 128 353 pres vsechny radky) vznika tim, ze **zalohy nesedi 1:1 na tu
zakazku, ke ktere narok patri**. Po jednotlivych zakazkach vzniknou kladne zbytky, ktere se
jinde kompenzuji preplatkem — jenze do podkladu jdou jen radky > 1 Kc, takze preplatky se
nikdy neodectou. DPH v odectu tenhle sum u platcu nahodne pohlcuje; u neplatcu ne.

Slouceni zakazek (`TabZakazka_EXT._IDSkupiny`) cast toho resi a v kandidatu
`podklad_vyplaceni_pdf_faze1` uz implementovano je (Erhard tim spadl ze 196 503 na 99 815,
Vorisek ze 127 588 na 116 318) — ale nestaci to, zalohy jsou rozhazene i mimo skupiny.

## Slepa ulicka, kterou uz nemusi nikdo prochazet

`EC_ZamPlatba_VlozVetu` plni `EC_ZamestPlatby` a z ni aktualizuje
`EC_ZakazkyFinanceZam.Vyplaceno`/`ZbyvaVyplatit`. **U OSVC se tahle cesta nepouziva** —
pro Erharda ma `EC_ZamestPlatby` 0 radku, `Vyplaceno` = 0 a `ZbyvaVyplatit` = `Vyplatit`.
Filtr `ZbyvaVyplatit > 1` v `#TmpUzavrene` proto u OSVC prakticky nic neodfiltruje;
jediny skutecny odecet jsou objednavky.

## Otevrene rozhodnuti (ceka na Kristy, pripadne Martiho)

Pocitat bez DPH (jak Kristy chce) samo o sobe problem neresi — jen odkryje zbytky, ktere
DPH schovavala. Navrh: castky brat bez DPH, ale zustatek hlidat **souhrnne za cloveka**
(u Erharda 12 972 Kc), ne jen po jednotlivych zakazkach.

