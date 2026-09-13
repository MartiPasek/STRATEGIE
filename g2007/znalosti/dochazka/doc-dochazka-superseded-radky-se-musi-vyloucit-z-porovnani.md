# Docházka: nahrazené (superseded) řádky se musí vyloučit, jinak vyjdou tisíce neexistujících hodin

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Pravidlo

Když porovnáváš `tenant.att_entry` (docházka = rámec dne) proti `tenant.vyroba_work`
(výkaz práce = rozpad na zakázky a činnosti), **vždycky vyfiltruj řádky se
`status = 'superseded'`**. Jsou to nahrazené verze záznamu, které v tabulce zůstávají
jako historie. Když je započítáš, docházka vyjde nafouknutá a rozdíl proti výkazu
vypadá jako obrovská ztráta hodin, která ve skutečnosti neexistuje.

Kristýna Marešová 11. 9. 2026: *„dej si pozor na superseded, na to někdy zapomínáme
a pak nám vychází strašidelné statistiky."* Není to teorie — stalo se to opakovaně.

## Doložený případ (C24, 11. 9. 2026)

Tři pokusy změřit „chybějící hodiny", tři různé nesmysly, než padl správný filtr:

| pokus | metoda | výsledek | co bylo špatně |
|---|---|---|---|
| 1 | rozdíl po dvojicích osoba+den+zakázka | 26 019 h | počítala se i režie |
| 2 | rozdíl po dvojicích osoba+den | 24 354 h | duplicitní karty zaměstnance + plánované absence na prosinec |
| 3 | párování přes `att_entry_id` | 410 h | **nevyloučené superseded řádky** |
| 4 | součty po měsících, bez režie, bez superseded | **0,0 h** | — |

Správný výsledek: duben 4 495,9 vs 4 495,9 h, květen 4 365,1 vs 4 365,1 h — na desetinu
přesně. Zbylé měsíce se liší o jednotky hodin z pěti tisíc.

## Stavy, které `att_entry.status` nabývá

`pending` (drtivá většina) · `superseded` (nahrazené) · `approved` · `confirmed` ·
`imported` · `announced`. K 11. 9. 2026 je od června 2 504 řádků `superseded`.

⚠️ **`is_active` na tohle nestačí** — mají ho `false` prakticky všechny docházkové řádky,
takže filtrem na `is_active` superseded neodfiltruješ. Rozlišuje jedině `status`.

## Další dvě pasti ve stejném porovnání

1. **Režie.** `project_ref` / `zakazka_ref` nabývá hodnoty `Rezie`, což není zakázka.
   Bez jejího vyloučení přiteče do rozdílu přes 25 000 h.
2. **Jeden člověk = víc karet** (doktrína #24). Agregace přes `att_employee.cislo_zam`
   sečte hodiny víc lidí dohromady — objevily se dny s 61 odpracovanou hodinou.
   Páruj přes `vyroba_work.att_entry_id`, ne přes osobní číslo.

## Co po očištění opravdu zbylo

Z 20 798 spárovaných dnů je **9 případů** (41,1 h), kdy se rámec dne prodloužil,
ale rozpad na úseky se nedopočítal. Tři cesty, kterými to vzniká: ruční oprava
příchodu/odchodu (5×), potvrzení příchodu přes notifikaci (2×) a auto-odhlášení
o půlnoci u home office (2×). Dopad na vyhodnocení zakázek mají jen dva z nich
(VR10641 4,74 h, VR10660 4,52 h) — zbytek je bez zakázky nebo na režii.

