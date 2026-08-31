# tenant.podminky_vychozi je POHLED - zápis hlásí 1 řádek a zpátky se nepřečte

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# `tenant.podminky_vychozi` je POHLED — zápis hlásí „1 řádek" a zpátky se nepřečte

**Peťa + Claude-26, 28. 8. 2026.** Naběhli jsme na to naostro při zakládání nové podmínky.

## Co se stalo
Zápis systémové výchozí hodnoty do `tenant.podminky_vychozi` proběhl **dvakrát**, obakrát
se schvalovacím bannerem, obakrát vrátil **`OK · 1 řádků dotčeno`** a v `fw.claude_write_request`
stojí `status = done`, `row_count = 1`, `error = NULL`.

**Řádek přesto v databázi není.** Kontrolní `SELECT` vrací 0.

## Příčina
`tenant.podminky_vychozi` **není tabulka, ale POHLED** (`information_schema.tables.table_type = VIEW`).
Skutečná data jsou v **`tenant.podminky_skupin`** — široká tabulka se sloupcem `pod_<kód>`
pro každou podmínku, jeden řádek na systém a jeden na skupinu. Pohled ji rozkládá do dlouhého
tvaru (`scope_kind`, `cond_code`, `value`). Zápis přes pohled tedy nemá kam uložit kód,
který v široké tabulce nemá sloupec.

Je to **sourozenec pasti, kterou G2007 popisuje u `tenant.staff_cond`** — jen o tabulku vedle.

## Jak to poznat dopředu
```sql
SELECT table_name, table_type FROM information_schema.tables
WHERE table_schema = 'tenant' AND table_name = '<nazev>';
```
Druhý signál: dotaz na `information_schema.columns ... WHERE is_nullable = 'NO'` vrátí
u pohledu **nula řádků**, i když má sloupce, které vypadají povinně. U tabulky vrátí aspoň
`id` a `tenant_id`. Toho jsem si všimla a nedošlo mi to — je to spolehlivý příznak.

## Důsledek pro přidání nové podmínky
Nová podmínka potřebuje:
- řádek v `tenant.staff_cond_def` (číselník, kreslí UI) — **stačí sám o sobě**,
- sloupec `pod_<kód>` v `tenant.engagement` (osobní hodnota),
- a **jen když má mít systémovou nebo skupinovou výchozí hodnotu**: sloupec `pod_<kód>`
  v `tenant.podminky_skupin` **a přepsání pohledu** `podminky_vychozi` i jeho INSTEAD OF
  spouštěče. To poslední je zásah, který je potřeba dělat vědomě.

Bez výchozí hodnoty se podmínka v kartě normálně ukáže, jen s pomlčkou = „nenastaveno".

## Poučení nad rámec případu
**Návratovka „OK, 1 řádek dotčen" není důkaz, že data v databázi jsou.** U pohledů,
spouštěčů INSTEAD OF a přepisovaných UPDATE platí jediné: **ověřuj čtením**. Kdybych
po zápisu nečetla, tvrdila bych, že je hotovo — a nebylo.

