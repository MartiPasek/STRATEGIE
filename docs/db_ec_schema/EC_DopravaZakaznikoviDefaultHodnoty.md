# EC_DopravaZakaznikoviDefaultHodnoty

**Schema**: dbo · **Cluster**: Other · **Rows**: 50 · **Size**: 0.20 MB · **Sloupců**: 23 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Oznaceni` | nvarchar(10) | ANO |  |  |
| 4 | `ObsahDodavky` | nchar(200) | ANO |  |  |
| 5 | `BylaZmena` | bit | ANO |  |  |
| 6 | `PrijemceDopravy` | int | ANO |  |  |
| 7 | `Objednava` | nvarchar(100) | ANO |  |  |
| 8 | `FinalniDatumVykladky` | bit | ANO |  |  |
| 9 | `DatumVykladkyOd` | datetime | ANO |  |  |
| 10 | `DatumVykladkyDo` | datetime | ANO |  |  |
| 11 | `DatDodaniDO_FIX` | bit | ANO |  |  |
| 12 | `DatumCasOdvozuOdDleZkusebna` | datetime | ANO |  |  |
| 13 | `DopravceKontakt` | nvarchar(100) | ANO |  |  |
| 14 | `AdresaDoruceni` | nvarchar(MAX) | ANO |  |  |
| 15 | `InfoProDopravce` | nvarchar(MAX) | ANO |  |  |
| 16 | `PozadavkyNaDopravu` | nvarchar(255) | ANO |  |  |
| 17 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 19 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 20 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 21 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 22 | `DatZmeny` | datetime | ANO |  |  |
| 23 | `DatumOdvozu` | datetime | ANO |  |  |
| 24 | `DopravceKontakt_CisloOrg` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_DopravaZakaznikoviDefaultHodnoty` (CLUSTERED) — `ID`
