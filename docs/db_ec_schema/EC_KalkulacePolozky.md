# EC_KalkulacePolozky

**Schema**: dbo · **Cluster**: Production · **Rows**: 235,637 · **Size**: 228.77 MB · **Sloupců**: 141 · **FK**: 0 · **Indexů**: 6

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `IDKmenZbozi` | int | ANO |  |  |
| 4 | `IDStavSkladu` | int | ANO |  |  |
| 5 | `ID_Skupina` | int | ANO |  |  |
| 6 | `IDCenik` | int | ANO |  |  |
| 7 | `IDNahrada` | int | ANO |  |  |
| 8 | `idPuvPolKalk` | int | ANO |  | odkaz na původní položku kalkulace v případě storna |
| 9 | `RegCis` | nvarchar(30) | ANO |  |  |
| 10 | `NazevListu` | nvarchar(40) | NE | ('') |  |
| 11 | `PosExcel` | int | ANO |  |  |
| 12 | `Pos` | int | ANO |  | Pozice radku v puvodni kalkulaci |
| 13 | `Bezeichnung` | nvarchar(160) | ANO |  | Nazev polozky v puvodni kalkulaci |
| 14 | `BezeichnungComment` | nvarchar(MAX) | ANO |  |  |
| 15 | `RegCisKalk` | nvarchar(30) | ANO |  |  |
| 16 | `Vyrobce` | nvarchar(30) | ANO |  |  |
| 17 | `PocetKusu` | numeric(12,2) | ANO |  |  |
| 18 | `PribalKusy` | numeric(6,2) | ANO |  |  |
| 19 | `Opce` | nchar(1) | ANO |  |  |
| 20 | `JCenaEUR` | numeric(8,2) | ANO |  |  |
| 21 | `RabatP` | numeric(6,2) | ANO |  |  |
| 22 | `RabatN` | numeric(6,2) | ANO |  |  |
| 23 | `K_ARB` | numeric(5,2) | ANO |  |  |
| 24 | `K_VKM` | numeric(5,2) | ANO |  |  |
| 25 | `PoznamkaVP` | nvarchar(1000) | ANO |  |  |
| 26 | `PoznamkaNakup` | nvarchar(128) | ANO |  |  |
| 27 | `Beistellung` | nvarchar(3) | ANO |  |  |
| 28 | `Hmotnost` | numeric(19,6) | ANO |  |  |
| 29 | `JeVKM` | bit | ANO |  |  |
| 30 | `GesamtPreis1` | numeric(33,10) | ANO |  |  |
| 31 | `KontrolaSklad` | smallint | ANO |  | 0 .. sklad.karta neexistuje, 1.. sklad karta existuje |
| 32 | `KontrolaCenik` | smallint | ANO |  | 0..cenik neexistuje,1 .. cenik existruje,2..cenik existuje a je v NC... |
| 33 | `PC_Cenik` | numeric(18,2) | ANO |  |  |
| 34 | `NC_Cenik` | numeric(18,2) | ANO |  |  |
| 35 | `NC_Posledni` | numeric(18,2) | ANO |  |  |
| 36 | `EinheitpreisPoSleve` | numeric(29,12) | ANO |  |  |
| 37 | `GesamtPreis` | numeric(37,12) | ANO |  |  |
| 38 | `Arbeitstunden` | numeric(18,4) | ANO |  |  |
| 39 | `VKM` | numeric(10,4) | ANO |  |  |
| 40 | `Arbeit` | numeric(11,4) | ANO |  |  |
| 41 | `Einbaupreis` | numeric(38,11) | ANO |  |  |
| 42 | `Hmotnost_Celkem` | numeric(32,8) | ANO |  |  |
| 43 | `ARB_Sazba` | numeric(5,2) | ANO |  |  |
| 44 | `VKM_Sazba` | numeric(4,2) | ANO |  |  |
| 45 | `Marze` | numeric(4,2) | ANO |  |  |
| 46 | `StavGenerovaniDO` | smallint | ANO | ((0)) | 0.. není generováno,1 .. označeno k přenosu do DO, 2.. přeneseno do DO |
| 47 | `Color` | nvarchar(MAX) | ANO |  |  |
| 48 | `ExcelColor` | nvarchar(MAX) | ANO |  |  |
| 49 | `ExcelNazevListu` | nvarchar(40) | ANO |  |  |
| 50 | `Bei` | int | ANO |  | Beistellung |
| 51 | `SumaKusu` | numeric(18,2) | ANO |  |  |
| 52 | `SkladDispozice` | numeric(18,2) | ANO |  |  |
| 53 | `Objednano` | numeric(18,2) | ANO |  |  |
| 54 | `Vydano` | numeric(18,2) | ANO |  |  |
| 55 | `VydanoVKM` | numeric(18,2) | ANO |  |  |
| 56 | `ZbyvaResit` | numeric(18,2) | ANO |  |  |
| 57 | `Objednej` | numeric(18,2) | ANO |  |  |
| 58 | `Vydej` | numeric(18,2) | ANO |  |  |
| 59 | `VydejVKM` | numeric(18,2) | ANO |  |  |
| 60 | `ZpetNaSklad` | numeric(18,2) | ANO |  |  |
| 61 | `VracenoZpet` | numeric(18,2) | ANO |  |  |
| 62 | `VydanoNavic` | numeric(18,2) | ANO |  |  |
| 63 | `SumaObjednano` | numeric(18,2) | ANO |  |  |
| 64 | `SumaVydano` | numeric(18,2) | ANO |  |  |
| 65 | `SumaObjednej` | numeric(18,2) | ANO |  |  |
| 66 | `SumaVydej` | numeric(18,2) | ANO |  |  |
| 67 | `StavSkladDispozice` | nvarchar(30) | ANO |  |  |
| 68 | `CisloZakazky` | nchar(20) | ANO |  |  |
| 69 | `ObjednatDo` | date | ANO |  |  |
| 70 | `SkutecNaklady` | numeric(18,2) | ANO |  |  |
| 71 | `DatumKalkSkutecNakl` | datetime | ANO |  |  |
| 72 | `SkutecMnozstvi` | numeric(18,2) | ANO |  |  |
| 73 | `IndPoptavka` | bit | ANO |  |  |
| 74 | `VazbaPoptavka` | int | ANO |  |  |
| 75 | `IndObjVydRucne` | bit | NE | ((0)) |  |
| 76 | `JeDodavatel` | bit | NE | ((0)) |  |
| 77 | `Dodavatel` | int | ANO |  |  |
| 78 | `Kontr_JCenaEUR` | numeric(8,2) | ANO |  |  |
| 79 | `Kontr_RabatP` | numeric(6,2) | ANO |  |  |
| 80 | `Kontr_RabatN` | numeric(6,2) | ANO |  |  |
| 81 | `Kontr_K_ARB` | numeric(5,2) | ANO |  |  |
| 82 | `Kontr_K_VKM` | numeric(5,2) | ANO |  |  |
| 83 | `Kontr_JeVKM` | bit | ANO |  |  |
| 84 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 85 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 86 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 87 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 88 | `IndArchiv` | bit | ANO |  |  |
| 89 | `DatPoslZmenyArchiv` | datetime | ANO |  |  |
| 90 | `InfoObjStav` | nvarchar(200) | ANO |  |  |
| 91 | `ObjNaSklad` | numeric(18,2) | ANO |  |  |
| 92 | `SdruzObj` | bit | ANO |  |  |
| 93 | `SdruzObjOtevrena` | nvarchar(100) | ANO |  |  |
| 94 | `VezmiZObjSklad` | numeric(18,2) | ANO |  |  |
| 95 | `IDCenikObjVazba` | int | ANO |  |  |
| 96 | `TextDoObj` | nvarchar(200) | ANO |  |  |
| 97 | `DruhExtPozadavku` | tinyint | ANO |  |  |
| 98 | `StatusPozadavku` | tinyint | ANO |  | ¨0,255 = Zadavani, 10 = Předáno ke zpracování, 15 = Vyřešeno skladem, 20 = Předáno nákupu, 25 = Vyřešeno nákupem, 30 = P |
| 99 | `DatSchvaleni` | datetime | ANO |  |  |
| 100 | `Schvalil` | nvarchar(128) | ANO |  |  |
| 101 | `PoznamkaPozadavku` | nvarchar(MAX) | ANO |  |  |
| 102 | `StatusPozadavkuText` | varchar(28) | ANO |  |  |
| 103 | `IDPrefObj` | int | ANO |  |  |
| 104 | `PozadDatDod` | datetime | ANO |  |  |
| 105 | `PoznamkaKontrola` | nvarchar(200) | ANO |  |  |
| 106 | `kontrolaOK` | int | NE |  |  |
| 107 | `KontrolovatVydani` | bit | ANO | ((1)) |  |
| 108 | `TiskVOBJ` | bit | ANO | ((1)) |  |
| 109 | `ZmenaKsOld` | bit | ANO |  |  |
| 110 | `BezeZmeny` | bit | ANO |  |  |
| 111 | `NeniKarta` | bit | ANO |  |  |
| 112 | `JeBEI` | bit | ANO |  |  |
| 113 | `PocetKusuArchiv` | numeric(18,2) | ANO |  |  |
| 114 | `ObjVKMRokObarvit` | bit | ANO |  |  |
| 115 | `ObjVKMRok` | numeric(18,2) | ANO |  |  |
| 116 | `MaxMnObj` | numeric(18,2) | ANO |  |  |
| 117 | `VydanoRokKs` | numeric(19,6) | ANO |  |  |
| 118 | `VydanoRokKolikrat` | int | ANO |  |  |
| 119 | `MnZapujcenoOdZak` | numeric(18,2) | ANO |  |  |
| 120 | `Zapujcil` | nvarchar(128) | ANO |  |  |
| 121 | `DatZapujceni` | datetime | ANO |  |  |
| 122 | `MnVracenoZak` | numeric(18,2) | ANO |  |  |
| 123 | `Vratil` | nvarchar(128) | ANO |  |  |
| 124 | `DatVraceni` | datetime | ANO |  |  |
| 125 | `PoznamkaZapujceno` | nvarchar(1000) | ANO |  |  |
| 126 | `ChybaCeny` | bit | NE | ((0)) |  |
| 127 | `StavGenDO15_DatZmeny` | datetime | ANO |  |  |
| 128 | `StavGenDO10_DatZmeny` | datetime | ANO |  |  |
| 129 | `StavGenDO15_Zmenil` | nvarchar(128) | ANO |  |  |
| 130 | `StavGenDO10_Zmenil` | nvarchar(128) | ANO |  |  |
| 131 | `StavGenerDO_Text` | varchar(27) | NE |  |  |
| 132 | `Einheitpreis` | numeric(24,10) | ANO |  |  |
| 133 | `CisloNabidkyDodavatele` | nvarchar(300) | ANO |  |  |
| 134 | `Sleva` | numeric(19,6) | ANO |  |  |
| 135 | `KCen_Cena` | numeric(19,6) | ANO |  |  |
| 136 | `ID_VPoptavky` | int | ANO |  |  |
| 137 | `BeiPrijato` | numeric(18,2) | ANO |  |  |
| 138 | `BeiDatPrijeti` | datetime | ANO |  |  |
| 139 | `BeiPrijal` | nvarchar(126) | ANO |  |  |
| 140 | `BeiDodano` | int | NE |  |  |
| 141 | `IDGenPolozky` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkulacePolozky` (CLUSTERED) — `ID`
- **INDEX** `EC_KalkulacePolozky_IDHlav_Arbeitstunden` (NONCLUSTERED) — `IDHlav`
- **INDEX** `IDHlav_Includes` (NONCLUSTERED) — `ID_Skupina, IDNahrada, Pos, Bezeichnung, RegCisKalk, K_ARB, K_VKM, Hmotnost, JeVKM, StavGenerovaniDO, IDHlav`
- **INDEX** `IDHlav_RegCisKalk_StavGenerovaniDO_Includes` (NONCLUSTERED) — `Vyrobce, KontrolaSklad, KontrolaCenik, IDHlav, RegCisKalk, StavGenerovaniDO`
- **INDEX** `Idx_EC_KalkulacePolozky_IDKmenZbozi` (NONCLUSTERED) — `IDKmenZbozi`
- **INDEX** `Ex_KalkulacePolozky_IDHlav_Bei_dodano` (NONCLUSTERED) — `IDHlav, Bei, BeiDodano`
