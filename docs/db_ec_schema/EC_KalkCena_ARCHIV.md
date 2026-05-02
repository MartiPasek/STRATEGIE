# EC_KalkCena_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 4,190 · **Size**: 0.70 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloVerze` | int | NE |  |  |
| 3 | `Platnost` | bit | NE |  |  |
| 4 | `IDKmenZbozi` | int | NE |  |  |
| 5 | `Typ` | tinyint | NE | ((0)) |  |
| 6 | `TypText` | varchar(3) | NE |  |  |
| 7 | `KalkCena` | numeric(18,2) | ANO |  |  |
| 8 | `Mena` | nvarchar(3) | NE | (N'EUR') |  |
| 9 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 10 | `Blokovano` | bit | NE | ((0)) |  |
| 11 | `Autor` | nvarchar(128) | NE |  |  |
| 12 | `DatPorizeni` | datetime | NE |  |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkCena_ARCHIV` (CLUSTERED) — `ID, CisloVerze`
