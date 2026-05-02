# EC_UniXLSexportHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poradi` | int | ANO | ((1000)) |  |
| 3 | `Aktivni` | bit | ANO | ((0)) |  |
| 4 | `Nazev` | nvarchar(500) | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `SelectDefiniceHlav` | nvarchar(MAX) | ANO |  |  |
| 11 | `SelectDefinicePol` | nvarchar(MAX) | ANO |  |  |
| 12 | `Sesit_PathFileName` | nvarchar(128) | NE | ('') |  |
| 14 | `PodminkaBit` | bit | NE | ((0)) |  |
| 16 | `PodminkaCellAdres` | nvarchar(128) | NE | ('') |  |
| 17 | `PodminkaVysledek` | nvarchar(128) | NE | ('') |  |

## Indexy

- **PK** `PK_EC_UniXLSexportHlav` (CLUSTERED) — `ID`
