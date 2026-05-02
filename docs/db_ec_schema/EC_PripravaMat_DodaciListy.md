# EC_PripravaMat_DodaciListy

**Schema**: dbo · **Cluster**: Production · **Rows**: 45 · **Size**: 0.07 MB · **Sloupců**: 27 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 3 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 5 | `Sloupec01` | nvarchar(300) | ANO |  |  |
| 6 | `Sloupec02` | nvarchar(300) | ANO |  |  |
| 7 | `Sloupec03` | nvarchar(300) | ANO |  |  |
| 8 | `Sloupec04` | nvarchar(300) | ANO |  |  |
| 9 | `Sloupec05` | nvarchar(300) | ANO |  |  |
| 10 | `Sloupec06` | nvarchar(300) | ANO |  |  |
| 11 | `Sloupec07` | nvarchar(300) | ANO |  |  |
| 12 | `Sloupec08` | nvarchar(300) | ANO |  |  |
| 13 | `Sloupec09` | nvarchar(300) | ANO |  |  |
| 14 | `Sloupec10` | nvarchar(300) | ANO |  |  |
| 15 | `Sloupec11` | nvarchar(300) | ANO |  |  |
| 16 | `Sloupec12` | nvarchar(300) | ANO |  |  |
| 17 | `Sloupec13` | nvarchar(300) | ANO |  |  |
| 18 | `Sloupec14` | nvarchar(300) | ANO |  |  |
| 19 | `Sloupec15` | nvarchar(300) | ANO |  |  |
| 20 | `Sloupec16` | nvarchar(300) | ANO |  |  |
| 21 | `Sloupec17` | nvarchar(300) | ANO |  |  |
| 22 | `Sloupec18` | nvarchar(300) | ANO |  |  |
| 23 | `Sloupec19` | nvarchar(300) | ANO |  |  |
| 24 | `Sloupec20` | nvarchar(300) | ANO |  |  |
| 25 | `CisloOrg` | int | ANO |  |  |
| 26 | `IDZakazky` | int | ANO |  |  |
| 27 | `CisloZakazky` | nvarchar(20) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PripravaMat_DodaciListy` (CLUSTERED) — `ID`
