# EC_FotoSestavy

**Schema**: dbo · **Cluster**: Other · **Rows**: 58 · **Size**: 0.09 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktivni` | bit | NE | ((1)) |  |
| 3 | `Nazev` | nvarchar(255) | NE |  |  |
| 4 | `IDNadrazeneSkupiny` | int | NE |  |  |
| 5 | `NazevNadrazeneSkupiny` | nvarchar(255) | NE |  |  |
| 6 | `Popis` | ntext | NE |  |  |
| 7 | `VzoroveFoto` | image | ANO |  |  |
| 8 | `Napoveda` | ntext | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `Poznamka` | ntext | ANO |  |  |
| 14 | `VyberZakazky` | bit | ANO |  |  |
| 15 | `Poradi` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_FotoSestavy` (CLUSTERED) — `ID`
