# EC_Sklad_StornovydejkySettings

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

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
| 8 | `ID_Stornovydejka` | int | ANO |  |  |
| 9 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 10 | `FilterZakazek` | nvarchar(10) | ANO |  |  |
| 11 | `SV_IDDoklad` | int | ANO |  |  |
| 12 | `Kontrola` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Sklad_StornovydejkySettings` (CLUSTERED) — `id`
