# EC_CenikyTXT

**Schema**: dbo · **Cluster**: Finance · **Rows**: 4,885,445 · **Size**: 1207.82 MB · **Sloupců**: 85 · **FK**: 0 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `RadekExcel` | int | ANO |  |  |
| 4 | `RegCisHeo` | nvarchar(50) | ANO |  |  |
| 35 | `MJ` | nvarchar(5) | ANO |  |  |
| 36 | `BaleniPo` | int | ANO |  |  |
| 37 | `MinDod` | int | ANO |  |  |
| 38 | `CenaZa` | int | ANO |  |  |
| 39 | `EC_PC` | numeric(18,4) | ANO |  |  |
| 40 | `EC_NC` | numeric(18,4) | ANO |  |  |
| 41 | `HmotnostKg` | numeric(18,3) | ANO |  |  |
| 42 | `EAN` | nvarchar(50) | ANO |  |  |
| 43 | `Popis` | nvarchar(300) | ANO |  |  |
| 44 | `RegCisHeoKompres` | nvarchar(4000) | ANO |  |  |
| 45 | `RegCisHeoKod` | nvarchar(80) | ANO |  |  |
| 46 | `RegCisHeoKodKompres` | nvarchar(4000) | ANO |  |  |
| 47 | `Upozorneni` | nvarchar(80) | ANO |  |  |
| 48 | `Par1` | nvarchar(200) | ANO |  |  |
| 49 | `Par2` | nvarchar(200) | ANO |  |  |
| 50 | `Par3` | nvarchar(200) | ANO |  |  |
| 51 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 52 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 53 | `DatPorizeni_D` | int | ANO |  |  |
| 54 | `DatPorizeni_M` | int | ANO |  |  |
| 55 | `DatPorizeni_Y` | int | ANO |  |  |
| 56 | `DatPorizeni_Q` | int | ANO |  |  |
| 57 | `DatPorizeni_W` | int | ANO |  |  |
| 58 | `DatPorizeni_X` | datetime | ANO |  |  |
| 59 | `Mena` | nvarchar(3) | ANO |  |  |
| 60 | `DatZmeny` | datetime | ANO |  |  |
| 61 | `EC_PRC` | numeric(18,4) | ANO |  |  |
| 62 | `Rabat_N` | numeric(6,1) | ANO |  |  |
| 63 | `Rabat_P` | numeric(6,1) | ANO |  |  |
| 64 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 85 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 86 | `Sloupec01` | nvarchar(80) | ANO |  |  |
| 87 | `Sloupec02` | nvarchar(80) | ANO |  |  |
| 88 | `Sloupec03` | nvarchar(80) | ANO |  |  |
| 89 | `Sloupec04` | nvarchar(80) | ANO |  |  |
| 90 | `Sloupec05` | nvarchar(80) | ANO |  |  |
| 91 | `Sloupec06` | nvarchar(80) | ANO |  |  |
| 92 | `Sloupec07` | nvarchar(80) | ANO |  |  |
| 93 | `Sloupec08` | nvarchar(80) | ANO |  |  |
| 94 | `Sloupec09` | nvarchar(80) | ANO |  |  |
| 95 | `Sloupec10` | nvarchar(80) | ANO |  |  |
| 96 | `Sloupec11` | nvarchar(80) | ANO |  |  |
| 97 | `Sloupec12` | nvarchar(80) | ANO |  |  |
| 98 | `Sloupec13` | nvarchar(80) | ANO |  |  |
| 99 | `Sloupec14` | nvarchar(80) | ANO |  |  |
| 100 | `Sloupec15` | nvarchar(80) | ANO |  |  |
| 101 | `Sloupec16` | nvarchar(80) | ANO |  |  |
| 102 | `Sloupec17` | nvarchar(80) | ANO |  |  |
| 103 | `Sloupec18` | nvarchar(80) | ANO |  |  |
| 104 | `Sloupec19` | nvarchar(80) | ANO |  |  |
| 105 | `Sloupec20` | nvarchar(80) | ANO |  |  |
| 106 | `Sloupec21` | nvarchar(80) | ANO |  |  |
| 107 | `Sloupec22` | nvarchar(80) | ANO |  |  |
| 108 | `Sloupec23` | nvarchar(80) | ANO |  |  |
| 109 | `Sloupec24` | nvarchar(80) | ANO |  |  |
| 110 | `Sloupec25` | nvarchar(80) | ANO |  |  |
| 111 | `Sloupec26` | nvarchar(80) | ANO |  |  |
| 112 | `Sloupec27` | nvarchar(80) | ANO |  |  |
| 113 | `Sloupec28` | nvarchar(80) | ANO |  |  |
| 114 | `Sloupec29` | nvarchar(80) | ANO |  |  |
| 115 | `Sloupec30` | nvarchar(80) | ANO |  |  |
| 116 | `Sloupec31` | nvarchar(80) | ANO |  |  |
| 117 | `Sloupec32` | nvarchar(80) | ANO |  |  |
| 118 | `Sloupec33` | nvarchar(80) | ANO |  |  |
| 119 | `Sloupec34` | nvarchar(80) | ANO |  |  |
| 120 | `Sloupec35` | nvarchar(80) | ANO |  |  |
| 121 | `Sloupec36` | nvarchar(80) | ANO |  |  |
| 122 | `Sloupec37` | nvarchar(80) | ANO |  |  |
| 123 | `Sloupec38` | nvarchar(80) | ANO |  |  |
| 124 | `Sloupec39` | nvarchar(80) | ANO |  |  |
| 125 | `Sloupec40` | nvarchar(80) | ANO |  |  |
| 126 | `Sloupec41` | nvarchar(80) | ANO |  |  |
| 127 | `Sloupec42` | nvarchar(80) | ANO |  |  |
| 128 | `Sloupec43` | nvarchar(80) | ANO |  |  |
| 129 | `Sloupec44` | nvarchar(80) | ANO |  |  |
| 130 | `Sloupec45` | nvarchar(80) | ANO |  |  |
| 131 | `Sloupec46` | nvarchar(80) | ANO |  |  |
| 132 | `Sloupec47` | nvarchar(80) | ANO |  |  |
| 133 | `Sloupec48` | nvarchar(80) | ANO |  |  |
| 134 | `Sloupec49` | nvarchar(80) | ANO |  |  |
| 135 | `Sloupec50` | nvarchar(80) | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenikyTXT` (CLUSTERED) — `ID`
- **INDEX** `Popis` (NONCLUSTERED) — `Popis`
- **INDEX** `RegCisHeo` (NONCLUSTERED) — `RegCisHeo`
- **INDEX** `RegCisHeoKompres` (NONCLUSTERED) — `RegCisHeoKompres`
