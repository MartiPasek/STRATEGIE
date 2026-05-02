# EC_Tabradekukod

**Schema**: dbo · **Cluster**: Finance · **Rows**: 302 · **Size**: 0.14 MB · **Sloupců**: 71 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDUKod` | int | NE |  |  |
| 2 | `Radek` | int | NE |  |  |
| 3 | `DruhRadku` | tinyint | NE |  |  |
| 4 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 5 | `Strana` | tinyint | NE |  |  |
| 6 | `CisloUcet` | nvarchar(30) | ANO |  |  |
| 7 | `UcetDPH` | nvarchar(30) | ANO |  |  |
| 8 | `TypParZnak` | tinyint | ANO |  |  |
| 9 | `CisloUtvar` | nvarchar(30) | ANO |  |  |
| 10 | `CisloOrg` | int | ANO |  |  |
| 11 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 12 | `CisloNakladovyOkruh` | nvarchar(15) | ANO |  |  |
| 13 | `IdVozidlo` | int | ANO |  |  |
| 14 | `CisloZam` | int | ANO |  |  |
| 15 | `Vzorec` | nvarchar(255) | NE |  |  |
| 16 | `CiziMena` | nchar(1) | NE |  |  |
| 17 | `Zaporne` | nchar(1) | NE |  |  |
| 18 | `Sklad` | tinyint | NE |  |  |
| 19 | `ZakazkaAN` | nchar(1) | NE |  |  |
| 20 | `Popis` | nvarchar(255) | NE |  |  |
| 21 | `DruhData` | tinyint | NE |  |  |
| 22 | `UplatnitDPH` | nchar(1) | NE |  |  |
| 23 | `Umisteni` | tinyint | ANO |  |  |
| 24 | `TextDoUcta` | tinyint | NE |  |  |
| 25 | `ParovaciZnak` | nvarchar(20) | NE |  |  |
| 26 | `DICOrg` | nvarchar(15) | ANO |  |  |
| 27 | `MRCisloUctu01` | nvarchar(30) | ANO |  |  |
| 28 | `IdStandardCislo` | int | ANO |  |  |
| 29 | `RecykStav` | tinyint | NE |  |  |
| 30 | `RecykUcet` | nvarchar(30) | ANO |  |  |
| 31 | `Sdruzovat` | bit | NE |  |  |
| 32 | `Autor` | nvarchar(128) | NE |  |  |
| 33 | `DatPorizeni` | datetime | NE |  |  |
| 34 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 35 | `DatZmeny` | datetime | ANO |  |  |
| 36 | `DatPorizeni_D` | int | ANO |  |  |
| 37 | `DatPorizeni_M` | int | ANO |  |  |
| 38 | `DatPorizeni_Y` | int | ANO |  |  |
| 39 | `DatPorizeni_Q` | int | ANO |  |  |
| 40 | `DatPorizeni_W` | int | ANO |  |  |
| 41 | `DatPorizeni_X` | datetime | ANO |  |  |
| 42 | `DatZmeny_D` | int | ANO |  |  |
| 43 | `DatZmeny_M` | int | ANO |  |  |
| 44 | `DatZmeny_Y` | int | ANO |  |  |
| 45 | `DatZmeny_Q` | int | ANO |  |  |
| 46 | `DatZmeny_W` | int | ANO |  |  |
| 47 | `DatZmeny_X` | datetime | ANO |  |  |
| 48 | `ZdrojData` | tinyint | NE |  |  |
| 49 | `LeasKumulace` | tinyint | NE |  |  |
| 50 | `LeasZaloha` | tinyint | NE |  |  |
| 51 | `LeasOrganizace` | tinyint | NE |  |  |
| 52 | `Id` | int | NE |  |  |
| 53 | `ICOClena` | nvarchar(20) | ANO |  |  |
| 54 | `ZdrojDSN` | tinyint | NE |  |  |
| 55 | `UcetDAL` | nvarchar(30) | ANO |  |  |
| 56 | `UcetMD` | nvarchar(30) | ANO |  |  |
| 57 | `DodrzetStranu` | bit | NE |  |  |
| 58 | `DruhDataUhrada` | tinyint | NE |  |  |
| 59 | `TypZmeny` | int | ANO |  |  |
| 60 | `PrenosOrgTran` | bit | NE |  |  |
| 61 | `RozpadUtvary` | bit | NE |  |  |
| 62 | `OrgTran` | int | ANO |  |  |
| 63 | `NakladyNV` | tinyint | NE |  |  |
| 64 | `DotahZakazka` | tinyint | NE |  |  |
| 65 | `DotahNO` | tinyint | NE |  |  |
| 66 | `DotahVozidlo` | tinyint | NE |  |  |
| 67 | `DotahZamest` | tinyint | NE |  |  |
| 68 | `IdPrijmyVydaje` | int | ANO |  |  |
| 69 | `Prepocet` | tinyint | NE |  |  |
| 70 | `MaOrganizace` | tinyint | NE |  |  |
| 71 | `IdDanovyKlic` | int | ANO |  |  |
