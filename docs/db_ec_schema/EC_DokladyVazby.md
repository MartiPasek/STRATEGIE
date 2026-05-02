# EC_DokladyVazby

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 31,471 · **Size**: 21.20 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Odkud` | int | ANO |  |  |
| 3 | `ID_Kam` | int | ANO |  |  |
| 4 | `Doklad_Odkud` | nchar(15) | ANO |  |  |
| 5 | `Doklad_Kam` | nchar(15) | ANO |  |  |
| 6 | `Tabulka_Odkud` | nchar(30) | ANO |  |  |
| 7 | `Tabulka_Kam` | nchar(30) | ANO |  |  |
| 8 | `Popis` | nchar(200) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `Neplatna` | bit | ANO |  |  |
| 12 | `DuvodZneplatneni` | nvarchar(100) | ANO |  |  |
| 13 | `RadaDoklOdkud` | int | ANO |  |  |
| 14 | `RadaDoklKam` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_DokladyVazby` (CLUSTERED) — `ID`
