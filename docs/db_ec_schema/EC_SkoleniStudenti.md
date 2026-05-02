# EC_SkoleniStudenti

**Schema**: dbo · **Cluster**: HR · **Rows**: 176 · **Size**: 0.20 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `IDSkol` | int | ANO |  |  |
| 4 | `DruhSkol` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_SkoleniStudenti` (CLUSTERED) — `ID`
