# EC_ImportXLSHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 9,063 · **Size**: 2.94 MB · **Sloupců**: 74 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | NE |  |  |
| 3 | `CisloOrgZakaznik` | int | ANO |  |  |
| 4 | `Vyrobce` | nvarchar(5) | ANO |  |  |
| 5 | `CenyCZK` | bit | NE | ((0)) |  |
| 6 | `PlatnostDo` | datetime | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Sloupec01` | nvarchar(80) | ANO |  |  |
| 9 | `Sloupec02` | nvarchar(80) | ANO |  |  |
| 10 | `Sloupec03` | nvarchar(80) | ANO |  |  |
| 11 | `Sloupec04` | nvarchar(80) | ANO |  |  |
| 12 | `Sloupec05` | nvarchar(80) | ANO |  |  |
| 13 | `Sloupec06` | nvarchar(80) | ANO |  |  |
| 14 | `Sloupec07` | nvarchar(80) | ANO |  |  |
| 15 | `Sloupec08` | nvarchar(80) | ANO |  |  |
| 16 | `Sloupec09` | nvarchar(80) | ANO |  |  |
| 17 | `Sloupec10` | nvarchar(80) | ANO |  |  |
| 18 | `Sloupec11` | nvarchar(80) | ANO |  |  |
| 19 | `Sloupec12` | nvarchar(80) | ANO |  |  |
| 20 | `Sloupec13` | nvarchar(80) | ANO |  |  |
| 21 | `Sloupec14` | nvarchar(80) | ANO |  |  |
| 22 | `Sloupec15` | nvarchar(80) | ANO |  |  |
| 23 | `Sloupec16` | nvarchar(80) | ANO |  |  |
| 24 | `Sloupec17` | nvarchar(80) | ANO |  |  |
| 25 | `Sloupec18` | nvarchar(80) | ANO |  |  |
| 26 | `Sloupec19` | nvarchar(80) | ANO |  |  |
| 27 | `Sloupec20` | nvarchar(80) | ANO |  |  |
| 28 | `Sloupec21` | nvarchar(80) | ANO |  |  |
| 29 | `Sloupec22` | nvarchar(80) | ANO |  |  |
| 30 | `Sloupec23` | nvarchar(80) | ANO |  |  |
| 31 | `Sloupec24` | nvarchar(80) | ANO |  |  |
| 32 | `Sloupec25` | nvarchar(80) | ANO |  |  |
| 33 | `Sloupec26` | nvarchar(80) | ANO |  |  |
| 34 | `Sloupec27` | nvarchar(80) | ANO |  |  |
| 35 | `Sloupec28` | nvarchar(80) | ANO |  |  |
| 36 | `Sloupec29` | nvarchar(80) | ANO |  |  |
| 37 | `Sloupec30` | nvarchar(80) | ANO |  |  |
| 38 | `Sloupec31` | nvarchar(80) | ANO |  |  |
| 39 | `Sloupec32` | nvarchar(80) | ANO |  |  |
| 40 | `Sloupec33` | nvarchar(80) | ANO |  |  |
| 41 | `Sloupec34` | nvarchar(80) | ANO |  |  |
| 42 | `Sloupec35` | nvarchar(80) | ANO |  |  |
| 43 | `Sloupec36` | nvarchar(80) | ANO |  |  |
| 44 | `Sloupec37` | nvarchar(80) | ANO |  |  |
| 45 | `Sloupec38` | nvarchar(80) | ANO |  |  |
| 46 | `Sloupec39` | nvarchar(80) | ANO |  |  |
| 47 | `Sloupec40` | nvarchar(80) | ANO |  |  |
| 48 | `Sloupec41` | nvarchar(80) | ANO |  |  |
| 49 | `Sloupec42` | nvarchar(80) | ANO |  |  |
| 50 | `Sloupec43` | nvarchar(80) | ANO |  |  |
| 51 | `Sloupec44` | nvarchar(80) | ANO |  |  |
| 52 | `Sloupec45` | nvarchar(80) | ANO |  |  |
| 53 | `Sloupec46` | nvarchar(80) | ANO |  |  |
| 54 | `Sloupec47` | nvarchar(80) | ANO |  |  |
| 55 | `Sloupec48` | nvarchar(80) | ANO |  |  |
| 56 | `Sloupec49` | nvarchar(80) | ANO |  |  |
| 57 | `Sloupec50` | nvarchar(80) | ANO |  |  |
| 58 | `EC_PC` | tinyint | ANO |  |  |
| 59 | `EC_NC` | tinyint | ANO |  |  |
| 60 | `EAN` | tinyint | ANO |  |  |
| 61 | `Blokovano` | bit | ANO | ((0)) |  |
| 62 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 63 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 64 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 65 | `DatZmeny` | datetime | ANO |  |  |
| 66 | `DatPorizeni_D` | int | ANO |  |  |
| 67 | `DatPorizeni_M` | int | ANO |  |  |
| 68 | `DatPorizeni_Y` | int | ANO |  |  |
| 69 | `DatPorizeni_Q` | int | ANO |  |  |
| 70 | `DatPorizeni_W` | int | ANO |  |  |
| 71 | `DatPorizeni_X` | datetime | ANO |  |  |
| 72 | `Zpracovano` | bit | ANO |  |  |
| 73 | `DatZpracovani` | datetime | ANO |  |  |
| 74 | `Zpracoval` | nvarchar(126) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ImportXLSHlav` (CLUSTERED) — `ID`
