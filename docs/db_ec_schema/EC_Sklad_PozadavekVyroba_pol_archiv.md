# EC_Sklad_PozadavekVyroba_pol_archiv

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 33 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `IDZboSklad` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(60) | ANO |  |  |
| 5 | `Mnozstvi` | numeric(19,2) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(100) | ANO |  |  |
| 7 | `Autor` | nvarchar(126) | ANO |  |  |
| 8 | `DatPorizeni` | datetime | ANO |  |  |
| 9 | `MnozstviKalkulace` | numeric(19,2) | ANO |  |  |
| 10 | `Skladem` | numeric(19,2) | ANO |  |  |
| 11 | `Barva` | int | ANO |  |  |
| 12 | `RegCisFiltr` | nvarchar(126) | ANO |  |  |
| 13 | `PoradiSkup` | int | ANO |  |  |
| 14 | `UzavreneVKM` | bit | ANO |  |  |
| 15 | `OtevreneVKM` | bit | ANO |  |  |
| 16 | `S1` | bit | ANO |  |  |
| 17 | `MnozstviVzor` | numeric(19,2) | ANO |  |  |
| 18 | `Nazev1` | nvarchar(200) | ANO |  |  |
| 19 | `NazevCZ` | nvarchar(200) | ANO |  |  |
| 20 | `MJ` | nvarchar(10) | ANO |  |  |
| 21 | `OsOdberSklad` | bit | ANO |  |  |
| 22 | `MnozstviVydane` | numeric(19,6) | ANO |  |  |
| 23 | `IDold` | int | ANO |  |  |
| 24 | `Archivoval` | nvarchar(126) | ANO | (suser_sname()) |  |
| 25 | `DatArchivace` | datetime | ANO | (getdate()) |  |
| 26 | `IDPuvodni` | int | ANO |  |  |
| 27 | `Procedura` | nvarchar(500) | ANO |  |  |
| 28 | `PoznamkaArch` | nvarchar(1000) | ANO |  |  |
| 29 | `TypPozadavkuPref` | int | ANO |  |  |
| 30 | `Stornoval` | nvarchar(126) | ANO |  |  |
| 31 | `DatStorna` | datetime | ANO |  |  |
| 32 | `MnozstviStorna` | numeric(19,6) | ANO |  |  |
| 33 | `IDPolVydejky` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_PozadavekVyroba_pol_Archiv` (CLUSTERED) — `ID`
