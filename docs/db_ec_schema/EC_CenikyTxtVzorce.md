# EC_CenikyTxtVzorce

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDCenik` | int | ANO |  |  |
| 3 | `Poradi` | tinyint | NE | ((0)) |  |
| 4 | `NazevCilSloupce` | nvarchar(40) | ANO |  |  |
| 5 | `Vzorec` | nvarchar(280) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(80) | ANO |  |  |
| 7 | `Opce` | tinyint | ANO |  |  |
| 8 | `Blokovano` | bit | NE | ((0)) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenikyTxtVzorce` (CLUSTERED) — `ID`
