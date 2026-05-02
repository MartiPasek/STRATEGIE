# EC_DopravaZakaznikovi_Archiv

**Schema**: dbo · **Cluster**: Other · **Rows**: 24,100 · **Size**: 22.83 MB · **Sloupců**: 58 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDopravy` | int | ANO |  |  |
| 3 | `Oznaceni` | nvarchar(10) | ANO |  |  |
| 4 | `ObsahDodavky` | nchar(100) | ANO |  |  |
| 5 | `Blokovano` | bit | ANO |  |  |
| 6 | `SeznamResitelu` | nvarchar(255) | ANO |  |  |
| 7 | `Objednava` | nvarchar(100) | ANO |  |  |
| 8 | `DatumVykladkyOd` | datetime | ANO |  |  |
| 9 | `DatumVykladkyDo` | datetime | ANO |  |  |
| 10 | `FinalniDatumVykladky` | bit | ANO |  |  |
| 11 | `AdresaDoruceni` | nvarchar(MAX) | ANO |  |  |
| 12 | `KontaktJmeno` | nvarchar(100) | ANO |  |  |
| 13 | `KontaktTelefon` | nvarchar(20) | ANO |  |  |
| 14 | `HmotnostPriblizna` | numeric(6,1) | ANO |  |  |
| 15 | `PozadavekNaZvazeni` | bit | ANO |  |  |
| 16 | `HmotnostZvazena` | numeric(6,1) | ANO |  |  |
| 17 | `PozadavkyNaDopravu` | nvarchar(255) | ANO |  |  |
| 18 | `InfoProDopravce` | nvarchar(MAX) | ANO |  |  |
| 19 | `Zeme` | nvarchar(200) | ANO |  |  |
| 20 | `Misto` | nvarchar(200) | ANO |  |  |
| 21 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 22 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 23 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 24 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 25 | `DatZmeny` | datetime | ANO |  |  |
| 26 | `Dat` | nchar(10) | ANO |  |  |
| 27 | `DokoncitVyrobuDo` | datetime | ANO |  |  |
| 28 | `ZkouskyDatum` | datetime | ANO |  |  |
| 29 | `NaPalete` | nvarchar(100) | ANO |  |  |
| 30 | `Spedici` | bit | ANO |  |  |
| 31 | `Jerab` | bit | ANO |  |  |
| 32 | `AutoSCelem` | bit | ANO |  |  |
| 33 | `BokemZadem` | bit | ANO |  |  |
| 34 | `DatumOdvozu` | datetime | ANO |  |  |
| 35 | `DopravceKontakt` | nvarchar(100) | ANO |  |  |
| 36 | `DatumCasOdvozuOdDleZkusebna` | datetime | ANO |  |  |
| 37 | `FinalniDatumOdvozu` | bit | ANO |  |  |
| 38 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 39 | `PocetColi` | int | ANO |  |  |
| 40 | `PrijemceDopravy` | int | ANO |  |  |
| 41 | `DokoncitVyrobuDo_Zmenil` | nvarchar(126) | ANO |  |  |
| 42 | `DatumOdvezeni` | datetime | ANO |  |  |
| 43 | `OdvozPotvrdil` | int | ANO |  |  |
| 44 | `AdresaDoruceniTisk` | nvarchar(MAX) | ANO |  |  |
| 45 | `NazevZakazkyTisk` | nvarchar(MAX) | ANO |  |  |
| 46 | `StavObjednani` | int | ANO |  | 0 = Neobjednáno, 1= v přípravě, 2 = objednáno |
| 47 | `PoznamkaLogistika` | nvarchar(4000) | ANO |  |  |
| 48 | `BylaZmena` | bit | ANO |  |  |
| 49 | `Archivoval` | nvarchar(128) | ANO | (suser_sname()) |  |
| 50 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 51 | `Zmeneno` | nvarchar(4000) | ANO |  |  |
| 52 | `DatDodaniDO_FIX` | bit | ANO | ((0)) |  |
| 53 | `Spedice_HodnotaZbo` | numeric(19,6) | ANO | ((0)) |  |
| 54 | `Spedice_HodnotaZboMena` | nvarchar(3) | ANO |  |  |
| 55 | `DopravceKontakt_CisloOrg` | int | ANO |  |  |
| 56 | `CenaKalkulovana` | numeric(19,6) | ANO | ((0)) |  |
| 57 | `JCbezDaniKC_proVOBJ` | numeric(19,6) | ANO | ((0)) |  |
| 58 | `CenaPojisteni_proVOBJ1` | numeric(19,6) | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_DopravaZakaznikovi_Archiv` (CLUSTERED) — `ID`
