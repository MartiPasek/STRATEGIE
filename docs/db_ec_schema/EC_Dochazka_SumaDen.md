# EC_Dochazka_SumaDen

**Schema**: dbo · **Cluster**: HR · **Rows**: 89,722 · **Size**: 36.02 MB · **Sloupců**: 58 · **FK**: 0 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `FPD` | numeric(3,2) | ANO |  |  |
| 4 | `Uzavreno` | bit | ANO | ((0)) |  |
| 5 | `CasNarizenoVolno` | numeric(19,2) | ANO | ((0)) | bit - příznak, že není práce a je povoleno jít do mínusu |
| 6 | `DatumPripadu` | datetime | ANO |  |  |
| 7 | `DatumPripadu_Y` | int | ANO |  |  |
| 8 | `DatumPripadu_M` | int | ANO |  |  |
| 9 | `DatumPripadu_D` | int | ANO |  |  |
| 10 | `CasCelkem` | numeric(19,2) | ANO |  |  |
| 11 | `CasDovolena` | numeric(19,2) | ANO |  |  |
| 12 | `CasSickDay` | numeric(19,2) | ANO |  |  |
| 13 | `CasLekar` | numeric(19,2) | ANO |  |  |
| 14 | `CasNemoc` | numeric(19,2) | ANO |  |  |
| 15 | `CasOCR` | numeric(19,2) | ANO |  |  |
| 16 | `CasNahradniVolno` | numeric(19,2) | ANO |  |  |
| 17 | `CasAbsence` | numeric(19,2) | ANO |  |  |
| 18 | `CasMontaz` | numeric(19,2) | ANO |  |  |
| 19 | `CasRezie` | numeric(19,2) | ANO |  |  |
| 20 | `CasPrescas` | numeric(21,2) | ANO |  | Hodiny nad (FPD + NeplacenyPrescas)  |
| 21 | `CasChybi` | numeric(20,2) | ANO |  |  |
| 22 | `CasPauza` | numeric(19,2) | ANO |  |  |
| 23 | `HodSazba` | int | ANO |  |  |
| 24 | `RezieKC` | numeric(8,3) | ANO |  |  |
| 25 | `RezieVyplaceno` | numeric(8,3) | ANO |  |  |
| 26 | `RezieZbyvaVyplatit` | numeric(9,3) | ANO |  |  |
| 27 | `NeplacenyPrescas` | numeric(19,2) | ANO |  | Počet hodin, které se nepočítají jako přesčas |
| 28 | `CasZacatek` | datetime | ANO |  |  |
| 29 | `CasKonec` | datetime | ANO |  |  |
| 30 | `HPP` | bit | ANO |  |  |
| 31 | `DPP` | bit | ANO |  |  |
| 32 | `OSVC` | bit | ANO |  |  |
| 33 | `PocetStravenek` | int | ANO |  |  |
| 34 | `Konto` | numeric(19,2) | ANO |  | Soucet hodin, ktere chybi odpracovat a nebyly nařízené |
| 35 | `KontoPlacene` | numeric(19,2) | ANO |  | hodiny, které chybí odpracovat protože bylo nařízeno |
| 36 | `KontoPlaceneMax` | numeric(19,2) | ANO |  | Součet hodin, které chybí odpracovat protože bylo nařízeno |
| 37 | `DatumZalozeniPlacKonta` | datetime | ANO |  | Datum, kdy se poprvé dostal nařízeně do mínusu |
| 38 | `KontoPlaceneKC` | numeric(30,2) | ANO |  |  |
| 39 | `KontoPlaceneKCCelkem` | numeric(19,2) | ANO |  |  |
| 40 | `ProcentoPlaceniKonta` | smallint | ANO |  |  |
| 41 | `ZakladZaHod` | int | ANO |  |  |
| 42 | `OsOhodZaHod` | int | ANO |  |  |
| 43 | `VykonOhodZaHod` | int | ANO |  |  |
| 44 | `HrHodBezFK` | numeric(19,2) | ANO |  |  |
| 45 | `SrazkaNarVolno` | numeric(19,2) | ANO |  |  |
| 46 | `CasNepritomen` | numeric(19,2) | ANO |  |  |
| 47 | `CasNahrazeneVolno` | numeric(19,2) | ANO |  |  |
| 48 | `PremieNahrazeneVolno` | numeric(19,2) | ANO |  |  |
| 49 | `CasOtec` | numeric(19,2) | ANO |  |  |
| 51 | `CasVolno60` | numeric(19,2) | ANO |  |  |
| 52 | `CasMaterska` | numeric(19,2) | ANO |  |  |
| 53 | `CasNeplVolno` | numeric(19,2) | ANO |  |  |
| 54 | `CasVolno80` | numeric(19,2) | ANO |  |  |
| 55 | `CasVolno90` | numeric(19,2) | ANO |  |  |
| 56 | `CasPrekazkaVPraci` | numeric(19,2) | ANO |  |  |
| 57 | `CasVolnoBezMzdy` | numeric(19,2) | ANO |  |  |
| 58 | `CasVolno70` | numeric(19,2) | ANO |  |  |
| 59 | `CasNepritAPS` | numeric(19,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Dochazka_SumaDen` (CLUSTERED) — `ID`
- **INDEX** `CisloZam_DatumPripadu_Includes` (NONCLUSTERED) — `Konto, KontoPlacene, KontoPlaceneMax, DatumZalozeniPlacKonta, KontoPlaceneKCCelkem, CisloZam, DatumPripadu`
- **INDEX** `CisloZam_DatumPripadu_CasCelkem` (NONCLUSTERED) — `CisloZam, DatumPripadu, CasCelkem`
