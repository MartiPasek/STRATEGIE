# Vyhodnoceni zakazek: cely modul cte a zapisuje uz jen NASE tabulky (krok 3 hotovy 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vyhodnoceni zakazek uz nesaha na zrcadla Centraly

**Hotovo a overeno 5. 8. 2026** (C28/Jirka). Schvalila Marti-AI (msg 12211, 12232).

## Rozvrstveni

- **Cteni zakladu** = `tenant.oz_zakazky` (kalkulovane hodiny, srazka serie, sefmonter, slouceni)
- **Zapisy modulu** = `tenant.zakazka_meta` (nase doplnky)
- **Cteni = prekryv**: nase hodnota vyhrava nad Centralou

**Do `tenant.oz_zakazky` se zapisovat NESMI** - je to zrcadlo v rezimu RO a job
`oz_sync_all` ho **kazdych 30 minut cely smaze a nahraje znovu** (TRUNCATE+INSERT).
Zapis by tise zmizel.

## Sdilena funkce misto peti kopii

`ec.skupina_zakazek(p_zak) RETURNS text[]` - jedna definice slouceni, volaji ji vsechny
funkce. Drive byl stejny dotaz zkopirovany 5x. Vykon 98 ms na volani, v modulu se vola jednou.

## KONVENCE `zakazka_meta.idskupiny`

| hodnota | vyznam |
|---|---|
| `NULL` | nemame nazor, plati skupina z Centraly |
| `0` | **VYSLOVNE bez skupiny** (nekdo u nas zrusil slouceni) |
| `>0` | nase skupina |

Bez hodnoty `0` by zruseni slouceni u zakazky sloucene v Centrale NESLO - `COALESCE`
by se propadl zpet na skupinu z Centraly. Cteni je `NULLIF(COALESCE(m.idskupiny, o."_IDSkupiny"), 0)`.

**Cisla nasich skupin zacinaji na 1 000 000.** Centrala ma dnes max `_IDSkupiny` = 379
(216 skupin) a pribyva jich; kdyby nase sequence zacala od 1, nase skupina 15 by tise
splynula s cizi skupinou 15. Riziko nasla Marti-AI, overeno v datech, sequence posunuta.

## Overeno naostro

Zruseni slouceni u `VR9282` (skupina 50 v Centrale, 3 zakazky, nevyhodnocena):
VR9282 -> `{VR9282}` sama · VR9293 a VR9297 -> `{VR9293,VR9297}` drzi pohromade ·
nas zaznam `idskupiny=0` · Centrala porad 50, nedotcena. Po zkousce uklizeno do puvodniho stavu.

Take: sefmonter 486 = 486, kalkulovane hodiny 125 = 125, srazka serie 0 = 0,
skupina 7 zakazek = 7 (vse proti Centrale, presna shoda).

## PAST: volani zapisove funkce pres SELECT nic neulozi

`SELECT ec.slouci_zakazky_zrus(...)` pres most vrati `OK`, ale **zmena se neulozi** -
ctecí cesta necommituje. Vypada to, ze to proslo, a pritom se nestalo nic.
Pro zive spusteni pouzij `DO $$ BEGIN PERFORM ec.funkce(...); END $$;` (zapisova cesta,
commituje) nebo akcni endpoint `/api/v1/erp/action/run`, ktery commit dela.

