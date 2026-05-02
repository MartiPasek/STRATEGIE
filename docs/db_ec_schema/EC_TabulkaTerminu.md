# EC_TabulkaTerminu

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypTerminu` | smallint | ANO |  |  |
| 3 | `IDDoklad` | int | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 5 | `Datum` | datetime | ANO |  |  |
| 6 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TabulkaTerminu` (CLUSTERED) — `ID`
