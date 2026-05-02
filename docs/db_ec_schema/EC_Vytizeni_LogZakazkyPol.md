# EC_Vytizeni_LogZakazkyPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 486,936 · **Size**: 279.36 MB · **Sloupců**: 39 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `idHLAV` | int | NE |  |  |
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
| 28 | `_Oblast` | nvarchar(256) | ANO |  |  |
| 29 | `RitDodan` | int | ANO |  |  |
| 30 | `RitPotvrzen` | int | ANO |  |  |
| 31 | `_VytizeniExterne` | bit | ANO |  |  |
| 32 | `ZhDoDnes` | int | ANO |  |  |
| 33 | `ZapsaneHodinyMimoPlan` | int | ANO |  |  |
| 34 | `TopujNabidku` | int | ANO |  |  |
| 35 | `Razeni` | datetime | ANO |  |  |
| 36 | `BarvaRamecek` | varchar(6) | ANO |  |  |
| 37 | `AutorLog` | nvarchar(126) | ANO | (suser_sname()) |  |
| 38 | `DatPorizeniLog` | datetime | ANO | (getdate()) |  |
| 39 | `ID` | int | NE |  |  |
