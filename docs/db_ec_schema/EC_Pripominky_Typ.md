# EC_Pripominky_Typ

**Schema**: dbo · **Cluster**: CRM · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | nvarchar(255) | ANO |  |  |
| 3 | `TypCislo` | int | ANO |  |  |
| 4 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Pripominky_Typ` (CLUSTERED) — `ID`
