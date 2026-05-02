# EC_DELPHI_PravaSkupinyUziv

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Skupina` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_PravaSkupinyUziv` (CLUSTERED) — `ID`
