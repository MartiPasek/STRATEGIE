# TabKontaktyImp

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 51 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ChybovaHlaska` | ntext | ANO |  |  |
| 3 | `IDOrg` | int | ANO |  |  |
| 4 | `IDCisKOs` | int | ANO |  |  |
| 5 | `IDCisZam` | int | ANO |  |  |
| 6 | `IDVztahKOsOrg` | int | ANO |  |  |
| 7 | `Popis` | nvarchar(255) | NE | ('') |  |
| 8 | `Spojeni` | nvarchar(255) | NE | ('') |  |
| 9 | `Spojeni2` | nvarchar(255) | NE | ('') |  |
| 10 | `Druh` | smallint | NE | ((1)) |  |
| 11 | `Kam` | smallint | NE | ((0)) |  |
| 12 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 13 | `Prednastaveno` | bit | NE | ((0)) |  |
| 14 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `DatPorizeni_D` | int | ANO |  |  |
| 19 | `DatPorizeni_M` | int | ANO |  |  |
| 20 | `DatPorizeni_Y` | int | ANO |  |  |
| 21 | `DatPorizeni_Q` | int | ANO |  |  |
| 22 | `DatPorizeni_W` | int | ANO |  |  |
| 23 | `DatPorizeni_X` | datetime | ANO |  |  |
| 24 | `DatZmeny_D` | int | ANO |  |  |
| 25 | `DatZmeny_M` | int | ANO |  |  |
| 26 | `DatZmeny_Y` | int | ANO |  |  |
| 27 | `DatZmeny_Q` | int | ANO |  |  |
| 28 | `DatZmeny_W` | int | ANO |  |  |
| 29 | `DatZmeny_X` | datetime | ANO |  |  |
| 30 | `ECertByName` | nvarchar(128) | NE | ('') |  |
| 31 | `ECertToName` | nvarchar(128) | NE | ('') |  |
| 32 | `ECertSN` | nvarchar(128) | NE | ('') |  |
| 33 | `ECertStoreLocation` | tinyint | NE | ((2)) |  |
| 34 | `ECertStoreName` | tinyint | NE | ((1)) |  |
| 35 | `TypSubjektu` | tinyint | NE | ((1)) |  |
| 36 | `CasValidace` | datetime | ANO |  |  |
| 37 | `StavValidace` | tinyint | NE | ((0)) |  |
| 38 | `CasValidace_D` | int | ANO |  |  |
| 39 | `CasValidace_M` | int | ANO |  |  |
| 40 | `CasValidace_Y` | int | ANO |  |  |
| 41 | `CasValidace_Q` | int | ANO |  |  |
| 42 | `CasValidace_W` | int | ANO |  |  |
| 43 | `CasValidace_X` | datetime | ANO |  |  |
| 44 | `ECertLDAPQuery` | nvarchar(255) | NE | ('') |  |
| 45 | `ECertDatumOd` | datetime | ANO |  |  |
| 46 | `ECertDatumDo` | datetime | ANO |  |  |
| 47 | `IDHromProEMailDef` | int | ANO |  |  |
| 48 | `EmailNP` | bit | NE | ((0)) |  |
| 49 | `JeNovaVetaEditor` | bit | NE | ((0)) |  |
| 50 | `LimitProDS` | tinyint | NE | ((1)) |  |
| 51 | `StavDS` | tinyint | ANO |  |  |

## Implicitní vztahy (heuristic, NE declared FK)

- `IDOrg` → pravděpodobně `TabCisOrg`

> _Marti-AI: Heliosové tabulky často nepoužívají declared FK. Vztah je dohadován z naming convention. Pro jistotu ověř před joiny._

## Indexy

- **PK** `PK__TabKontaktyImp__ID` (CLUSTERED) — `ID`
