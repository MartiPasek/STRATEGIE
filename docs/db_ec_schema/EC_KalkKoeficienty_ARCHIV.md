# EC_KalkKoeficienty_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 3,676 · **Size**: 0.57 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloVerze` | int | NE |  |  |
| 3 | `Platnost` | bit | NE |  |  |
| 4 | `IDKmenZbozi` | int | ANO |  |  |
| 5 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 6 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 7 | `Puvod` | nvarchar(100) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Blokovano` | bit | NE | ((0)) |  |
| 10 | `Zamceno` | bit | NE | ((0)) |  |
| 11 | `DatZamceni` | datetime | ANO |  |  |
| 12 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE |  |  |
| 14 | `DatPorizeni` | datetime | NE |  |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkKoeficienty_ARCHIV` (CLUSTERED) — `ID, CisloVerze`
