# EC_CentralaMenu

**Schema**: dbo · **Cluster**: Finance · **Rows**: 793 · **Size**: 0.26 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `MenuText` | nvarchar(50) | NE |  |  |
| 4 | `NadrazeneMenu` | int | ANO |  |  |
| 5 | `Ikona` | tinyint | NE |  |  |
| 6 | `CisloDef` | int | ANO |  |  |
| 7 | `CisloVyjimky` | int | ANO |  |  |
| 8 | `Poradi` | int | NE | ((0)) |  |
| 9 | `Oblibene` | bit | NE | ((0)) |  |
| 10 | `CisloZam` | int | ANO |  |  |
| 11 | `NaposledyPouzite` | datetime | ANO |  |  |
| 12 | `Verejne` | bit | NE | ((0)) |  |
| 13 | `PozadovatPrihlaseni` | bit | NE | ((0)) |  |
| 14 | `Hint` | nvarchar(250) | ANO |  |  |
| 15 | `Offline` | bit | NE | ((0)) |  |
| 16 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 17 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 19 | `DatZmeny` | datetime | ANO |  |  |
| 20 | `Alias` | nvarchar(255) | ANO |  |  |
| 21 | `Sys` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_CentralaMenu` (CLUSTERED) — `ID`
