# EC_Projekty

**Schema**: dbo · **Cluster**: Other · **Rows**: 532 · **Size**: 2.63 MB · **Sloupců**: 23 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Projekt` | nvarchar(15) | ANO |  |  |
| 3 | `ProjektZkr` | nvarchar(15) | NE | ('') |  |
| 4 | `Nazev` | nvarchar(100) | NE | ('') |  |
| 5 | `DatumZacatek` | datetime | ANO |  |  |
| 6 | `DatumKonecPlan` | datetime | ANO |  |  |
| 7 | `DatumKonecReal` | datetime | ANO |  |  |
| 8 | `PopisZadani` | ntext | ANO |  |  |
| 9 | `PopisAktualniStav` | ntext | ANO |  |  |
| 10 | `Divize` | int | ANO |  |  |
| 11 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 12 | `Zadavatel` | int | ANO | ([dbo].[ec_getuserciszam]()) |  |
| 13 | `Zodpovida` | int | ANO |  |  |
| 14 | `MaOpravneni` | nvarchar(200) | ANO |  |  |
| 15 | `ISZodpovidaUziv` | int | ANO |  |  |
| 16 | `Ukonceno` | int | NE |  |  |
| 17 | `Stav` | nvarchar(15) | NE | ('') |  |
| 18 | `Priorita` | nvarchar(10) | NE | ('') |  |
| 19 | `CisloContrUcet` | int | ANO |  |  |
| 20 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 21 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 22 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 23 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Projekty` (CLUSTERED) — `ID`
