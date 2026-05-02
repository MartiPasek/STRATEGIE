# EC_SkoleniRidicu

**Schema**: dbo · **Cluster**: HR · **Rows**: 18 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `PlatnostOd` | datetime | ANO |  |  |
| 4 | `PlatnostDo` | datetime | ANO |  |  |
| 5 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_SkoleniRidicu` (CLUSTERED) — `ID`
