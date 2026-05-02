# EC_KalkulacePolozky_TempVykryti

**Schema**: dbo · **Cluster**: Production · **Rows**: 378 · **Size**: 0.70 MB · **Sloupců**: 19 · **FK**: 0 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZamObj` | int | NE | ((0)) |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(50) | ANO |  |  |
| 5 | `PocetKusuSum` | numeric(18,2) | NE | ((0)) |  |
| 6 | `PoceStejnychRegCis` | int | NE | ((0)) |  |
| 7 | `Objednano` | numeric(18,2) | ANO |  |  |
| 8 | `Vydano` | numeric(18,2) | ANO |  |  |
| 9 | `StornoVydeje` | numeric(18,2) | ANO |  |  |
| 10 | `SkladDispozice` | numeric(18,2) | ANO |  |  |
| 11 | `SkladMinimum` | numeric(18,2) | ANO |  |  |
| 12 | `SkladSortiment` | nvarchar(40) | ANO |  |  |
| 13 | `SkladKontrolaBlokovana` | bit | ANO |  |  |
| 14 | `CisloZakazky` | nvarchar(20) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `SkladBlokace` | numeric(18,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkulacePolozky_TempVykryti` (CLUSTERED) — `ID`
- **INDEX** `Ex_KalkulacePolozky_TempVykryti_CisloZam` (NONCLUSTERED) — `CisloZamObj`
- **INDEX** `Ex_KalkulacePolozky_TempVykryti_RegCis_CisloZak_CisloZam_` (NONCLUSTERED) — `CisloZamObj, RegCis, CisloZakazky`
