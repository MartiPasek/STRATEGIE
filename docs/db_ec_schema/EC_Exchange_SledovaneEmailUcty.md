# EC_Exchange_SledovaneEmailUcty

**Schema**: dbo · **Cluster**: CRM · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `EmailAdresa` | nvarchar(512) | ANO |  |  |
| 3 | `EmailCredentials` | nvarchar(512) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |
| 8 | `Aktivni` | bit | ANO | ((0)) |  |
| 9 | `EmailAdresa_Kopie` | nvarchar(512) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Exchange_SledovaneEmailUcty` (CLUSTERED) — `id`
