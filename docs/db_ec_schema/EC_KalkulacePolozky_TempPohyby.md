# EC_KalkulacePolozky_TempPohyby

**Schema**: dbo · **Cluster**: Production · **Rows**: 714 · **Size**: 0.52 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZamObj` | int | NE | ((0)) |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(50) | ANO |  |  |
| 5 | `Mnozstvi` | numeric(18,2) | ANO |  |  |
| 6 | `MnozstviStorno` | numeric(18,2) | ANO |  |  |
| 7 | `MnOdebrane` | numeric(18,2) | ANO |  |  |
| 8 | `DruhPohybuZbo` | int | ANO |  |  |
| 9 | `Splneno` | bit | ANO |  |  |
| 10 | `CisloZakazky` | nvarchar(20) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |
| 15 | `MnozstviTisk` | numeric(18,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkulacePolozky_TempPohyby` (CLUSTERED) — `ID`
- **INDEX** `Ex_KalkulacePolozky_TempPohyby_CisloZam` (NONCLUSTERED) — `CisloZamObj`
- **INDEX** `Ex_KalkulacePolozky_TempPohyby_RegCis_CisloZak_CisloZam` (NONCLUSTERED) — `CisloZamObj, RegCis, CisloZakazky`
