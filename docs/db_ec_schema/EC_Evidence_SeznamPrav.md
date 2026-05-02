# EC_Evidence_SeznamPrav

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `Typ` | nvarchar(100) | NE |  |  |
| 3 | `Nazev` | nvarchar(255) | NE |  |  |
| 4 | `Popis` | nvarchar(4000) | ANO |  |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Evide__3213E83FC600B1B3` (CLUSTERED) — `id`
