# EC_Sklad_VydejPozadavkuSettings

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `LoginName_Station` | nvarchar(128) | ANO |  |  |
| 3 | `LoginName_User` | nvarchar(128) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |
| 8 | `ID_Pozadavku` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_VydejPozadavkuXXX` (CLUSTERED) — `id`
