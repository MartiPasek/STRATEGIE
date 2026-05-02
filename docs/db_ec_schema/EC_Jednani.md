# EC_Jednani

**Schema**: dbo · **Cluster**: CRM · **Rows**: 2,852 · **Size**: 5.27 MB · **Sloupců**: 45 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `PoradoveCislo` | int | ANO |  |  |
| 3 | `Kategorie` | nvarchar(3) | ANO |  |  |
| 4 | `Predmet` | nvarchar(255) | ANO |  |  |
| 5 | `Typ` | nvarchar(3) | ANO |  |  |
| 6 | `Stav` | nvarchar(3) | ANO |  |  |
| 7 | `CisloOrg` | int | ANO |  |  |
| 8 | `CisloZam` | int | ANO |  |  |
| 9 | `CisloKontOsoba` | int | ANO |  |  |
| 10 | `MistoKonani` | nvarchar(255) | ANO |  |  |
| 11 | `SeznamOsob` | nvarchar(1000) | ANO |  |  |
| 12 | `DatumJednaniOd` | datetime | ANO |  |  |
| 13 | `DatumJednaniDo` | datetime | ANO |  |  |
| 14 | `Popis` | ntext | ANO |  |  |
| 15 | `Anglictina` | nvarchar(255) | ANO |  |  |
| 16 | `Nemcina` | nvarchar(255) | ANO |  |  |
| 17 | `DalsiJazyk` | nvarchar(255) | ANO |  |  |
| 18 | `OchotaCestovat` | nvarchar(255) | ANO |  |  |
| 19 | `ProgramovaciJazyky` | nvarchar(255) | ANO |  |  |
| 20 | `CiziJazyky` | nvarchar(255) | ANO |  |  |
| 21 | `PosledniZamestnani` | nvarchar(255) | ANO |  |  |
| 22 | `DuvodOdchodu` | nvarchar(255) | ANO |  |  |
| 23 | `Vzdelani` | nvarchar(255) | ANO |  |  |
| 24 | `Vyhlaska50` | bit | ANO |  |  |
| 25 | `TerminNastupu` | datetime | ANO |  |  |
| 26 | `Faze` | nvarchar(50) | ANO |  |  |
| 27 | `Sazba` | nvarchar(255) | ANO |  |  |
| 28 | `Zdroj` | nvarchar(100) | ANO |  |  |
| 29 | `TerminPohovoru` | datetime | ANO |  |  |
| 30 | `TerminTestovacichDni` | datetime | ANO |  |  |
| 31 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 32 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 33 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 34 | `DatZmeny` | datetime | ANO |  |  |
| 35 | `IDSkoly` | int | ANO | ((1)) |  |
| 36 | `CisZam` | int | ANO |  |  |
| 37 | `Prijmeni` | nvarchar(50) | ANO |  |  |
| 38 | `Jmeno` | nvarchar(50) | ANO |  |  |
| 39 | `Email` | nvarchar(200) | ANO |  |  |
| 40 | `Telefon` | nvarchar(50) | ANO |  |  |
| 41 | `DuvodZamitnuti` | int | ANO |  |  |
| 42 | `IDMistnosti` | int | ANO |  |  |
| 43 | `Alias` | nvarchar(30) | ANO |  |  |
| 44 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 45 | `SocialniSite` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Jednani` (CLUSTERED) — `ID`
