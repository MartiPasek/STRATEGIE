# EC_Hala2015_Skupina

**Schema**: dbo · **Cluster**: Production · **Rows**: 12 · **Size**: 0.09 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | ANO |  |  |
| 3 | `Popis` | ntext | ANO |  |  |
| 4 | `NadrazenaSkupina` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Hala2015_Skupina` (CLUSTERED) — `ID`
