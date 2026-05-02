# EC_Sklad_PozadavekVyroba_pol

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 32 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `IDZboSklad` | int | ANO |  |  |
| 4 | `RegCis` | nvarchar(60) | ANO |  |  |
| 5 | `Mnozstvi` | numeric(19,2) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(100) | ANO |  |  |
| 7 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `MnozstviKalkulace` | numeric(19,2) | ANO |  |  |
| 10 | `Skladem` | numeric(19,2) | ANO |  |  |
| 11 | `PocetProjektu` | numeric(5,0) | ANO |  |  |
| 12 | `PocetProjektuCelkem` | numeric(5,0) | ANO |  |  |
| 13 | `ProcentoProjekty` | numeric(15,0) | ANO |  |  |
| 14 | `Web` | nvarchar(1000) | ANO |  |  |
| 15 | `Barva` | int | ANO |  |  |
| 16 | `RegCisFiltr` | nvarchar(126) | ANO |  |  |
| 17 | `PoradiSkup` | int | ANO |  |  |
| 18 | `UzavreneVKM` | bit | ANO |  |  |
| 19 | `OtevreneVKM` | bit | ANO |  |  |
| 20 | `S1` | bit | ANO |  |  |
| 21 | `MnozstviVzor` | numeric(19,2) | ANO |  |  |
| 22 | `Nazev1` | nvarchar(200) | ANO |  |  |
| 23 | `NazevCZ` | nvarchar(200) | ANO |  |  |
| 24 | `MJ` | nvarchar(10) | ANO |  |  |
| 25 | `OsOdberSklad` | bit | ANO | ((0)) |  |
| 26 | `MnozstviVydane` | numeric(19,6) | ANO |  |  |
| 27 | `IDold` | int | ANO |  |  |
| 28 | `TypPozadavkuPref` | int | ANO |  |  |
| 29 | `Stornoval` | nvarchar(126) | ANO |  |  |
| 30 | `DatStorna` | datetime | ANO |  |  |
| 31 | `MnozstviStorna` | numeric(19,6) | ANO |  |  |
| 32 | `IDPolVydejky` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Sklad_PozadavekVyroba_pol` (CLUSTERED) — `ID`
