# EC_KmenZbozi_DefVlastnosti

**Schema**: dbo · **Cluster**: Production · **Rows**: 32 · **Size**: 0.09 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | ANO |  |  |
| 3 | `Popis` | ntext | ANO |  |  |
| 4 | `Typ` | nvarchar(50) | ANO |  |  |
| 5 | `Hodnota` | nvarchar(50) | ANO |  |  |
| 6 | `IDNadrazene` | int | ANO |  |  |
| 7 | `Poznamka` | ntext | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_KmenZbozi_DefVlastnosti` (CLUSTERED) — `ID`
