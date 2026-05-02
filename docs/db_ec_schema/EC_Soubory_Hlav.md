# EC_Soubory_Hlav

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Popis` | nvarchar(100) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Soubory_Hlav` (CLUSTERED) — `ID`
