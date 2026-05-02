# EC_DopravaInterni

**Schema**: dbo · **Cluster**: Other · **Rows**: 22 · **Size**: 0.07 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Oznaceni` | nvarchar(10) | ANO |  |  |
| 3 | `Smer` | nchar(100) | ANO |  |  |
| 4 | `ObsahDodavky` | nchar(100) | ANO |  |  |
| 5 | `Blokovano` | bit | ANO |  |  |
| 6 | `SeznamResitelu` | nvarchar(255) | ANO |  |  |
| 7 | `DatumDopravyOd` | datetime | ANO |  |  |
| 8 | `DatumDopravyDo` | datetime | ANO |  |  |
| 9 | `FinalniDatumDopravy` | bit | ANO |  |  |
| 10 | `Adresa` | nvarchar(MAX) | ANO |  |  |
| 11 | `Typ` | nvarchar(255) | ANO |  |  |
| 12 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `Dat` | nchar(10) | ANO |  |  |
| 18 | `CisloZakazky` | nvarchar(10) | ANO |  |  |

## Indexy

- **PK** `PK_EC_DopravaInterni` (CLUSTERED) — `ID`
