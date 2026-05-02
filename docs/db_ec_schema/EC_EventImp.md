# EC_EventImp

**Schema**: dbo · **Cluster**: Logging · **Rows**: 22,761 · **Size**: 3.55 MB · **Sloupců**: 24 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDTyp` | int | ANO |  |  |
| 3 | `DatumOd` | datetime | ANO |  |  |
| 4 | `DatumDo` | datetime | ANO |  |  |
| 5 | `Archiv` | int | ANO |  |  |
| 6 | `CisloZam` | int | ANO |  |  |
| 7 | `Rejected` | bit | ANO | ((0)) |  |
| 8 | `PL` | bit | ANO | ((0)) |  |
| 9 | `Schvalil` | nvarchar(128) | ANO |  |  |
| 10 | `Schvaleno` | int | NE |  |  |
| 11 | `DatSchvaleni` | datetime | ANO |  |  |
| 12 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `IDZdroj` | int | ANO |  |  |
| 18 | `DelkaUdalostiMinuty` | int | ANO |  |  |
| 19 | `ZamPoznamka` | nvarchar(4000) | ANO |  |  |
| 20 | `VedPoznamka` | nvarchar(4000) | ANO |  |  |
| 21 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 22 | `CasPauza` | int | ANO |  |  |
| 23 | `Kontrola` | bit | ANO | ((0)) |  |
| 24 | `ZaznamPresPrelomMes` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_EventImp` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_EventImp_By_IdTyp_CisloZam` (NONCLUSTERED) — `DatumOd, DatumDo, IDTyp, CisloZam`
