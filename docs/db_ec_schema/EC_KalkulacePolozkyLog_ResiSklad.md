# EC_KalkulacePolozkyLog_ResiSklad

**Schema**: dbo · **Cluster**: Production · **Rows**: 4,360 · **Size**: 1.25 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `KalkPol_RegCis` | nvarchar(30) | ANO |  |  |
| 3 | `KalkPol_Mnozstvi` | numeric(12,2) | ANO |  |  |
| 4 | `Kalk_CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `StavGenerovaniDo` | smallint | NE |  |  |
| 8 | `KalkPol_ID` | int | ANO |  |  |
| 9 | `Poznamka` | nvarchar(256) | ANO |  |  |
| 10 | `KalkPolVKM_NewID` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkulacePolozkyLog_ResiSklad` (CLUSTERED) — `ID`
