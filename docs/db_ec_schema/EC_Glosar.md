# EC_Glosar

**Schema**: dbo · **Cluster**: Other · **Rows**: 13 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Pojem` | nvarchar(100) | ANO |  |  |
| 3 | `VyznamLaik` | nvarchar(100) | ANO |  |  |
| 4 | `VyznamOdb` | nvarchar(100) | ANO |  |  |
| 5 | `Obor` | nvarchar(100) | ANO |  |  |
| 6 | `PoznamkaLaik` | nvarchar(MAX) | ANO |  |  |
| 7 | `PoznamkaOdb` | nvarchar(MAX) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Glosar` (CLUSTERED) — `ID`
