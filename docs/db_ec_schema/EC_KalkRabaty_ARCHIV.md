# EC_KalkRabaty_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 4,980 · **Size**: 0.82 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloVerze` | int | NE |  |  |
| 3 | `Platnost` | bit | NE |  |  |
| 4 | `IDKmenZbozi` | int | NE |  |  |
| 5 | `Typ` | tinyint | NE | ((0)) |  |
| 6 | `TypText` | varchar(3) | NE |  |  |
| 7 | `Rabat` | numeric(6,1) | ANO |  |  |
| 8 | `CisloOrg` | int | ANO |  |  |
| 9 | `CisloOrgDod` | int | ANO |  |  |
| 10 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 11 | `Blokovano` | bit | NE | ((0)) |  |
| 12 | `Autor` | nvarchar(128) | NE |  |  |
| 13 | `DatPorizeni` | datetime | NE |  |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `CenaCZK` | numeric(18,2) | ANO |  |  |
| 17 | `MenaCZK` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_KalkRabaty_ARCHIV` (CLUSTERED) — `ID, CisloVerze`
