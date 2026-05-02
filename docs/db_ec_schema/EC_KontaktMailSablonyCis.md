# EC_KontaktMailSablonyCis

**Schema**: dbo · **Cluster**: CRM · **Rows**: 6 · **Size**: 0.14 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `Poradi` | int | ANO |  |  |
| 7 | `Nazev` | nvarchar(128) | ANO |  |  |
| 8 | `Sablona` | ntext | ANO |  |  |
| 9 | `OdkazEditor` | nvarchar(41) | ANO |  |  |
| 10 | `ListPriloh` | nvarchar(1000) | ANO |  |  |
| 11 | `PredmetEmailu` | nvarchar(256) | ANO |  |  |
| 12 | `SeznamPriloh` | nvarchar(MAX) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KontaktMailSablony` (CLUSTERED) — `ID`
