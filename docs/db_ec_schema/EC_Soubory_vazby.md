# EC_Soubory_vazby

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDSouboryHlav` | int | ANO |  |  |
| 3 | `IDSoubor` | int | ANO |  |  |
| 4 | `IDApp` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Soubory_vazby` (CLUSTERED) — `ID`
