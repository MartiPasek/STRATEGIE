# EC_WebSQL

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.09 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | NE |  |  |
| 3 | `Oznaceni` | nvarchar(30) | NE |  |  |
| 4 | `SQL_dotaz` | ntext | NE |  |  |
| 5 | `Poznamka` | ntext | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_WebSQL` (CLUSTERED) — `ID`
