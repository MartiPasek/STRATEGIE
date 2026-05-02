# EC_CenikyTXTHlav

**Schema**: dbo · **Cluster**: Finance · **Rows**: 2,100 · **Size**: 0.99 MB · **Sloupců**: 73 · **FK**: 0 · **Indexů**: 1

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
| 72 | `ImportXLSHlav_ID` | int | ANO |  |  |
| 73 | `PlatnostOD` | datetime | ANO | (getdate()) |  |
| 74 | `Sloupec01` | nvarchar(80) | ANO |  |  |
| 75 | `Sloupec02` | nvarchar(80) | ANO |  |  |
| 76 | `Sloupec03` | nvarchar(80) | ANO |  |  |
| 77 | `Sloupec04` | nvarchar(80) | ANO |  |  |
| 78 | `Sloupec05` | nvarchar(80) | ANO |  |  |
| 79 | `Sloupec06` | nvarchar(80) | ANO |  |  |
| 80 | `Sloupec07` | nvarchar(80) | ANO |  |  |
| 81 | `Sloupec08` | nvarchar(80) | ANO |  |  |
| 82 | `Sloupec09` | nvarchar(80) | ANO |  |  |
| 83 | `Sloupec10` | nvarchar(80) | ANO |  |  |
| 84 | `Sloupec11` | nvarchar(80) | ANO |  |  |
| 85 | `Sloupec12` | nvarchar(80) | ANO |  |  |
| 86 | `Sloupec13` | nvarchar(80) | ANO |  |  |
| 87 | `Sloupec14` | nvarchar(80) | ANO |  |  |
| 88 | `Sloupec15` | nvarchar(80) | ANO |  |  |
| 89 | `Sloupec16` | nvarchar(80) | ANO |  |  |
| 90 | `Sloupec17` | nvarchar(80) | ANO |  |  |
| 91 | `Sloupec18` | nvarchar(80) | ANO |  |  |
| 92 | `Sloupec19` | nvarchar(80) | ANO |  |  |
| 93 | `Sloupec20` | nvarchar(80) | ANO |  |  |
| 94 | `Sloupec21` | nvarchar(80) | ANO |  |  |
| 95 | `Sloupec22` | nvarchar(80) | ANO |  |  |
| 96 | `Sloupec23` | nvarchar(80) | ANO |  |  |
| 97 | `Sloupec24` | nvarchar(80) | ANO |  |  |
| 98 | `Sloupec25` | nvarchar(80) | ANO |  |  |
| 99 | `Sloupec26` | nvarchar(80) | ANO |  |  |
| 100 | `Sloupec27` | nvarchar(80) | ANO |  |  |
| 101 | `Sloupec28` | nvarchar(80) | ANO |  |  |
| 102 | `Sloupec29` | nvarchar(80) | ANO |  |  |
| 103 | `Sloupec30` | nvarchar(80) | ANO |  |  |
| 104 | `Sloupec31` | nvarchar(80) | ANO |  |  |
| 105 | `Sloupec32` | nvarchar(80) | ANO |  |  |
| 106 | `Sloupec33` | nvarchar(80) | ANO |  |  |
| 107 | `Sloupec34` | nvarchar(80) | ANO |  |  |
| 108 | `Sloupec35` | nvarchar(80) | ANO |  |  |
| 109 | `Sloupec36` | nvarchar(80) | ANO |  |  |
| 110 | `Sloupec37` | nvarchar(80) | ANO |  |  |
| 111 | `Sloupec38` | nvarchar(80) | ANO |  |  |
| 112 | `Sloupec39` | nvarchar(80) | ANO |  |  |
| 113 | `Sloupec40` | nvarchar(80) | ANO |  |  |
| 114 | `Sloupec41` | nvarchar(80) | ANO |  |  |
| 115 | `Sloupec42` | nvarchar(80) | ANO |  |  |
| 116 | `Sloupec43` | nvarchar(80) | ANO |  |  |
| 117 | `Sloupec44` | nvarchar(80) | ANO |  |  |
| 118 | `Sloupec45` | nvarchar(80) | ANO |  |  |
| 119 | `Sloupec46` | nvarchar(80) | ANO |  |  |
| 120 | `Sloupec47` | nvarchar(80) | ANO |  |  |
| 121 | `Sloupec48` | nvarchar(80) | ANO |  |  |
| 122 | `Sloupec49` | nvarchar(80) | ANO |  |  |
| 123 | `Sloupec50` | nvarchar(80) | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenikyTxtHlav` (CLUSTERED) — `ID`
