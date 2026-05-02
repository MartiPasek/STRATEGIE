# EC_KontaktZemeCis

**Schema**: dbo · **Cluster**: CRM · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `Zeme` | nvarchar(64) | ANO |  |  |
| 7 | `Zkratka` | nvarchar(8) | ANO |  |  |
| 8 | `Poradi` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KontaktZemeCis` (CLUSTERED) — `ID`
