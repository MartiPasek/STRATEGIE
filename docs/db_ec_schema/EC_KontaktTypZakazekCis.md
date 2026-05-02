# EC_KontaktTypZakazekCis

**Schema**: dbo · **Cluster**: CRM · **Rows**: 7 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `TypZakazky` | nvarchar(128) | ANO |  |  |
| 7 | `Poradi` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KontaktTypZakazekCis` (CLUSTERED) — `ID`
