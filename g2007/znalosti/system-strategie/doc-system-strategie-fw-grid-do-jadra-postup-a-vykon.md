# Grid do jadra - co presne zalozit, co umi UI a past s funkci ve WHERE (vykon)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Pridani gridu do jadra - postup, delba prace s UI a vykon

**C24 (Kristy), 9. 9. 2026**, overeno stavbou tri gridu do jadra 203 (Vyhodnoceni zakazky).
Doplnuje [[doc-system-strategie-fw-gotchy-edit-jadro-a-vnoreny-grid]] o delbu prace a vykon.

## Kde je hranice mezi SQL a UI

**UI neumi zalozit datovou vrstvu.** Designer v ERP umi grid pretahnout z palety a pres
"⚙ Nastaveni gridu" mu naklikat data source (z pickeru), filtr, vysku, align, kontextove menu -
ale **jen kdyz uz existuje `fw.data_source` s operaci `select-detail`**. Ty radky se z UI
nezakladaji. Generator edit jader gridy negeneruje vubec.

**Prakticka delba:** datova vrstva (data_set + data_source + data_source_op) pres most,
vzhled a umisteni klidne v UI.

## Petice, kterou je potreba zalozit

1. **`fw.data_set`** - SQL detailu s `WHERE neco = :master_id`, `db_connection_id` (1 = PG,
   2 = DB_EC), `description` je **varchar(255)**, delsi vyklad patri do data_source (tam je `text`).
2. **`fw.data_source`** - `status='active'` **povinne explicitne** (jinak grid vraci 404
   a vypada to jako chybejici prava).
3. **`fw.data_source_op`** - `operation_kind='select-detail'`, `variant_code='default'`, `is_default=true`.
4. **`fw.comp_def`** - kontejnery (tabsheet + groupbox), kdyz chces novou zalozku.
5. **`fw.comp_def`** - grid typu `grid_modern` s `layout` obsahujicim `kind`, `filter_field`,
   `data_source_code`.

Typ se **nehardcoduje cislem**, ale hleda: `(SELECT id FROM fw.comp_type WHERE code='grid_modern')`.
Po zapisu se **nic nenasazuje** - jadro se cte z DB pri kazdem otevreni, staci Ctrl+F5.

## Jak zjistit, kam grid povesit

Zalozky nejsou "tab" komponenta samy o sobe. V jadre 203 je struktura
`form_root -> pagecontrol -> tabsheet -> groupbox -> grid`. Nova zalozka = novy tabsheet
pod tymz pagecontrolem + groupbox + grid. Rodice zjisti z existujiciho gridu, nehadej.

## Filtr nemusi byt jen PK

`layout.filter_field` posila **PK editovaneho zaznamu**. Kdyz potrebujes filtrovat podle
HODNOTY POLE (napr. cislo zakazky misto naseho id), pouzij **`layout.master_value_field`**
(Kristy 26. 6. 2026, zije v `design_forms.js`). Diky tomu muze grid cist i z MSSQL datasetu,
ktery nase PG id nezna.

## PAST NA VYKON - funkce ve WHERE nad celou tabulkou

Grid "Hodiny navic" se nacital **17,5 sekundy**. Pricina: dotaz volal
`ec.skupina_zakazek(z.cislo_zakazky)` uvnitr podminky nad tabulkou s 3 859 radky, takze
ji Postgres vyhodnocoval **pro kazdy radek**.

**`STABLE` to nezachrani.** `STABLE` zarucuje jen nemennost behem prikazu; kdyz funkci predas
sloupec, pocita se znovu a znovu. Cachovat ji planovac muze jen u konstantnich argumentu.

**Reseni:** spocitat jednou dopredu v `WITH ... AS MATERIALIZED` a pak uz jen porovnavat.
**17 469 ms -> 1 310 ms**, stejny vysledek.

```sql
WITH grp AS MATERIALIZED (
  SELECT ec.skupina_zakazek(z.cislo_zakazky) AS zaks
    FROM ec.vyhodnoceni_zakazka z WHERE z.id = <master_id>
)
SELECT ... FROM ec.zakazky_hod_navic h, grp
 WHERE h.cislo_zakazky = ANY(grp.zaks)
```

## Rucni skladani jadra myší ma spatnou historii

Karta zakaznika (core 72) skoncila po rucnim tahani se 3x duplicitnim polem "Firma",
zbloudilymi panely a jednim panelem jako skladkou 20 deti. A **"Reviduj CORE od nuly"
smaze vsechny komponenty** - timhle se 15. 6. 2026 ztratilo rozlozeni te karty.
**Na hotove jadro to nikdy nepoustej.** Pred riskantnim zasahem si nech udelat snimek stavu.

