# EC_KontaktAkce

**Schema**: dbo · **Cluster**: CRM · **Rows**: 10,005 · **Size**: 4.40 MB · **Sloupců**: 33 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Poradi` | int | ANO |  |  |
| 4 | `IDAkce` | int | ANO |  |  |
| 5 | `Prubeh` | nvarchar(MAX) | ANO |  |  |
| 6 | `Splneno` | bit | ANO | ((0)) |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `FirmaText` | nvarchar(128) | ANO |  |  |
| 12 | `FirmaIDOrg` | int | ANO |  |  |
| 13 | `Kategorie` | smallint | ANO |  |  |
| 14 | `TypZakazky` | smallint | ANO |  |  |
| 15 | `ZemeID` | int | ANO |  |  |
| 16 | `Jmeno` | nvarchar(128) | ANO |  |  |
| 17 | `Prijmeni` | nvarchar(128) | ANO |  |  |
| 18 | `Mobil` | nvarchar(30) | ANO |  |  |
| 19 | `Telefon` | nvarchar(100) | ANO |  |  |
| 20 | `Email` | nvarchar(128) | ANO |  |  |
| 21 | `LinkedIn` | nvarchar(128) | ANO |  |  |
| 22 | `VyhledanoZ` | nvarchar(500) | ANO |  |  |
| 23 | `FirmaWeb` | nvarchar(500) | ANO |  |  |
| 24 | `Web` | nvarchar(256) | ANO |  |  |
| 25 | `Pozice` | nvarchar(128) | ANO |  |  |
| 26 | `ID_Sablona` | int | ANO |  |  |
| 27 | `DatumAkce` | date | ANO |  |  |
| 28 | `Popis` | nvarchar(2000) | ANO |  |  |
| 29 | `Poznamka` | nvarchar(2000) | ANO |  |  |
| 30 | `Adresa` | nvarchar(500) | ANO |  |  |
| 31 | `Titul` | nvarchar(64) | ANO |  |  |
| 32 | `Informace` | nvarchar(MAX) | ANO |  |  |
| 33 | `ID_LastAkce` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_KontaktAkce` (CLUSTERED) — `ID`
