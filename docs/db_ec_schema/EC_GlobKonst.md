# EC_GlobKonst

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.09 MB · **Sloupců**: 31 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Help_CisZam` | int | ANO |  |  |
| 3 | `Kalk_KcHod_Zakazky` | int | ANO |  |  |
| 4 | `KoefPrepoctuZam` | numeric(10,2) | ANO |  |  |
| 5 | `BezpHeslo` | varchar(50) | ANO |  |  |
| 6 | `DatGenerOpakUkolu` | datetime | ANO |  |  |
| 7 | `DatPoslKontrPridelSmernic` | datetime | ANO |  |  |
| 8 | `CenaMed_EUR_100Kg` | numeric(18,2) | ANO |  |  |
| 9 | `PrednastavenySklad` | nvarchar(30) | ANO |  |  |
| 10 | `PrednastaveneObdobi` | int | ANO |  |  |
| 11 | `Firma` | nvarchar(10) | ANO |  |  |
| 12 | `RootDataServer` | nvarchar(50) | ANO |  |  |
| 13 | `VObj_SchvaleniLimit1` | int | ANO | ((30000)) |  |
| 14 | `VObj_SchvaleniLimit2` | int | ANO | ((40000)) |  |
| 15 | `KALK_LimitInfoVP` | numeric(19,6) | ANO |  |  |
| 16 | `PrednastavSQLTimeOutVsec` | int | ANO |  |  |
| 17 | `DatSpusteniSluzbyUpdate` | datetime | ANO |  |  |
| 18 | `All_DALI_Light_powerOFF_time` | time | ANO |  |  |
| 19 | `PLCapp_running` | bit | ANO |  |  |
| 20 | `PLCapp_cislo_zmeny` | int | ANO |  |  |
| 21 | `DefFontSize` | nvarchar(50) | ANO | (N'Verdana11') |  |
| 22 | `ProjektDefaultPopisZadani` | ntext | ANO |  |  |
| 23 | `MzdyVeZpracovani` | bit | NE | ((0)) |  |
| 24 | `MQTT_WrittenDateTime` | datetime | ANO |  |  |
| 25 | `MQTT_RunFlag` | int | NE |  |  |
| 29 | `Info_PotvrzDatDod_KLepsimu_PocetDnu` | smallint | NE | ((30)) |  |
| 30 | `Info_PotvrzDatDod_KHorsimu_PocetDnu` | smallint | NE | ((7)) |  |
| 31 | `Mzdy_PlatitPrescasyDilna` | bit | ANO | ((0)) |  |
| 32 | `RezieHodnoceni` | int | ANO |  |  |
| 33 | `ToleranceKontrolyCenFakKalk` | numeric(10,2) | ANO |  |  |
| 34 | `KALK_LimitInfoVratkyVP` | numeric(19,6) | ANO |  |  |

## Indexy

- **PK** `PK_EC_GlobKonst` (CLUSTERED) — `ID`
