# EC_ZakazkaPrehled

**Schema**: dbo · **Cluster**: Finance · **Rows**: 2,683 · **Size**: 1.52 MB · **Sloupců**: 45 · **FK**: 0 · **Indexů**: 1

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
| 11 | `HodinyRozpRezieA` | numeric(18,6) | ANO |  |  |
| 12 | `HodinyRozpRezieM` | numeric(18,6) | ANO |  |  |
| 13 | `PrimeNakladyA` | numeric(18,6) | ANO |  |  |
| 14 | `PrimeNakladyM` | numeric(18,6) | ANO |  |  |
| 15 | `VynosyA` | numeric(18,6) | ANO |  |  |
| 16 | `VynosyM` | numeric(18,6) | ANO |  |  |
| 17 | `VynosyC` | numeric(18,6) | ANO |  |  |
| 18 | `CelkemNakladyVcNV_A` | numeric(18,6) | ANO |  |  |
| 19 | `CelkemNakladyA` | numeric(18,6) | ANO |  |  |
| 20 | `CelkemNakladyM` | numeric(18,6) | ANO |  |  |
| 21 | `CelkemNakladyC` | numeric(18,6) | ANO |  |  |
| 22 | `RezieVKM` | numeric(18,6) | ANO |  |  |
| 23 | `RezieVyroba` | numeric(18,6) | ANO |  |  |
| 24 | `RezieSprava` | numeric(18,6) | ANO |  |  |
| 25 | `UkoncenoVyroba` | bit | ANO |  |  |
| 26 | `Ukonceno` | bit | ANO |  |  |
| 27 | `NepocitatNV` | bit | ANO |  |  |
| 28 | `HV_BezNV` | numeric(18,6) | ANO |  |  |
| 29 | `HV_A` | numeric(18,6) | ANO |  |  |
| 30 | `HV_M` | numeric(18,6) | ANO |  |  |
| 31 | `HV_C` | numeric(18,6) | ANO |  |  |
| 32 | `HV_Rezie` | numeric(18,6) | ANO |  |  |
| 33 | `OstatniVynosy` | numeric(18,6) | ANO |  |  |
| 34 | `ZiskNaKalkHodinu` | numeric(18,6) | ANO |  |  |
| 35 | `ZiskNaRealHodinu` | numeric(18,6) | ANO |  |  |
| 36 | `NV_Naklady` | numeric(18,6) | ANO |  |  |
| 37 | `NV_Vynosy` | numeric(18,6) | ANO |  |  |
| 38 | `NakladyRezie` | numeric(18,6) | ANO |  |  |
| 39 | `VynosyRezie` | numeric(18,6) | ANO |  |  |
| 40 | `NV` | numeric(18,6) | ANO |  |  |
| 41 | `NV_DenikV` | numeric(18,6) | ANO |  |  |
| 42 | `NV_DenikN` | numeric(18,6) | ANO |  |  |
| 43 | `KalkVKM_Koef` | numeric(18,6) | ANO |  |  |
| 44 | `KalkVKM_Celkem` | numeric(18,6) | ANO |  |  |
| 45 | `DatPoslAkt` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZakazkaPrehled` (CLUSTERED) — `ID`
