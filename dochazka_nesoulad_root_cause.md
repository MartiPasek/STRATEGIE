# Docházka — nesoulad zdrojů (root cause + rozhodnutí)
Peta + Claude‑26, 24. 7. 2026

## Problém (1 věta)
Stejný člověk a den vypadá **jinak** podle toho, kde se koukneš — a `att_entry` (to, co jde do mezd) se rozešlo s `vyroba_work` (to, co ukazuje Docházka new i mobil).

## Důkaz (živá data)
**Bláha 24. 7.:** Opravy docházky (`att_entry`) ~**6 h** (start 04:57, navíc blok Režie 1,29 h) × Docházka new (`vyroba_work`) **4,30 h** (start 05:49, bez režie).

**Dvořáková (49):**

| Den | Opravy docházky (mzdy) | Docházka new |
|---|---|---|
| 7. 7. | 6,50 h | 0,93 h |
| 14. 7. | 7,16 h | 4,08 h |
| 15. 7. | 6,00 h | **nic** |
| 16. 7. | 6,00 h | **nic** |

→ Opravy provedené v „Opravách docházky" se do Docházky new **vůbec nepropsaly**.

## Proč (kořen, ověřeno v kódu)
1. Docházka new čte tabulku **`vyroba_work`**, která se plní z appky (`work_alloc`) **jen za poslední 3 dny** → starší dny a opravy se tam nikdy nedostanou.
2. Opravy v „Opravách docházky" mění **`att_entry`**, ale **ne** `vyroba_work`.
3. Už u zdroje appka plní `att_entry` a `work_alloc` **jinak** (jiný začátek, jiný rozpad po zakázkách, režie navíc).

**Závěr:** `vyroba_work` je zastaralá/neúplná kopie. **Pravda je `att_entry`** (to se edituje a jde do mezd).

## Rozhodnutí (Peta)
Musí to **sedět všude stejně**. Jediná cesta = **jeden zdroj pravdy = `att_entry`**. Docházka new (a všechny pohledy) musí čerpat z něj, ne ze `vyroba_work`.

## Co opravit — směr (dořešit s Jirkou; vlastní sync + appku)
- **Docházka new přepnout na zdroj `att_entry`** (zakázka = `project_ref`, činnost = typ/činnost záznamu). Případně `vyroba_work` plnit 1:1 z `att_entry` bez 3denního okna.
- **Opravy docházky** musí změnu okamžitě promítnout do toho, co čte Docházka new (žádné čekání na 3denní sync).
- **Odstranit dvojkolejnost** `work_alloc → vyroba_work`, ať neexistují dvě „pravdy".
- U mezd **nic neopravovat naslepo** — nejdřív srovnat zdroj, pak čísla.

## Stejný jev
Potvrzeno u Bláhy i Dvořákové — není to jednotlivost, je to systémové.
