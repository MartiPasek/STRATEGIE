# EC_PripravaMat_Kusovnik_Pol

**Schema**: dbo · **Cluster**: Production · **Rows**: 42,394 · **Size**: 17.95 MB · **Sloupců**: 46 · **FK**: 0 · **Indexů**: 2

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
| 18 | `Tisk` | bit | ANO | ((0)) |  |
| 19 | `Sloupec13` | nvarchar(300) | ANO |  |  |
| 20 | `Sloupec14` | nvarchar(300) | ANO |  |  |
| 21 | `Sloupec15` | nvarchar(300) | ANO |  |  |
| 22 | `Sloupec16` | nvarchar(300) | ANO |  |  |
| 23 | `Sloupec17` | nvarchar(300) | ANO |  |  |
| 24 | `Sloupec18` | nvarchar(300) | ANO |  |  |
| 25 | `Sloupec19` | nvarchar(300) | ANO |  |  |
| 26 | `Sloupec20` | nvarchar(300) | ANO |  |  |
| 27 | `SerioveCisloStroje` | nvarchar(200) | ANO |  |  |
| 28 | `TypTisku` | smallint | ANO | ((0)) |  |
| 29 | `Nalezeno` | bit | ANO | ((0)) |  |
| 30 | `PoznamkaDilna` | nvarchar(MAX) | ANO |  |  |
| 31 | `K` | bit | ANO | ((0)) |  |
| 32 | `DFL` | bit | ANO | ((0)) |  |
| 33 | `DilChybi` | bit | ANO | ((0)) |  |
| 34 | `Chyba` | bit | ANO | ((0)) |  |
| 35 | `MnCelkem` | numeric(18,4) | ANO |  |  |
| 36 | `SkenCislo` | nvarchar(300) | ANO |  |  |
| 37 | `ObjednaciCislo` | nvarchar(300) | ANO |  |  |
| 38 | `Popis` | nvarchar(300) | ANO |  |  |
| 39 | `Vyrobce` | nvarchar(300) | ANO |  |  |
| 40 | `Mnozstvi` | nvarchar(300) | ANO |  |  |
| 41 | `Znaceni` | nvarchar(300) | ANO |  |  |
| 42 | `Strana` | nvarchar(300) | ANO |  |  |
| 43 | `ZnaceniStrana` | nvarchar(300) | ANO |  |  |
| 44 | `BarCode` | nvarchar(50) | ANO |  |  |
| 45 | `JunkerOsa` | nvarchar(50) | ANO |  |  |
| 46 | `IDKmenZbo` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_PripravaMat_Kusovnik_Pol` (CLUSTERED) — `ID`
- **INDEX** `IX_KusovnikPol_Sloupec05_Poznamka` (NONCLUSTERED) — `Sloupec05, Poznamka`
