# EC_AutZprDefMailFilter

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 8 · **Size**: 0.09 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktivni` | bit | ANO | ((1)) |  |
| 3 | `EmailAdress` | nvarchar(100) | NE |  |  |
| 4 | `PredmetFilter` | nvarchar(500) | ANO | ('...') |  |
| 5 | `PrilohaFilter` | nvarchar(500) | ANO | ('...') |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `TestOndra` | ntext | ANO |  |  |

## Indexy

- **PK** `PK_EC_AutZprDefMailFilter` (CLUSTERED) — `ID`
