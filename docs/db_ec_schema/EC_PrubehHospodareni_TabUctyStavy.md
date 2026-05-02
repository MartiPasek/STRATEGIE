# EC_PrubehHospodareni_TabUctyStavy

**Schema**: dbo · **Cluster**: Finance · **Rows**: 5,751 · **Size**: 1.03 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Rok` | int | NE |  |  |
| 3 | `Mesic` | int | NE |  |  |
| 4 | `Ucet` | int | NE |  |  |
| 5 | `Stredisko` | nvarchar(3) | ANO |  |  |
| 6 | `Nazev` | nvarchar(128) | ANO |  |  |
| 7 | `Vysledovka` | tinyint | NE |  |  |
| 8 | `Zustatek` | numeric(18,2) | NE |  |  |
| 9 | `DatZmenyUctu` | smalldatetime | NE |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPoslAkt` | smalldatetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_PrubehHospodareni_TabUctyStav` (CLUSTERED) — `ID`
