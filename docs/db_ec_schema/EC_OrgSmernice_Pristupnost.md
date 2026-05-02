# EC_OrgSmernice_Pristupnost

**Schema**: dbo · **Cluster**: HR · **Rows**: 5 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Pristupnost` | int | ANO |  |  |
| 3 | `PristupnostText` | nvarchar(50) | ANO |  |  |
| 4 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Smernice_Pristupnost` (CLUSTERED) — `ID`
