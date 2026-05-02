# EC_KontaktAkceCis

**Schema**: dbo · **Cluster**: CRM · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `HodnotaAkce` | smallint | ANO |  |  |
| 3 | `Poradi` | smallint | ANO |  |  |
| 4 | `Nazev` | nvarchar(128) | ANO |  |  |
| 5 | `Popis` | nvarchar(2000) | ANO |  |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `ID_Edit` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KontaktAkceCis` (CLUSTERED) — `ID`
