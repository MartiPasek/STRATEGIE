# EC_ZasedaciMistnosti

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,046 · **Size**: 0.67 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `Popis` | nvarchar(255) | NE |  |  |
| 4 | `DatumOd` | datetime | ANO |  |  |
| 5 | `DatumDo` | datetime | ANO |  |  |
| 6 | `Mistnost` | nvarchar(100) | NE |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `IDMistnosti` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZasedaciMistnosti` (CLUSTERED) — `ID`
