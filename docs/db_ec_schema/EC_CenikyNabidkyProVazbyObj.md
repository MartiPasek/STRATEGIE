# EC_CenikyNabidkyProVazbyObj

**Schema**: dbo · **Cluster**: Finance · **Rows**: 150 · **Size**: 0.07 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Cenik` | int | ANO |  |  |
| 3 | `ID_Nabidka` | int | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(20) | ANO |  |  |
| 5 | `PouzitiIproDalsiPrj` | bit | NE | ((1)) |  |
| 6 | `TextDoObjednavky` | nvarchar(200) | ANO |  |  |
| 7 | `Blokovano` | bit | NE | ((0)) |  |
| 8 | `CisloOrgZakaznik` | int | ANO |  |  |
| 9 | `Poznamka` | nvarchar(255) | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `ID_VazbaCenik` | int | ANO |  |  |
| 15 | `Jazyk` | nvarchar(3) | ANO |  |  |
| 16 | `NabidkaZakaznik` | nvarchar(100) | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenikyNabidkyProVazbyObj` (CLUSTERED) — `ID`
