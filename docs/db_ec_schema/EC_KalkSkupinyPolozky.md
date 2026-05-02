# EC_KalkSkupinyPolozky

**Schema**: dbo · **Cluster**: Production · **Rows**: 1,675 · **Size**: 0.20 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Skupina` | int | ANO |  |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `Zamceno` | bit | NE | ((0)) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 11 | `DatZamceni` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkSkupinyRegCisVazby` (CLUSTERED) — `ID`
