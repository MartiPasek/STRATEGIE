# EC_UkolyProblemove

**Schema**: dbo · **Cluster**: Other · **Rows**: 124 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Typ_Problem` | smallint | ANO |  |  |
| 4 | `ID_Ukol` | int | ANO |  |  |
| 5 | `ID_Smernice` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_UkolyProblemove` (CLUSTERED) — `ID`
