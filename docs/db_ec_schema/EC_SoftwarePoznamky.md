# EC_SoftwarePoznamky

**Schema**: dbo · **Cluster**: Other · **Rows**: 98 · **Size**: 5.78 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `VerzeCentraly` | int | ANO |  |  |
| 3 | `Predmet` | nvarchar(1000) | ANO |  |  |
| 4 | `Poznamka` | varbinary(MAX) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_SoftwarePoznamky` (CLUSTERED) — `id`
