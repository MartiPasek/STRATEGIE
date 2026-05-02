# EC_Dochazka_Udalosti

**Schema**: dbo · **Cluster**: HR · **Rows**: 15,746 · **Size**: 2.59 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `DatumOdPozad` | datetime | ANO |  |  |
| 4 | `DatumDoPozad` | datetime | ANO |  |  |
| 5 | `DatumOdSchval` | datetime | ANO |  |  |
| 6 | `DatumDoSchval` | datetime | ANO |  |  |
| 7 | `DatumOdReal` | datetime | ANO |  |  |
| 8 | `DatumDoReal` | datetime | ANO |  |  |
| 9 | `Schvalil` | int | NE | ((0)) |  |
| 10 | `Typ` | int | NE | ((0)) |  |
| 11 | `IdZdroj` | int | NE | ((0)) |  |
| 12 | `TabZdroj` | nvarchar(50) | NE | (N'RucniPorizeni') |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `DatumOdPozad_Y` | int | ANO |  |  |
| 18 | `DatumOdPozad_M` | int | ANO |  |  |
| 19 | `DatumOdPozad_D` | int | ANO |  |  |
| 20 | `DatumDoPozad_Y` | int | ANO |  |  |
| 21 | `DatumDoPozad_M` | int | ANO |  |  |
| 22 | `DatumDoPozad_D` | int | ANO |  |  |
| 23 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 24 | `ZamPoznamka` | nvarchar(4000) | ANO |  |  |
| 25 | `VedPoznamka` | nvarchar(4000) | ANO |  |  |
| 26 | `CisloZakazky` | nvarchar(15) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Dochazka_Udalosti` (CLUSTERED) — `ID`
