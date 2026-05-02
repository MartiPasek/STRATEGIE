# EC_PripravaMat_DodaciListy_Pol

**Schema**: dbo · **Cluster**: Production · **Rows**: 10,029 · **Size**: 3.48 MB · **Sloupců**: 28 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 3 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `IDHlav` | int | NE |  |  |
| 6 | `Sloupec01` | nvarchar(300) | ANO |  |  |
| 7 | `Sloupec02` | nvarchar(300) | ANO |  |  |
| 8 | `Sloupec03` | nvarchar(300) | ANO |  |  |
| 9 | `Sloupec04` | nvarchar(300) | ANO |  |  |
| 10 | `Sloupec05` | nvarchar(300) | ANO |  |  |
| 11 | `Sloupec06` | nvarchar(300) | ANO |  |  |
| 12 | `Sloupec07` | nvarchar(300) | ANO |  |  |
| 13 | `Sloupec08` | nvarchar(300) | ANO |  |  |
| 14 | `Sloupec09` | nvarchar(300) | ANO |  |  |
| 15 | `Sloupec10` | nvarchar(300) | ANO |  |  |
| 16 | `Sloupec11` | nvarchar(300) | ANO |  |  |
| 17 | `Sloupec12` | nvarchar(300) | ANO |  |  |
| 18 | `Sloupec13` | nvarchar(300) | ANO |  |  |
| 19 | `Sloupec14` | nvarchar(300) | ANO |  |  |
| 20 | `Sloupec15` | nvarchar(300) | ANO |  |  |
| 21 | `Sloupec16` | nvarchar(300) | ANO |  |  |
| 22 | `Sloupec17` | nvarchar(300) | ANO |  |  |
| 23 | `Sloupec18` | nvarchar(300) | ANO |  |  |
| 24 | `Sloupec19` | nvarchar(300) | ANO |  |  |
| 25 | `Sloupec20` | nvarchar(300) | ANO |  |  |
| 26 | `SkenCislo` | nvarchar(300) | ANO |  |  |
| 27 | `Popis` | nvarchar(300) | ANO |  |  |
| 28 | `Mnozstvi` | nvarchar(300) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PripravaMat_DodaciListy_Pol` (CLUSTERED) — `ID`
- **INDEX** `IX_DodaciListyPol_Sloupec03_Poznamka_IDHlav` (NONCLUSTERED) — `Sloupec03, Poznamka, IDHlav`
