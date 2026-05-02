# EC_LogTrvani_Vazby

**Schema**: dbo · **Cluster**: Logging · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloPrehledu` | int | ANO |  |  |
| 4 | `autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Aktivni` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_LogTrvani_Vazby` (CLUSTERED) — `ID`
