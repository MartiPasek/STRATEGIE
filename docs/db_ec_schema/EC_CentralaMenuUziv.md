# EC_CentralaMenuUziv

**Schema**: dbo · **Cluster**: Finance · **Rows**: 2,846 · **Size**: 0.39 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDMenu` | int | NE |  |  |
| 3 | `Poradi` | int | NE | ((0)) |  |
| 4 | `Oblibene` | bit | NE | ((0)) |  |
| 5 | `CisloZam` | int | ANO |  |  |
| 6 | `NaposledyPouzite` | datetime | ANO |  |  |
| 7 | `TypStromu` | nvarchar(1) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_CentralaMenuUziv` (CLUSTERED) — `ID`
