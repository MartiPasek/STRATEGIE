# EC_EventTyp

**Schema**: dbo · **Cluster**: Logging · **Rows**: 26 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Text` | nvarchar(100) | ANO |  |  |
| 3 | `Popis` | nvarchar(250) | ANO |  |  |
| 4 | `ID_I` | int | ANO |  |  |
| 5 | `ID_E` | int | ANO |  |  |
| 6 | `Oblast` | int | ANO | ((1)) | 1 = docházka, 2=WorkReporty |
| 7 | `Poradi` | tinyint | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DruhCinnosti` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_EventTyp` (CLUSTERED) — `ID`
