# EC_Kontakt

**Schema**: dbo · **Cluster**: CRM · **Rows**: 9,105 · **Size**: 7.77 MB · **Sloupců**: 36 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `FirmaText` | nvarchar(128) | ANO |  |  |
| 7 | `FirmaIDOrg` | int | ANO |  |  |
| 8 | `FirmaTelefon` | nvarchar(30) | ANO |  |  |
| 9 | `FirmaEmail` | nvarchar(128) | ANO |  |  |
| 10 | `FirmaWeb` | nvarchar(500) | ANO |  |  |
| 11 | `Kategorie` | smallint | ANO |  |  |
| 12 | `TypZakazky` | smallint | ANO |  |  |
| 13 | `KontaktText` | nvarchar(128) | ANO |  |  |
| 14 | `KontaktID` | int | ANO |  |  |
| 15 | `OdpOsobaAtext` | nvarchar(128) | ANO |  |  |
| 16 | `OdpOsAkontaktID` | int | ANO |  |  |
| 17 | `OdpOsobaBtext` | nvarchar(128) | ANO |  |  |
| 18 | `OdpOsBkontaktID` | int | ANO |  |  |
| 19 | `OdpOsobaCtext` | nvarchar(128) | ANO |  |  |
| 20 | `OdpOsCkontaktID` | int | ANO |  |  |
| 21 | `OdpOsobaDtext` | nvarchar(128) | ANO |  |  |
| 22 | `OdpOsDkontaktID` | int | ANO |  |  |
| 23 | `OdpOsobaEtext` | nvarchar(128) | ANO |  |  |
| 24 | `OdpOsEkontaktID` | int | ANO |  |  |
| 25 | `ObeslalZamID` | int | ANO |  |  |
| 26 | `KomunikaceZamID` | int | ANO |  |  |
| 27 | `VyhledanoZ` | nvarchar(500) | ANO |  |  |
| 28 | `PoDDspoluprace` | smallint | ANO |  |  |
| 29 | `PoProBjednani` | smallint | ANO |  |  |
| 30 | `Atraktivita` | smallint | ANO |  |  |
| 31 | `PristiKontakt` | datetime | ANO |  |  |
| 32 | `Razeni` | int | ANO |  |  |
| 33 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 34 | `Poznamka` | nvarchar(500) | ANO |  |  |
| 35 | `Zeme` | nvarchar(64) | ANO |  |  |
| 36 | `ZemeID` | int | ANO |  |  |

## Implicitní vztahy (heuristic, NE declared FK)

- `KontaktID` → pravděpodobně `EC_Kontakt`
- `OdpOsAkontaktID` → pravděpodobně `EC_Kontakt`
- `OdpOsBkontaktID` → pravděpodobně `EC_Kontakt`
- `OdpOsCkontaktID` → pravděpodobně `EC_Kontakt`
- `OdpOsDkontaktID` → pravděpodobně `EC_Kontakt`
- `OdpOsEkontaktID` → pravděpodobně `EC_Kontakt`

> _Marti-AI: Heliosové tabulky často nepoužívají declared FK. Vztah je dohadován z naming convention. Pro jistotu ověř před joiny._

## Indexy

- **PK** `PK_EC_Kontakt` (CLUSTERED) — `ID`
