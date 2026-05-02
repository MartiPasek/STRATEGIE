# EC_DELPHI_TabObecnyPrehledPodminky

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 340 · **Size**: 0.20 MB · **Sloupců**: 19 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloPrehledu` | int | NE |  |  |
| 3 | `Podminka` | nvarchar(1000) | NE | ('') |  |
| 4 | `FontName` | nvarchar(100) | NE | ('MS Sans Serif') |  |
| 5 | `FontStyle` | tinyint | NE | ((0)) |  |
| 6 | `FontSize` | int | NE | ((10)) |  |
| 7 | `FontColor` | int | NE | ((-16777208)) |  |
| 8 | `BackgroundColor` | int | NE | ((-16777201)) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `DatPorizeni_D` | int | ANO |  |  |
| 14 | `DatPorizeni_M` | int | ANO |  |  |
| 15 | `DatPorizeni_Y` | int | ANO |  |  |
| 16 | `DatPorizeni_Q` | int | ANO |  |  |
| 17 | `DatPorizeni_W` | int | ANO |  |  |
| 18 | `DatPorizeni_X` | datetime | ANO |  |  |
| 21 | `AplikovatStyle` | tinyint | NE | ((30)) |  |

## Indexy

- **PK** `PK_EC_DELPHI_TabObecnyPrehledPodminky` (CLUSTERED) — `ID`
