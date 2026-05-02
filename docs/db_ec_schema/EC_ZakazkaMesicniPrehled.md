# EC_ZakazkaMesicniPrehled

**Schema**: dbo · **Cluster**: Finance · **Rows**: 1,367 · **Size**: 0.73 MB · **Sloupců**: 42 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Utvar` | nvarchar(30) | ANO |  |  |
| 3 | `CisloZakazky` | varchar(50) | ANO |  |  |
| 4 | `Rok` | int | ANO |  |  |
| 5 | `Poradi` | int | ANO |  |  |
| 6 | `Resitel` | nvarchar(20) | ANO |  |  |
| 7 | `HodinyRealRok` | numeric(18,6) | ANO |  |  |
| 8 | `HodinyReal` | numeric(18,6) | ANO |  |  |
| 9 | `HodinyKalk` | numeric(18,6) | ANO |  |  |
| 10 | `SumaKalkVkmMesic` | numeric(18,6) | ANO |  |  |
| 11 | `HodinyProcMesic` | numeric(18,6) | ANO |  |  |
| 12 | `HodinyRozpRezie` | numeric(18,6) | ANO |  |  |
| 13 | `PrimeNaklady` | numeric(18,6) | ANO |  |  |
| 14 | `PrimeNakladyRozp` | numeric(18,6) | ANO |  |  |
| 15 | `Vynosy` | numeric(18,6) | ANO |  |  |
| 16 | `HrubyZisk` | numeric(18,6) | ANO |  |  |
| 17 | `RezieVKM` | numeric(18,6) | ANO |  |  |
| 18 | `RezieVyroba` | numeric(18,6) | ANO |  |  |
| 19 | `RezieSprava` | numeric(18,6) | ANO |  |  |
| 20 | `UkoncenoVyroba` | bit | ANO |  |  |
| 21 | `Ukonceno` | bit | ANO |  |  |
| 22 | `NepocitatNV` | bit | ANO |  |  |
| 23 | `CelkemNaklady` | numeric(18,6) | ANO |  |  |
| 24 | `CelkemNakladyRozp` | numeric(18,6) | ANO |  |  |
| 25 | `HV` | numeric(18,6) | ANO |  |  |
| 26 | `HV_Rezie` | numeric(18,6) | ANO |  |  |
| 27 | `HV_BezNV` | numeric(18,6) | ANO |  |  |
| 28 | `OstatniVynosy` | numeric(18,6) | ANO |  |  |
| 29 | `SumaVynosy` | numeric(18,6) | ANO |  |  |
| 30 | `ProcPrimychNakladu` | numeric(18,6) | ANO |  |  |
| 31 | `ZiskNaKalkHodinu` | numeric(18,6) | ANO |  |  |
| 32 | `ZiskNaRealHodinu` | numeric(18,6) | ANO |  |  |
| 33 | `NV_Naklady` | numeric(18,6) | ANO |  |  |
| 34 | `NV_Vynosy` | numeric(18,6) | ANO |  |  |
| 35 | `NakladyRezie` | numeric(18,6) | ANO |  |  |
| 36 | `VynosyRezie` | numeric(18,6) | ANO |  |  |
| 37 | `NV` | numeric(18,6) | ANO |  |  |
| 38 | `NV_DenikV` | numeric(18,6) | ANO |  |  |
| 39 | `NV_DenikN` | numeric(18,6) | ANO |  |  |
| 40 | `KalkVKM_Koef` | numeric(18,6) | ANO |  |  |
| 41 | `KalkVKM_Celkem` | numeric(18,6) | ANO |  |  |
| 42 | `DatPoslAkt` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZakazkaMesicniPrehled` (CLUSTERED) — `ID`
