# EC_SkoleniBOZPPO

**Schema**: dbo · **Cluster**: HR · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `SkoleniProCinnost` | nvarchar(200) | ANO |  |  |
| 4 | `PlatnostOd` | datetime | ANO |  |  |
| 5 | `PlatnostDo` | datetime | ANO |  |  |
| 6 | `NoveOdpovednaOs` | nvarchar(50) | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZamSkoleniBOZPPO` (CLUSTERED) — `ID`
