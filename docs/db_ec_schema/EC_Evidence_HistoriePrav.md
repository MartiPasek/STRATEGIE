# EC_Evidence_HistoriePrav

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `IDEPrava` | int | NE |  |  |
| 3 | `Typ` | nvarchar(100) | NE |  |  |
| 4 | `Datum` | date | NE |  |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Evide__3213E83FFB57AAE5` (CLUSTERED) — `id`
