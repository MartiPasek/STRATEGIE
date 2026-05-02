# EC_DW_Dokumenty

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDoklad` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 4 | `TypDoklad` | int | ANO |  | 1=TabDokladyZbozi, 3 = ZZVTK |
| 5 | `Kod` | nvarchar(30) | ANO |  |  |
| 6 | `Stav` | int | ANO | ((0)) |  |
| 7 | `Stav2` | int | ANO |  |  |
| 8 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `DatNaskenovani` | datetime | ANO |  |  |
| 11 | `Naskenoval` | nvarchar(126) | ANO |  |  |
| 12 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 13 | `SeznamZakazek` | nvarchar(2000) | ANO |  |  |
| 14 | `SeznamRegCis` | nvarchar(2000) | ANO |  |  |
| 15 | `SeznamPrijemek` | nvarchar(2000) | ANO |  |  |
| 16 | `SeznamObjednavek` | nvarchar(2000) | ANO |  |  |
| 17 | `NechtenyMaterial` | bit | ANO | ((0)) |  |
| 18 | `NedodanyMaterial` | bit | ANO | ((0)) |  |
| 19 | `DokladSmazan` | bit | ANO | ((0)) |  |
| 20 | `DokladSmazal` | nvarchar(126) | ANO |  |  |
| 21 | `KomuPreposlat` | nvarchar(2000) | ANO |  |  |
| 22 | `VPEmail1` | nvarchar(100) | ANO |  |  |
| 23 | `VPEmail2` | nvarchar(100) | ANO |  |  |
| 24 | `VPEmail3` | nvarchar(100) | ANO |  |  |
| 25 | `VPEmail4` | nvarchar(100) | ANO |  |  |
| 26 | `VPEmail5` | nvarchar(100) | ANO |  |  |
| 27 | `SefmonterEmail` | nvarchar(2000) | ANO |  |  |
| 28 | `Zakazky` | nvarchar(2000) | ANO |  |  |
| 29 | `DWZpravaWF` | nvarchar(1000) | ANO |  |  |
