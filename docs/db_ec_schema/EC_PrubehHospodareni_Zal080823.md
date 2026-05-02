# EC_PrubehHospodareni_Zal080823

**Schema**: dbo · **Cluster**: Finance · **Rows**: 14 · **Size**: 0.13 MB · **Sloupců**: 78 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `ROK` | int | NE |  |  |
| 3 | `SumaRezie001` | numeric(19,0) | ANO |  |  |
| 4 | `SumaRezie002` | numeric(19,0) | ANO |  |  |
| 5 | `SumaSpravniRezie` | numeric(19,0) | ANO |  |  |
| 6 | `SumaVKM` | numeric(19,0) | ANO |  |  |
| 7 | `VynosyVRxxxx` | numeric(19,0) | ANO |  |  |
| 8 | `VynosySWxxxx` | numeric(19,0) | ANO |  |  |
| 9 | `VynosyPRxxxx001` | numeric(19,0) | ANO |  |  |
| 10 | `VynosyPRxxxx002` | numeric(19,0) | ANO |  |  |
| 11 | `VynosySdruzena` | numeric(19,0) | ANO |  |  |
| 12 | `NakladyVRxxxx` | numeric(19,0) | ANO |  |  |
| 13 | `NakladySWxxxx` | numeric(19,0) | ANO |  |  |
| 14 | `NakladyPRxxxx001` | numeric(19,0) | ANO |  |  |
| 15 | `NakladyPRxxxx002` | numeric(19,0) | ANO |  |  |
| 16 | `NakladySdruzena` | numeric(19,0) | ANO |  |  |
| 17 | `SumaHodinKalkZakazkyRok` | numeric(19,0) | ANO |  |  |
| 18 | `SumaKalkVkmRok` | numeric(19,0) | ANO |  |  |
| 19 | `SumaHodinZakazkyRok` | numeric(19,0) | ANO |  |  |
| 20 | `SumaHodinOstatniRok` | numeric(19,0) | ANO |  |  |
| 21 | `CelkovyPodilRezieNaHodinuZakazky` | numeric(19,0) | ANO |  |  |
| 22 | `CelkovyPodilRezieNaKalkHodinuZakazky` | numeric(19,0) | ANO |  |  |
| 23 | `PodilSpravnilRezieNaHodinuZakazkyRok` | numeric(19,0) | ANO |  |  |
| 24 | `PodilVkmNaHodinuZakazkyRok` | numeric(19,0) | ANO |  |  |
| 25 | `PodilRezieNaVynos002` | numeric(19,0) | ANO |  |  |
| 26 | `PodilSpravniRezieNaVynos002` | numeric(19,0) | ANO |  |  |
| 27 | `KoefRealKalkVKM` | numeric(19,0) | ANO |  |  |
| 28 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 29 | `Material` | numeric(19,6) | ANO |  |  |
| 30 | `Kooperace` | numeric(19,6) | ANO |  |  |
| 31 | `OstPrimeNakl` | numeric(19,6) | ANO |  |  |
| 32 | `Vykony` | numeric(19,6) | ANO |  |  |
| 33 | `SpravniRezie` | numeric(19,6) | ANO |  |  |
| 34 | `ObchRezie` | numeric(19,6) | ANO |  |  |
| 35 | `Trzby` | numeric(19,6) | ANO |  |  |
| 36 | `HV` | numeric(19,0) | ANO |  |  |
| 37 | `Hodiny` | numeric(19,6) | ANO |  |  |
| 38 | `PC_Hod` | numeric(19,6) | ANO |  |  |
| 39 | `Mesic` | int | ANO |  |  |
| 40 | `Naklady001` | numeric(19,0) | ANO |  |  |
| 41 | `Vynosy001` | numeric(19,0) | ANO |  |  |
| 42 | `Zustatek001` | numeric(20,0) | ANO |  |  |
| 43 | `Naklady002` | numeric(19,0) | ANO |  |  |
| 44 | `Vynosy002` | numeric(19,0) | ANO |  |  |
| 45 | `Zustatek002` | numeric(20,0) | ANO |  |  |
| 46 | `Naklady900` | numeric(19,0) | ANO |  |  |
| 47 | `Vynosy900` | numeric(19,0) | ANO |  |  |
| 48 | `Zustatek900` | numeric(20,0) | ANO |  |  |
| 49 | `Naklady` | numeric(19,0) | ANO |  |  |
| 50 | `Vynosy` | numeric(19,0) | ANO |  |  |
| 51 | `Zustatek` | numeric(20,0) | ANO |  |  |
| 52 | `Naklady1_900` | numeric(22,0) | ANO |  |  |
| 53 | `Vynosy1_900` | numeric(22,0) | ANO |  |  |
| 54 | `HV_1_900` | numeric(23,0) | ANO |  |  |
| 55 | `Naklady2_900` | numeric(22,0) | ANO |  |  |
| 56 | `Vynosy2_900` | numeric(22,0) | ANO |  |  |
| 57 | `HV_2_900` | numeric(23,0) | ANO |  |  |
| 58 | `HVrozp_1_900` | numeric(19,0) | ANO |  |  |
| 59 | `HVrozp_2_900` | numeric(19,0) | ANO |  |  |
| 60 | `Dat_PoslAkt_mes` | smalldatetime | ANO |  |  |
| 61 | `Dat_PoslAkt_HV` | smalldatetime | ANO |  |  |
| 62 | `PrNaklad002` | numeric(19,0) | ANO |  |  |
| 63 | `PrRezie002` | numeric(19,0) | ANO |  |  |
| 64 | `ProcNaklad002` | numeric(19,0) | ANO |  |  |
| 65 | `ProcRezie002` | numeric(19,0) | ANO |  |  |
| 66 | `RealNaklad002` | numeric(19,0) | ANO |  |  |
| 67 | `RealRezie002` | numeric(19,0) | ANO |  |  |
| 68 | `RezieJenVP` | numeric(18,0) | ANO |  |  |
| 69 | `RezieBezVPnaKalkHod` | numeric(18,0) | ANO |  |  |
| 70 | `RezieBezVP` | numeric(18,0) | ANO |  |  |
| 71 | `RezieJenVPnaKalkHod` | numeric(18,0) | ANO |  |  |
| 72 | `zRezieVP` | numeric(18,0) | ANO |  |  |
| 73 | `zRezieIT` | numeric(18,0) | ANO |  |  |
| 74 | `zRezieNakup` | numeric(18,0) | ANO |  |  |
| 75 | `zRezieDilna` | numeric(18,0) | ANO |  |  |
| 76 | `zRezieSprava` | numeric(18,0) | ANO |  |  |
| 77 | `ZustatekMP002` | numeric(19,0) | ANO |  |  |
| 78 | `SumaRezie900` | numeric(19,0) | ANO |  |  |
