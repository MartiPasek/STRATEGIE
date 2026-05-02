# EC_DELPHI_PravaSkupiny

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | NE |  |  |
| 3 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_PravaSkupiny` (CLUSTERED) — `ID`
