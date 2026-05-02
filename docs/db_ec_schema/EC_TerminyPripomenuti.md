# EC_TerminyPripomenuti

**Schema**: dbo · **Cluster**: Other · **Rows**: 618 · **Size**: 0.20 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `CisloZamSkolitel` | int | ANO |  |  |
| 5 | `PlatnostOd` | datetime | ANO |  |  |
| 6 | `PlatnostDo` | datetime | ANO |  |  |
| 7 | `Tema` | nvarchar(500) | ANO |  |  |
| 8 | `NoveOdpovednaOs` | nvarchar(50) | ANO |  |  |
| 9 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 10 | `IDProces` | int | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 15 | `DatDalsiSkoleni` | datetime | ANO |  |  |
| 16 | `Cinnost` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Skoleni` (CLUSTERED) — `ID`
