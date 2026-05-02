# EC_PlanovaniVyroby_VikendySvatky

**Schema**: dbo · **Cluster**: Other · **Rows**: 18 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 4 | `DatumOd` | datetime | ANO |  |  |
| 5 | `DatumDo` | datetime | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_PlanovaniVyroby_PraceNavic` (CLUSTERED) — `ID`
