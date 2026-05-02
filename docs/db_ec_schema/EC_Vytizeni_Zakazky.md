# EC_Vytizeni_Zakazky

**Schema**: dbo · **Cluster**: Production · **Rows**: 120 · **Size**: 0.27 MB · **Sloupců**: 57 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumZadani` | datetime | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(31) | ANO |  |  |
| 4 | `Nazev` | nvarchar(100) | ANO |  |  |
| 5 | `DruhyNazev` | nvarchar(100) | ANO |  |  |
| 6 | `ZakListHodiny` | numeric(23,6) | ANO |  |  |
| 7 | `ZapsaneHodiny` | int | ANO |  |  |
| 8 | `RealHodiny` | numeric(38,0) | ANO |  |  |
| 9 | `VPZak` | nvarchar(201) | ANO |  |  |
| 10 | `VP` | nvarchar(128) | ANO |  |  |
| 11 | `SpecialitaBarva` | nvarchar(100) | ANO |  |  |
| 12 | `KonDatum` | nvarchar(200) | ANO |  |  |
| 13 | `Poznamka` | ntext | ANO |  |  |
| 14 | `_Uzavreno` | int | ANO |  |  |
| 15 | `Sefmonter` | nvarchar(20) | ANO |  |  |
| 16 | `Zakaznik` | nvarchar(100) | ANO |  |  |
| 17 | `_ZobrazitVeVytizeni` | int | ANO |  |  |
| 18 | `Prideleno` | int | ANO |  |  |
| 19 | `CisloZakaznik` | int | ANO |  |  |
| 20 | `_VytizeniPoznamka` | nvarchar(4000) | ANO |  |  |
| 21 | `SefmonterCislo` | int | ANO |  |  |
| 22 | `VytizeniHodinyOdhad` | bit | ANO |  |  |
| 23 | `PravdepodobnostRealizace` | numeric(24,6) | ANO |  |  |
| 24 | `CisloZakazkyZobrazeni` | nvarchar(4000) | ANO |  |  |
| 25 | `BarvaSkupina` | nvarchar(6) | ANO |  |  |
| 26 | `BarvaZakazka` | varchar(6) | ANO |  |  |
| 27 | `JsemNabidka` | int | ANO |  |  |
| 28 | `JsemPoptavka` | int | ANO |  |  |
| 29 | `_Oblast` | nvarchar(256) | ANO |  |  |
| 30 | `RitDodan` | int | ANO |  |  |
| 31 | `RitPotvrzen` | int | ANO |  |  |
| 32 | `_VytizeniExterne` | bit | ANO |  |  |
| 33 | `ZhDoDnes` | int | ANO |  |  |
| 34 | `ZapsaneHodinyMimoPlan` | int | ANO |  |  |
| 35 | `TopujNabidku` | int | ANO |  |  |
| 36 | `Razeni` | datetime | ANO |  |  |
| 37 | `BarvaRamecek` | varchar(6) | ANO |  |  |
| 38 | `Poradi` | int | ANO |  |  |
| 39 | `IDSkupinyVytizeni` | int | ANO |  |  |
| 40 | `OdvozJenMinulost` | bit | ANO | ((0)) |  |
| 41 | `UmozniPlanovaniHodin` | int | ANO |  |  |
| 42 | `BarvaDatum` | varchar(6) | ANO |  |  |
| 43 | `BarvaRamecekDatum` | varchar(6) | ANO |  |  |
| 44 | `TypPlanu` | int | ANO |  |  |
| 45 | `kodZakazky` | nvarchar(10) | ANO |  |  |
| 46 | `Rozvadec` | nvarchar(10) | ANO |  |  |
| 47 | `Desky` | nvarchar(10) | ANO |  |  |
| 48 | `Material` | nvarchar(10) | ANO |  |  |
| 49 | `Lakovna` | nvarchar(10) | ANO |  |  |
| 50 | `Konektory` | nvarchar(10) | ANO |  |  |
| 51 | `BarvaNazevZakazky` | varchar(6) | ANO |  |  |
| 52 | `BarvaRozvadec` | varchar(6) | ANO |  |  |
| 53 | `BarvaDesky` | varchar(6) | ANO |  |  |
| 54 | `BarvaMaterial` | varchar(6) | ANO |  |  |
| 55 | `BarvaLakovna` | varchar(6) | ANO |  |  |
| 56 | `BarvaKonektory` | varchar(6) | ANO |  |  |
| 57 | `NejblizsiOdvoz` | date | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Zakazky` (CLUSTERED) — `ID`
