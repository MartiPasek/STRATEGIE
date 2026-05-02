# EC_OrgSmernice_PristupnostVazby

**Schema**: dbo · **Cluster**: HR · **Rows**: 281 · **Size**: 0.20 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPristupnost` | int | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_OrgSmernice_PristupnostVazby` (CLUSTERED) — `ID`
