# EC_PripravaMat_Kusovnik

**Schema**: dbo · **Cluster**: Production · **Rows**: 43 · **Size**: 0.07 MB · **Sloupců**: 38 · **FK**: 0 · **Indexů**: 1

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
| 17 | `CisloOrg` | int | ANO |  |  |
| 18 | `Tisk_Stitky_Pomlcka` | bit | ANO | ((0)) |  |
| 19 | `Sloupec13` | nvarchar(300) | ANO |  |  |
| 20 | `Sloupec14` | nvarchar(300) | ANO |  |  |
| 21 | `Sloupec15` | nvarchar(300) | ANO |  |  |
| 22 | `Sloupec16` | nvarchar(300) | ANO |  |  |
| 23 | `Sloupec17` | nvarchar(300) | ANO |  |  |
| 24 | `Sloupec18` | nvarchar(300) | ANO |  |  |
| 25 | `Sloupec19` | nvarchar(300) | ANO |  |  |
| 26 | `Sloupec20` | nvarchar(300) | ANO |  |  |
| 27 | `TMPsken_inputTEXT` | nvarchar(200) | ANO |  |  |
| 28 | `TMPsken_fullTEXT` | nvarchar(2000) | ANO |  |  |
| 29 | `TMPsken_akceTEXT` | nvarchar(50) | ANO | (N'Naskenuj číslo stroje.') |  |
| 30 | `TMPsken_testovani` | nvarchar(500) | ANO |  |  |
| 31 | `TMPskenKusovnik_inputTEXT` | nvarchar(200) | ANO |  |  |
| 32 | `TMPskenKusovnik_fullTEXT` | nvarchar(2000) | ANO |  |  |
| 33 | `TMPskenKusovnik_akceTEXT` | nvarchar(50) | ANO | (N'Naskenuj číslo stroje.') |  |
| 34 | `TMPskenKusovnik_testovani` | nvarchar(500) | ANO |  |  |
| 35 | `TypTisku` | smallint | ANO | ((0)) |  |
| 36 | `TMPskenKusovnik_Mnozstvi` | smallint | ANO | ((1)) |  |
| 37 | `IDZakazky` | int | ANO |  |  |
| 38 | `CisloZakazky` | nvarchar(20) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PripravaMat_Kusovnik` (CLUSTERED) — `ID`
