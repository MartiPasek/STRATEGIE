# EC_ObaloveHospodarstvi_GlobKonst

**Schema**: dbo · **Cluster**: Other · **Rows**: 19 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `nazev` | nvarchar(400) | ANO |  |  |
| 3 | `jednotka` | char(5) | ANO |  |  |
| 4 | `hodnota` | numeric(18,6) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObaloveHospodarstvi_GlobKonst` (CLUSTERED) — `id`
