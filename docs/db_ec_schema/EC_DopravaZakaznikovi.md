# EC_DopravaZakaznikovi

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,526 · **Size**: 4.70 MB · **Sloupců**: 65 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Oznaceni` | nvarchar(10) | ANO |  |  |
| 3 | `ObsahDodavky` | nchar(100) | ANO |  |  |
| 4 | `Blokovano` | bit | ANO |  |  |
| 5 | `SeznamResitelu` | nvarchar(255) | ANO |  |  |
| 6 | `Objednava` | nvarchar(100) | ANO |  |  |
| 7 | `DatumVykladkyOd` | datetime | ANO |  |  |
| 8 | `DatumVykladkyDo` | datetime | ANO |  |  |
| 9 | `FinalniDatumVykladky` | bit | ANO |  |  |
| 10 | `AdresaDoruceni` | nvarchar(MAX) | ANO |  |  |
| 11 | `KontaktJmeno` | nvarchar(100) | ANO |  |  |
| 12 | `KontaktTelefon` | nvarchar(20) | ANO |  |  |
| 13 | `HmotnostPriblizna` | numeric(6,1) | ANO |  |  |
| 14 | `PozadavekNaZvazeni` | bit | ANO | ((1)) |  |
| 15 | `HmotnostZvazena` | numeric(6,1) | ANO |  |  |
| 16 | `PozadavkyNaDopravu` | nvarchar(255) | ANO |  |  |
| 17 | `InfoProDopravce` | nvarchar(MAX) | ANO |  |  |
| 18 | `Zeme` | nvarchar(200) | ANO |  |  |
| 19 | `Misto` | nvarchar(200) | ANO |  |  |
| 20 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 21 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 22 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 23 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 24 | `DatZmeny` | datetime | ANO |  |  |
| 25 | `Dat` | nchar(10) | ANO |  |  |
| 26 | `DokoncitVyrobuDo` | datetime | ANO |  |  |
| 27 | `ZkouskyDatum` | datetime | ANO |  |  |
| 28 | `NaPalete` | nvarchar(100) | ANO |  |  |
| 29 | `Spedici` | bit | ANO |  |  |
| 30 | `Jerab` | bit | ANO |  |  |
| 31 | `AutoSCelem` | bit | ANO |  |  |
| 32 | `BokemZadem` | bit | ANO |  |  |
| 33 | `DatumOdvozu` | datetime | ANO |  |  |
| 34 | `DopravceKontakt` | nvarchar(100) | ANO |  |  |
| 35 | `DatumCasOdvozuOdDleZkusebna` | datetime | ANO |  |  |
| 36 | `FinalniDatumOdvozu` | bit | ANO |  |  |
| 37 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 38 | `PocetColi` | int | ANO |  |  |
| 39 | `PrijemceDopravy` | int | ANO |  |  |
| 40 | `DokoncitVyrobuDo_Zmenil` | nvarchar(126) | ANO |  |  |
| 41 | `DatumOdvezeni` | datetime | ANO |  |  |
| 42 | `OdvozPotvrdil` | int | ANO |  |  |
| 43 | `AdresaDoruceniTisk` | nvarchar(MAX) | ANO |  |  |
| 44 | `NazevZakazkyTisk` | nvarchar(MAX) | ANO |  |  |
| 45 | `StavObjednani` | int | ANO | ((0)) | 0 = Neobjednáno, 1= v přípravě, 2 = objednáno |
| 46 | `PoznamkaLogistika` | nvarchar(4000) | ANO |  |  |
| 47 | `BylaZmena` | bit | ANO | ((0)) |  |
| 48 | `Zpracovava` | int | ANO |  |  |
| 49 | `DatDodaniDO_FIX` | bit | ANO | ((0)) |  |
| 50 | `Spedice_HodnotaZbo` | numeric(19,6) | ANO | ((0)) |  |
| 51 | `Spedice_HodnotaZboMena` | nvarchar(3) | ANO |  |  |
| 52 | `DopravceKontakt_CisloOrg` | int | ANO |  |  |
| 53 | `ZpatecniDoprava` | bit | ANO | ((0)) |  |
| 54 | `ID_VOBJ` | int | ANO |  |  |
| 55 | `BylaZmenaVyroba` | bit | ANO | ((0)) |  |
| 56 | `AdresaDoruceni_bak` | nvarchar(MAX) | ANO |  |  |
| 57 | `InfoProDopravce_bak` | nvarchar(MAX) | ANO |  |  |
| 58 | `FinalniDatumVykladky_OpenD` | bit | ANO | ((0)) |  |
| 59 | `FinalniDatumVykladky_CloseD` | bit | ANO | ((0)) |  |
| 60 | `CenaKalkulovana` | numeric(19,6) | ANO | ((0)) |  |
| 61 | `JCbezDaniKC_proVOBJ` | numeric(19,6) | ANO | ((0)) |  |
| 62 | `SeznamZakazek_VOBJ` | nvarchar(200) | ANO |  |  |
| 63 | `TypDopravy` | int | ANO | ((3)) |  |
| 67 | `DatumTiskuCMR` | datetime | ANO |  |  |
| 68 | `CenaPojisteni_proVOBJ1` | numeric(19,6) | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_DopravaZakaznikovi` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_DopravaZakaznikovi_CisloZakazky` (NONCLUSTERED) — `CisloZakazky`
