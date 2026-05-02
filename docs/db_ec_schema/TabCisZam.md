# TabCisZam

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 428 · **Size**: 0.81 MB · **Sloupců**: 171 · **FK**: 14 · **Indexů**: 5

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | NE |  |  |
| 3 | `Jmeno` | nvarchar(100) | NE | ('') |  |
| 4 | `Prijmeni` | nvarchar(100) | NE | ('') |  |
| 5 | `RodnePrijmeni` | nvarchar(100) | NE | ('') |  |
| 6 | `TitulPred` | nvarchar(100) | NE | ('') |  |
| 7 | `TitulZa` | nvarchar(100) | NE | ('') |  |
| 8 | `LoginId` | nvarchar(128) | NE | ('') |  |
| 9 | `DatumNarozeni` | datetime | ANO |  |  |
| 10 | `RodneCislo` | nvarchar(11) | NE | ('') |  |
| 11 | `Pohlavi` | smallint | NE | ((0)) |  |
| 12 | `MistoNarozeni` | nvarchar(100) | NE | ('') |  |
| 13 | `AdrTrvUlice` | nvarchar(100) | NE | ('') |  |
| 14 | `AdrTrvOrCislo` | nvarchar(15) | NE | ('') |  |
| 15 | `AdrTrvPopCislo` | nvarchar(15) | NE | ('') |  |
| 16 | `AdrTrvMisto` | nvarchar(100) | NE | ('') |  |
| 17 | `AdrTrvPSC` | nvarchar(10) | NE | ('') |  |
| 18 | `AdrTrvZeme` | nvarchar(3) | ANO |  |  |
| 19 | `AdrPrechUlice` | nvarchar(100) | NE | ('') |  |
| 20 | `AdrPrechOrCislo` | nvarchar(15) | NE | ('') |  |
| 21 | `AdrPrechPopCislo` | nvarchar(15) | NE | ('') |  |
| 22 | `AdrPrechMisto` | nvarchar(100) | NE | ('') |  |
| 23 | `AdrPrechPSC` | nvarchar(10) | NE | ('') |  |
| 24 | `AdrPrechZeme` | nvarchar(3) | ANO |  |  |
| 25 | `StatniPrislus` | nvarchar(3) | ANO |  |  |
| 26 | `Narodnost` | nvarchar(100) | NE | ('') |  |
| 27 | `RodinnyStav` | smallint | NE | ((0)) |  |
| 28 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 29 | `NakladovyOkruh` | nvarchar(15) | ANO |  |  |
| 30 | `Zakazka` | nvarchar(15) | ANO |  |  |
| 31 | `CisloOP` | nvarchar(15) | NE | ('') |  |
| 32 | `PlatnostOP` | datetime | ANO |  |  |
| 33 | `CisloPasu` | nvarchar(20) | NE | ('') |  |
| 34 | `PlatnostPasu` | datetime | ANO |  |  |
| 35 | `CisloRP` | nvarchar(20) | NE | ('') |  |
| 36 | `SkupinaRP` | nvarchar(55) | NE | ('') |  |
| 37 | `Status` | tinyint | NE | ((0)) |  |
| 38 | `IdObdobi` | int | NE | ((0)) |  |
| 39 | `Obrazek` | varbinary(MAX) | ANO |  |  |
| 40 | `Alias` | nvarchar(15) | NE | ('') |  |
| 41 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 42 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 43 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 44 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 45 | `DatZmeny` | datetime | ANO |  |  |
| 46 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 50 | `DatumNarozeni_D` | int | ANO |  |  |
| 51 | `DatumNarozeni_M` | int | ANO |  |  |
| 52 | `DatumNarozeni_Y` | int | ANO |  |  |
| 53 | `DatumNarozeni_Q` | int | ANO |  |  |
| 54 | `DatumNarozeni_W` | int | ANO |  |  |
| 55 | `DatumNarozeni_X` | datetime | ANO |  |  |
| 58 | `PlatnostOP_D` | int | ANO |  |  |
| 59 | `PlatnostOP_M` | int | ANO |  |  |
| 60 | `PlatnostOP_Y` | int | ANO |  |  |
| 61 | `PlatnostOP_Q` | int | ANO |  |  |
| 62 | `PlatnostOP_W` | int | ANO |  |  |
| 63 | `PlatnostOP_X` | datetime | ANO |  |  |
| 64 | `PlatnostPasu_D` | int | ANO |  |  |
| 65 | `PlatnostPasu_M` | int | ANO |  |  |
| 66 | `PlatnostPasu_Y` | int | ANO |  |  |
| 67 | `PlatnostPasu_Q` | int | ANO |  |  |
| 68 | `PlatnostPasu_W` | int | ANO |  |  |
| 69 | `PlatnostPasu_X` | datetime | ANO |  |  |
| 71 | `DatPorizeni_D` | int | ANO |  |  |
| 72 | `DatPorizeni_M` | int | ANO |  |  |
| 73 | `DatPorizeni_Y` | int | ANO |  |  |
| 74 | `DatPorizeni_Q` | int | ANO |  |  |
| 75 | `DatPorizeni_W` | int | ANO |  |  |
| 76 | `DatPorizeni_X` | datetime | ANO |  |  |
| 77 | `DatZmeny_D` | int | ANO |  |  |
| 78 | `DatZmeny_M` | int | ANO |  |  |
| 79 | `DatZmeny_Y` | int | ANO |  |  |
| 80 | `DatZmeny_Q` | int | ANO |  |  |
| 81 | `DatZmeny_W` | int | ANO |  |  |
| 82 | `DatZmeny_X` | datetime | ANO |  |  |
| 83 | `SSN` | nvarchar(24) | NE | ('') |  |
| 84 | `PovoleniKPobytu` | nvarchar(30) | NE | ('') |  |
| 86 | `HesloPDF` | nvarchar(20) | NE | ('') |  |
| 98 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 99 | `PrijmeniJmenoTituly` | nvarchar(403) | ANO |  |  |
| 100 | `CisloJmenoTituly` | nvarchar(410) | ANO |  |  |
| 101 | `AdrTrvUliceSCisly` | nvarchar(132) | NE |  |  |
| 102 | `AdrPrechUliceSCisly` | nvarchar(132) | NE |  |  |
| 103 | `HesloPokladni` | nvarchar(200) | NE | ('') |  |
| 104 | `AdrKontJmeno` | nvarchar(100) | NE | ('') |  |
| 105 | `AdrKontPrijmeni` | nvarchar(100) | NE | ('') |  |
| 106 | `AdrKontUlice` | nvarchar(100) | NE | ('') |  |
| 107 | `AdrKontOrCislo` | nvarchar(15) | NE | ('') |  |
| 108 | `AdrKontPopCislo` | nvarchar(15) | NE | ('') |  |
| 109 | `AdrKontMisto` | nvarchar(100) | NE | ('') |  |
| 110 | `AdrKontPSC` | nvarchar(10) | NE | ('') |  |
| 111 | `AdrKontZeme` | nvarchar(3) | ANO |  |  |
| 112 | `RodneCisloBezLomitka` | nvarchar(11) | ANO |  |  |
| 115 | `AdrKontPrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 116 | `AdrKontUliceSCisly` | nvarchar(132) | NE |  |  |
| 117 | `VyraditZPrehledu` | bit | NE | ((0)) |  |
| 118 | `PasVydal` | nvarchar(40) | NE | ('') |  |
| 120 | `Obrazek_DatLen` | bigint | NE |  |  |
| 121 | `IDZdrojOsUdaju` | int | ANO |  |  |
| 122 | `JeNovaVetaEditor` | bit | NE | ((0)) |  |
| 123 | `OmezeniZpracOU` | bit | NE | ((0)) |  |
| 125 | `AdrTrvOkres` | nvarchar(15) | ANO |  |  |
| 126 | `PasVydal_Zeme` | nvarchar(3) | ANO |  |  |
| 127 | `RC_Cizinec` | nvarchar(24) | NE | ('') |  |
| 128 | `PovoleniKPobytuOd` | datetime | ANO |  |  |
| 129 | `PovoleniKPobytuDo` | datetime | ANO |  |  |
| 130 | `UcelPobytu` | nvarchar(255) | NE | ('') |  |
| 131 | `SSN_RC` | nvarchar(24) | ANO |  |  |
| 132 | `SSN_RC_BezLomitka` | nvarchar(24) | ANO |  |  |
| 133 | `PovoleniKPobytuOd_D` | int | ANO |  |  |
| 134 | `PovoleniKPobytuOd_M` | int | ANO |  |  |
| 135 | `PovoleniKPobytuOd_Y` | int | ANO |  |  |
| 136 | `PovoleniKPobytuOd_Q` | int | ANO |  |  |
| 137 | `PovoleniKPobytuOd_W` | int | ANO |  |  |
| 138 | `PovoleniKPobytuOd_X` | datetime | ANO |  |  |
| 139 | `PovoleniKPobytuDo_D` | int | ANO |  |  |
| 140 | `PovoleniKPobytuDo_M` | int | ANO |  |  |
| 141 | `PovoleniKPobytuDo_Y` | int | ANO |  |  |
| 142 | `PovoleniKPobytuDo_Q` | int | ANO |  |  |
| 143 | `PovoleniKPobytuDo_W` | int | ANO |  |  |
| 144 | `PovoleniKPobytuDo_X` | datetime | ANO |  |  |
| 145 | `RC_SSN_C` | nvarchar(24) | ANO |  |  |
| 146 | `RC_SSN_C_BezLomitka` | nvarchar(24) | ANO |  |  |
| 147 | `RC_C_RC` | nvarchar(24) | ANO |  |  |
| 148 | `RC_C_RC_BezLomitka` | nvarchar(24) | ANO |  |  |
| 149 | `IdVTypUcelPobytu_DuvodPovolSK` | int | ANO |  |  |
| 150 | `ProfeseAPI` | nvarchar(60) | NE | ('') |  |
| 151 | `AVAReferenceID` | nvarchar(40) | NE | (CONVERT([nvarchar](36),CONVERT([uniqueidentifier],newid()))) |  |
| 152 | `AVAExternalID` | nvarchar(255) | NE | ('') |  |
| 153 | `AVAOutputFlag` | tinyint | NE | ((0)) |  |
| 154 | `AVASentDate` | datetime | ANO |  |  |
| 156 | `AVASentDate_D` | int | ANO |  |  |
| 157 | `AVASentDate_M` | int | ANO |  |  |
| 158 | `AVASentDate_Y` | int | ANO |  |  |
| 159 | `AVASentDate_Q` | int | ANO |  |  |
| 160 | `AVASentDate_W` | int | ANO |  |  |
| 161 | `AVASentDate_X` | datetime | ANO |  |  |
| 162 | `Ciz_Doklad_Typ` | smallint | NE | ((0)) |  |
| 163 | `Ciz_Doklad_Cislo` | nvarchar(20) | NE | ('') |  |
| 164 | `Ciz_Doklad_Vydal` | nvarchar(100) | NE | ('') |  |
| 165 | `Ciz_Doklad_Vydal_Zeme` | nvarchar(3) | ANO |  |  |
| 166 | `Ciz_Doklad_Typ_Kod` | nvarchar(2) | ANO |  |  |
| 167 | `StatNarozeni` | nvarchar(3) | ANO |  |  |
| 168 | `PlatnostRP` | datetime | ANO |  |  |
| 169 | `DochazkaChip` | nvarchar(128) | ANO |  |  |
| 170 | `OsobniIC` | nvarchar(10) | NE | ('') |  |
| 171 | `AdrRez_Ulice` | nvarchar(100) | NE | ('') |  |
| 172 | `AdrRez_OrCislo` | nvarchar(12) | NE | ('') |  |
| 173 | `AdrRez_PopCislo` | nvarchar(12) | NE | ('') |  |
| 174 | `AdrRez_Misto` | nvarchar(100) | NE | ('') |  |
| 175 | `AdrRez_PSC` | nvarchar(10) | NE | ('') |  |
| 176 | `AdrRez_Zeme` | nvarchar(3) | ANO |  |  |
| 177 | `KodZdrPojAVA` | nvarchar(40) | ANO |  |  |
| 178 | `CisloPojistenceAVA` | nvarchar(15) | NE | ('') |  |
| 179 | `AdrTrvAVAReferenceID` | nvarchar(40) | NE | (CONVERT([nvarchar](36),CONVERT([uniqueidentifier],newid()))) |  |
| 180 | `AdrPrechAVAReferenceID` | nvarchar(40) | NE | (CONVERT([nvarchar](36),CONVERT([uniqueidentifier],newid()))) |  |
| 181 | `AVAReceivedDate` | datetime | ANO |  |  |
| 182 | `Obrazek_BGJ` | nvarchar(6) | ANO |  |  |
| 183 | `PlatnostRP_D` | int | ANO |  |  |
| 184 | `PlatnostRP_M` | int | ANO |  |  |
| 185 | `PlatnostRP_Y` | int | ANO |  |  |
| 186 | `PlatnostRP_Q` | int | ANO |  |  |
| 187 | `PlatnostRP_W` | int | ANO |  |  |
| 188 | `PlatnostRP_X` | datetime | ANO |  |  |
| 189 | `AVAReceivedDate_D` | int | ANO |  |  |
| 190 | `AVAReceivedDate_M` | int | ANO |  |  |
| 191 | `AVAReceivedDate_Y` | int | ANO |  |  |
| 192 | `AVAReceivedDate_Q` | int | ANO |  |  |
| 193 | `AVAReceivedDate_W` | int | ANO |  |  |
| 194 | `AVAReceivedDate_X` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `AdrTrvOkres` → `TabRegion`.`Cislo` _(constraint: `FK__TabCisZam__AdrTrvOkres`)_
- `PasVydal_Zeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__PasVydal_Zeme`)_
- `Stredisko` → `TabStrom`.`Cislo` _(constraint: `FK__TabCisZam__Stredisko`)_
- `Zakazka` → `TabZakazka`.`CisloZakazky` _(constraint: `FK__TabCisZam__Zakazka`)_
- `IdVTypUcelPobytu_DuvodPovolSK` → `TabVTypUcelPobytuDuvodPovolSK`.`ID` _(constraint: `FK__TabCisZam__IdVTypUcelPobytu_DuvodPovolSK`)_
- `Ciz_Doklad_Vydal_Zeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__Ciz_Doklad_Vydal_Zeme`)_
- `AdrRez_Zeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__AdrRez_Zeme`)_
- `StatNarozeni` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__StatNarozeni`)_
- `StatniPrislus` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__StatniPrislus`)_
- `AdrPrechZeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__AdrPrechZeme`)_
- `AdrTrvZeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__AdrTrvZeme`)_
- `IDZdrojOsUdaju` → `TabZdrojeOsUdaju`.`ID` _(constraint: `FK__TabCisZam__IDZdrojOsUdaju`)_
- `AdrKontZeme` → `TabZeme`.`ISOKod` _(constraint: `FK__TabCisZam__AdrKontZeme`)_
- `NakladovyOkruh` → `TabNakladovyOkruh`.`Cislo` _(constraint: `FK__TabCisZam__NakladovyOkruh`)_

## Indexy

- **PK** `PK__TabCisZam__ID` (CLUSTERED) — `ID`
- **UNIQUE** `UQ__TabCisZam__Cislo` (NONCLUSTERED) — `Cislo`
- **UNIQUE** `UQ__TabCisZam__AVAReferenceID` (NONCLUSTERED) — `AVAReferenceID`
- **INDEX** `IX__TabCisZam__AVAExternalID` (NONCLUSTERED) — `AVAExternalID`
- **INDEX** `IX__TabCisZam__LoginId` (NONCLUSTERED) — `LoginId`
