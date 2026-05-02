# EC_SouboryKKopirovani

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 2,175 · **Size**: 0.86 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Id` | int | NE |  |  |
| 2 | `Odkud` | nvarchar(600) | NE |  |  |
| 3 | `Kam` | nvarchar(600) | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Poznamka` | nvarchar(200) | NE | ('') |  |
| 7 | `Chyba` | bit | NE | ((0)) |  |
| 8 | `Blokovano` | bit | NE | ((0)) |  |
| 9 | `KomuInfo` | int | NE | ((0)) |  |
| 10 | `Zpracovano` | bit | NE | ((0)) |  |
| 11 | `Smazat` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_SouboryKKopirovani` (CLUSTERED) — `Id`
