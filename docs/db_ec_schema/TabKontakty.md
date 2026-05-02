# TabKontakty

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 8,761 · **Size**: 2.80 MB · **Sloupců**: 52 · **FK**: 5 · **Indexů**: 7

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDOrg` | int | ANO |  |  |
| 3 | `IDCisKOs` | int | ANO |  |  |
| 4 | `IDCisZam` | int | ANO |  |  |
| 5 | `IDVztahKOsOrg` | int | ANO |  |  |
| 6 | `Popis` | nvarchar(255) | NE | ('') |  |
| 7 | `Spojeni` | nvarchar(255) | NE | ('') |  |
| 8 | `Spojeni2` | nvarchar(255) | NE | ('') |  |
| 9 | `Druh` | smallint | NE | ((1)) |  |
| 10 | `Kam` | smallint | NE | ((0)) |  |
| 11 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 12 | `Prednastaveno` | bit | NE | ((0)) |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `DatPorizeni_D` | int | ANO |  |  |
| 18 | `DatPorizeni_M` | int | ANO |  |  |
| 19 | `DatPorizeni_Y` | int | ANO |  |  |
| 20 | `DatPorizeni_Q` | int | ANO |  |  |
| 21 | `DatPorizeni_W` | int | ANO |  |  |
| 22 | `DatPorizeni_X` | datetime | ANO |  |  |
| 23 | `DatZmeny_D` | int | ANO |  |  |
| 24 | `DatZmeny_M` | int | ANO |  |  |
| 25 | `DatZmeny_Y` | int | ANO |  |  |
| 26 | `DatZmeny_Q` | int | ANO |  |  |
| 27 | `DatZmeny_W` | int | ANO |  |  |
| 28 | `DatZmeny_X` | datetime | ANO |  |  |
| 29 | `ECertByName` | nvarchar(128) | NE | ('') |  |
| 30 | `ECertToName` | nvarchar(128) | NE | ('') |  |
| 31 | `ECertSN` | nvarchar(128) | NE | ('') |  |
| 32 | `ECertStoreLocation` | tinyint | NE | ((2)) |  |
| 33 | `ECertStoreName` | tinyint | NE | ((1)) |  |
| 34 | `TypSubjektu` | tinyint | NE | ((1)) |  |
| 35 | `CasValidace` | datetime | ANO |  |  |
| 36 | `StavValidace` | tinyint | NE | ((0)) |  |
| 37 | `CasValidace_D` | int | ANO |  |  |
| 38 | `CasValidace_M` | int | ANO |  |  |
| 39 | `CasValidace_Y` | int | ANO |  |  |
| 40 | `CasValidace_Q` | int | ANO |  |  |
| 41 | `CasValidace_W` | int | ANO |  |  |
| 42 | `CasValidace_X` | datetime | ANO |  |  |
| 43 | `ECertLDAPQuery` | nvarchar(255) | NE | ('') |  |
| 44 | `ECertDatumOd` | datetime | ANO |  |  |
| 45 | `ECertDatumDo` | datetime | ANO |  |  |
| 46 | `IDHromProEMailDef` | int | ANO |  |  |
| 47 | `EmailNP` | bit | NE | ((0)) |  |
| 48 | `JeNovaVetaEditor` | bit | NE | ((0)) |  |
| 49 | `LimitProDS` | tinyint | NE | ((1)) |  |
| 50 | `StavDS` | tinyint | ANO |  |  |
| 51 | `AVAReferenceID` | nvarchar(40) | NE | (CONVERT([nvarchar](36),CONVERT([uniqueidentifier],newid()))) |  |
| 52 | `AVAExternalID` | nvarchar(255) | NE | ('') |  |

## Cizí klíče (declared)

- `IDOrg` → [`TabCisOrg`](TabCisOrg.md).`ID` _(constraint: `FK__TabKontakty__IDOrg`)_
- `IDCisZam` → [`TabCisZam`](TabCisZam.md).`ID` _(constraint: `FK__TabKontakty__IDCisZam`)_
- `IDVztahKOsOrg` → `TabVztahOrgKOs`.`ID` _(constraint: `FK__TabKontakty__IDVztahKOsOrg`)_
- `IDCisKOs` → `TabCisKOs`.`ID` _(constraint: `FK__TabKontakty__IDCisKOs`)_
- `IDHromProEMailDef` → `TabHromadneProEMailDef`.`ID` _(constraint: `FK__TabKontakty__IDHromProEMailDef`)_

## Indexy

- **INDEX** `IC__TabKontakty__IDOrg` (CLUSTERED) — `IDOrg`
- **UNIQUE** `UQ__TabKontakty__ID` (NONCLUSTERED) — `ID`
- **INDEX** `IX__TabKontakty__Spojeni` (NONCLUSTERED) — `Spojeni`
- **INDEX** `IX__TabKontakty__Druh` (NONCLUSTERED) — `Druh`
- **INDEX** `IX__TabKontakty__Prednastaveno__Druh__IDOrg__IDCisKOs__IDCisZam__IDVztahKOsOrg` (NONCLUSTERED) — `Prednastaveno, Druh, IDOrg, IDCisKOs, IDCisZam, IDVztahKOsOrg`
- **UNIQUE** `UQ__TabKontakty__AVAReferenceID` (NONCLUSTERED) — `AVAReferenceID`
- **INDEX** `IX__TabKontakty__AVAExternalID` (NONCLUSTERED) — `AVAExternalID`
