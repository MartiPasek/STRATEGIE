# EC_InventuraHlav

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 51 · **Size**: 0.07 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloInventury` | nvarchar(15) | NE |  |  |
| 3 | `IDSklad` | int | NE |  |  |
| 4 | `StatusInventury` | tinyint | NE | ((0)) |  |
| 5 | `StatusText` | varchar(50) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `CastiSkladu` | nvarchar(200) | ANO |  |  |
| 12 | `KontrolaMnozstvi` | bit | ANO | ((0)) |  |
| 13 | `IDVydej` | int | ANO |  |  |
| 14 | `IDStorno` | int | ANO |  |  |
| 15 | `IDVydejFikt` | int | ANO |  |  |
| 16 | `IDStornoFikt` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_InventuraHlav` (CLUSTERED) — `ID`
