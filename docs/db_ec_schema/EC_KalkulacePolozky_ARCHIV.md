# EC_KalkulacePolozky_ARCHIV

**Schema**: dbo · **Cluster**: Production · **Rows**: 593,390 · **Size**: 410.39 MB · **Sloupců**: 87 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(30) | ANO |  |  |
| 5 | `NazevListu` | nvarchar(40) | NE | ('') |  |
| 6 | `PosExcel` | int | ANO |  |  |
| 7 | `Pos` | int | ANO |  | Pozice radku v puvodni kalkulaci |
| 8 | `Bezeichnung` | nvarchar(160) | ANO |  | Nazev polozky v puvodni kalkulaci |
| 9 | `RegCisKalk` | nvarchar(30) | ANO |  |  |
| 10 | `Vyrobce` | nvarchar(30) | ANO |  |  |
| 11 | `PocetKusu` | numeric(12,2) | ANO |  |  |
| 12 | `PribalKusy` | numeric(6,2) | ANO |  |  |
| 13 | `Opce` | nchar(1) | ANO |  |  |
| 14 | `JCenaEUR` | numeric(8,2) | ANO | ((0.0)) |  |
| 15 | `RabatP` | numeric(6,2) | ANO |  |  |
| 16 | `RabatN` | numeric(6,2) | ANO |  |  |
| 17 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 18 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 19 | `PoznamkaVP` | nvarchar(1000) | ANO |  |  |
| 20 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 21 | `Beistellung` | nvarchar(3) | ANO |  |  |
| 22 | `Hmotnost` | numeric(5,2) | ANO |  |  |
| 23 | `JeVKM` | bit | ANO |  |  |
| 24 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 25 | `KontrolaSklad` | smallint | ANO |  | 0 .. sklad.karta neexistuje, 1.. sklad karta existuje |
| 26 | `KontrolaCenik` | smallint | ANO |  | 0..cenik neexistuje,1 .. cenik existruje,2..cenik existuje a je v NC... |
| 27 | `PC_Cenik` | numeric(18,4) | ANO |  |  |
| 28 | `NC_Cenik` | numeric(18,4) | ANO |  |  |
| 29 | `NC_Posledni` | numeric(18,2) | ANO |  |  |
| 30 | `ARB_Sazba` | numeric(5,2) | ANO |  |  |
| 31 | `VKM_Sazba` | numeric(4,2) | ANO |  |  |
| 32 | `Marze` | numeric(4,2) | ANO |  |  |
| 33 | `StavGenerovaniDO` | smallint | ANO | ((0)) | 0.. není generováno,1 .. označeno k přenosu do DO, 2.. přeneseno do DO |
| 34 | `StavGenerDO_Text` | varchar(26) | NE |  |  |
| 35 | `idStavSkladu` | int | ANO |  |  |
| 36 | `Color` | nvarchar(MAX) | ANO |  |  |
| 37 | `ExcelColor` | nvarchar(MAX) | ANO |  |  |
| 38 | `idPuvPolKalk` | int | ANO |  | odkaz na původní položku kalkulace v případě storna |
| 39 | `SumaKusu` | numeric(18,2) | ANO |  |  |
| 40 | `SkladDispozice` | numeric(18,2) | ANO |  |  |
| 41 | `Objednano` | numeric(18,2) | ANO |  |  |
| 42 | `Vydano` | numeric(18,2) | ANO |  |  |
| 43 | `VydanoVKM` | numeric(18,2) | ANO |  |  |
| 44 | `ZbyvaResit` | numeric(18,2) | ANO |  |  |
| 45 | `Objednej` | numeric(18,2) | ANO |  |  |
| 46 | `Vydej` | numeric(18,2) | ANO |  |  |
| 47 | `VydejVKM` | numeric(18,2) | ANO |  |  |
| 48 | `ZpetNaSklad` | numeric(18,2) | ANO |  |  |
| 49 | `CisloZakazky` | nchar(20) | ANO |  |  |
| 50 | `ObjednatDo` | date | ANO |  |  |
| 51 | `Autor` | nvarchar(128) | NE |  |  |
| 52 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 53 | `DatZmeny` | datetime | ANO |  |  |
| 54 | `SkutecNaklady` | numeric(18,2) | ANO |  |  |
| 55 | `DatumKalkSkutecNakl` | datetime | ANO |  |  |
| 56 | `SkutecMnozstvi` | numeric(18,2) | ANO |  |  |
| 57 | `IndPoptavka` | bit | ANO |  |  |
| 58 | `VazbaPoptavka` | int | ANO |  |  |
| 59 | `IndObjVydRucne` | bit | NE | ((0)) |  |
| 60 | `CisloVerze` | int | NE |  |  |
| 61 | `Platnost` | bit | NE |  |  |
| 62 | `DatPoslZmeny` | datetime | NE | (getdate()) |  |
| 63 | `Dodavatel` | int | ANO |  |  |
| 64 | `IdNahrada` | int | ANO |  |  |
| 65 | `Kontr_JCenaEUR` | numeric(8,2) | ANO |  |  |
| 66 | `Kontr_RabatP` | numeric(6,2) | ANO |  |  |
| 67 | `Kontr_RabatN` | numeric(6,2) | ANO |  |  |
| 68 | `Kontr_K_ARB` | numeric(5,2) | ANO |  |  |
| 69 | `Kontr_K_VKM` | numeric(5,2) | ANO |  |  |
| 70 | `Kontr_JeVKM` | bit | ANO |  |  |
| 71 | `InfoObjStav` | nvarchar(200) | ANO |  |  |
| 72 | `ObjNaSklad` | numeric(18,2) | ANO |  |  |
| 73 | `SdruzObj` | bit | ANO |  |  |
| 74 | `SdruzObjOtevrena` | nvarchar(100) | ANO |  |  |
| 75 | `VezmiZObjSklad` | numeric(18,2) | ANO |  |  |
| 76 | `IDPrefObj` | int | ANO |  |  |
| 81 | `MnZapujcenoOdZak` | numeric(18,2) | ANO |  |  |
| 82 | `Zapujcil` | nvarchar(128) | ANO |  |  |
| 83 | `DatZapujceni` | datetime | ANO |  |  |
| 84 | `MnVracenoZak` | numeric(18,2) | ANO |  |  |
| 85 | `Vratil` | nvarchar(128) | ANO |  |  |
| 86 | `DatVraceni` | datetime | ANO |  |  |
| 87 | `PoznamkaZapujceno` | nvarchar(1000) | ANO |  |  |
| 88 | `TypArchivace` | nvarchar(1) | ANO |  |  |
| 89 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 90 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 91 | `IDGenPolozky` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkulacePolozky_II` (CLUSTERED) — `ID, CisloVerze`
