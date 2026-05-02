# EC_UniXLSexportPol

**Schema**: dbo · **Cluster**: Other · **Rows**: 9 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `Polozka` | bit | ANO | ((0)) |  |
| 4 | `Poradi` | int | ANO | ((0)) |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `FieldName` | nvarchar(128) | ANO |  |  |
| 8 | `_pozice_OD` | nvarchar(10) | ANO | ('') |  |
| 9 | `_pozice_DO` | nvarchar(10) | ANO | ('') |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_UniXLSexportPol` (CLUSTERED) — `ID`
