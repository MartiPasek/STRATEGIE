# EC_FinZamPodminky_KraceniNarokuDovolene

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `CisloZam` | int | NE |  |  |
| 7 | `DruhSmlouvy` | int | NE |  |  |
| 8 | `NarokDovolena` | int | NE |  |  |
| 9 | `Poznamka` | nvarchar(500) | ANO |  |  |
| 10 | `PlatnostRok` | int | NE | (datepart(year,getdate())) |  |

## Indexy

- **PK** `PK_EC_FinZamPodminky_KraceniNarokuDovolene` (CLUSTERED) — `ID`
