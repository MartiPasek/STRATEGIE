# EC_AutZprDokladPol

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 22,458 · **Size**: 13.39 MB · **Sloupců**: 61 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Polozka` | nvarchar(10) | ANO |  |  |
| 4 | `Pozice` | nvarchar(10) | ANO |  |  |
| 5 | `PocetEvid` | numeric(18,2) | ANO |  |  |
| 6 | `Pocet` | numeric(12,2) | ANO |  |  |
| 7 | `MJ` | nvarchar(10) | ANO |  |  |
| 8 | `MJkontr` | nvarchar(10) | ANO |  |  |
| 9 | `MJEvid` | nvarchar(10) | ANO |  |  |
| 10 | `ObjCislo` | nvarchar(100) | ANO |  |  |
| 11 | `RegCis` | nvarchar(30) | ANO |  |  |
| 12 | `Nazev` | nvarchar(200) | ANO |  |  |
| 13 | `DPH` | tinyint | ANO |  |  |
| 14 | `SlevaProc` | numeric(10,2) | ANO |  |  |
| 15 | `SlevaCena` | numeric(18,2) | ANO |  |  |
| 16 | `CenaBruttoMJ` | numeric(18,6) | ANO |  |  |
| 17 | `CenaBruttoCelkem` | numeric(18,6) | ANO |  |  |
| 18 | `CenaNettoMJ` | numeric(18,6) | ANO |  |  |
| 19 | `CenaNettoCelkem` | numeric(18,6) | ANO |  |  |
| 20 | `CenaNettoMJEvid` | numeric(18,6) | ANO |  |  |
| 21 | `DodaciList` | nvarchar(100) | ANO |  |  |
| 22 | `DodaciListDatum` | datetime | ANO |  |  |
| 23 | `PotvrzDatDodani` | datetime | ANO |  |  |
| 24 | `IDZboSklad` | int | ANO |  |  |
| 25 | `KoefEvid` | numeric(12,2) | ANO |  |  |
| 26 | `PocetEvidSUM` | numeric(12,2) | ANO |  |  |
| 27 | `PocetSUM` | numeric(12,2) | ANO |  |  |
| 28 | `ObjPocetSUM` | numeric(12,2) | ANO |  |  |
| 29 | `PrPocetSUM` | numeric(12,2) | ANO |  |  |
| 30 | `FaPocetSUM` | numeric(12,2) | ANO |  |  |
| 31 | `ObjID` | int | ANO |  |  |
| 32 | `ObjPocet` | numeric(12,2) | ANO |  |  |
| 33 | `ObjMJ` | nvarchar(10) | ANO |  |  |
| 34 | `ObjCena` | numeric(18,6) | ANO |  |  |
| 35 | `ObjCisloZakazky` | nvarchar(15) | ANO |  |  |
| 36 | `ObjOK` | bit | ANO |  |  |
| 37 | `ObjCenaOK` | bit | ANO |  |  |
| 38 | `PrID` | int | ANO |  |  |
| 39 | `PrPocet` | numeric(12,2) | ANO |  |  |
| 40 | `PrMJ` | nvarchar(10) | ANO |  |  |
| 41 | `PrCena` | numeric(18,6) | ANO |  |  |
| 42 | `PrOK` | bit | ANO |  |  |
| 43 | `UzivPolOK` | bit | ANO |  |  |
| 44 | `UzivInfo` | nvarchar(200) | ANO |  |  |
| 45 | `CasTXT` | nvarchar(10) | ANO |  |  |
| 46 | `VS` | nvarchar(100) | ANO |  |  |
| 47 | `KS` | nvarchar(20) | ANO |  |  |
| 48 | `SS` | nvarchar(20) | ANO |  |  |
| 49 | `Text1` | nvarchar(140) | ANO |  |  |
| 50 | `Text2` | nvarchar(1000) | ANO |  |  |
| 51 | `Text3` | nvarchar(140) | ANO |  |  |
| 52 | `Text4` | nvarchar(140) | ANO |  |  |
| 53 | `NazevUctu` | nvarchar(80) | ANO |  |  |
| 54 | `CisloUctu` | nvarchar(80) | ANO |  |  |
| 55 | `KodBanky` | int | ANO |  |  |
| 56 | `KodUctovani` | int | ANO | ((0)) |  |
| 57 | `TypTransakce` | nvarchar(80) | ANO |  |  |
| 58 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 59 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 60 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 61 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_AutZprDokladPol` (CLUSTERED) — `ID`
