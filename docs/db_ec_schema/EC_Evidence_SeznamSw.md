# EC_Evidence_SeznamSw

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | NE |  |  |
| 3 | `Verze` | nvarchar(100) | ANO |  |  |
| 4 | `TypLicence` | nvarchar(100) | ANO |  |  |
| 5 | `PlatnostDoLicence` | date | ANO |  |  |
| 6 | `Licence` | nvarchar(4000) | ANO |  |  |
| 7 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 8 | `Adresar` | nvarchar(4000) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Evide__3213E83F58656A65` (CLUSTERED) — `id`
