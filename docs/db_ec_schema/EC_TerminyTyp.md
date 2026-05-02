# EC_TerminyTyp

**Schema**: dbo · **Cluster**: Other · **Rows**: 8 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Text` | nvarchar(100) | ANO |  |  |
| 3 | `Popis` | nvarchar(250) | ANO |  |  |
| 4 | `Poradi` | tinyint | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SkoleniTyp` (CLUSTERED) — `ID`
