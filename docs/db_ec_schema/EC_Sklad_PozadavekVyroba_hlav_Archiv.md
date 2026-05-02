# EC_Sklad_PozadavekVyroba_hlav_Archiv

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `DatZpracovani` | datetime | ANO |  |  |
| 4 | `Zpracoval` | nvarchar(126) | ANO |  |  |
| 5 | `Priorita` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(126) | ANO |  |  |
| 7 | `DatPorizeni` | datetime | ANO |  |  |
| 8 | `DatOdeslani` | datetime | ANO |  |  |
| 9 | `CisloZakazkyVzor` | nvarchar(10) | ANO |  |  |
| 10 | `Urgentni` | bit | ANO |  |  |
| 11 | `Typ` | int | ANO |  |  |
| 12 | `IDOldPozadavek` | int | ANO |  |  |
| 13 | `VeZpracovani` | bit | ANO |  |  |
| 14 | `Resitel` | int | ANO |  |  |
| 15 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 16 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 17 | `IDPuvodni` | int | ANO |  |  |
| 18 | `Procedura` | nvarchar(500) | ANO |  |  |
| 19 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 20 | `VydanPredOdeslanim` | bit | ANO |  |  |
| 21 | `StavKalkulace` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_PozadavekVyroba_Archiv` (CLUSTERED) — `ID`
