# EC_DELPHI_PrehledNavi

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aplikace` | nvarchar(128) | NE | (N'Centrala') |  |
| 3 | `TypStromuPreOblNed` | nvarchar(2) | ANO |  |  |
| 4 | `ViewNumber` | int | NE |  |  |
| 5 | `IDVety` | int | NE |  |  |
| 6 | `Mode` | int | NE |  |  |
| 7 | `ModeText` | varchar(9) | ANO |  |  |
| 8 | `Poradi` | int | ANO |  |  |
| 9 | `Priorita` | int | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_PrehledNavi` (CLUSTERED) — `ID`
