# EC_TabUKOD

**Schema**: dbo · **Cluster**: Finance · **Rows**: 74 · **Size**: 0.03 MB · **Sloupců**: 47 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloKontace` | int | NE |  |  |
| 3 | `DruhPohybu` | tinyint | NE |  |  |
| 4 | `RadaDokladu` | nvarchar(3) | ANO |  |  |
| 5 | `Nazev` | nvarchar(100) | NE |  |  |
| 6 | `DatumOd` | datetime | NE |  |  |
| 7 | `DatumDo` | datetime | NE |  |  |
| 8 | `Sbornik` | nvarchar(3) | ANO |  |  |
| 9 | `Editace` | nchar(1) | NE |  |  |
| 10 | `Zakladni` | bit | NE |  |  |
| 11 | `VypocetDane` | tinyint | ANO |  |  |
| 12 | `Seskupovat` | bit | NE |  |  |
| 13 | `NedotahovatUcty` | bit | NE |  |  |
| 14 | `Autor` | nvarchar(128) | NE |  |  |
| 15 | `DatPorizeni` | datetime | NE |  |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 19 | `DatumOd_D` | int | ANO |  |  |
| 20 | `DatumOd_M` | int | ANO |  |  |
| 21 | `DatumOd_Y` | int | ANO |  |  |
| 22 | `DatumOd_Q` | int | ANO |  |  |
| 23 | `DatumOd_W` | int | ANO |  |  |
| 24 | `DatumOd_X` | datetime | ANO |  |  |
| 25 | `DatumDo_D` | int | ANO |  |  |
| 26 | `DatumDo_M` | int | ANO |  |  |
| 27 | `DatumDo_Y` | int | ANO |  |  |
| 28 | `DatumDo_Q` | int | ANO |  |  |
| 29 | `DatumDo_W` | int | ANO |  |  |
| 30 | `DatumDo_X` | datetime | ANO |  |  |
| 31 | `DatPorizeni_D` | int | ANO |  |  |
| 32 | `DatPorizeni_M` | int | ANO |  |  |
| 33 | `DatPorizeni_Y` | int | ANO |  |  |
| 34 | `DatPorizeni_Q` | int | ANO |  |  |
| 35 | `DatPorizeni_W` | int | ANO |  |  |
| 36 | `DatPorizeni_X` | datetime | ANO |  |  |
| 37 | `DatZmeny_D` | int | ANO |  |  |
| 38 | `DatZmeny_M` | int | ANO |  |  |
| 39 | `DatZmeny_Y` | int | ANO |  |  |
| 40 | `DatZmeny_Q` | int | ANO |  |  |
| 41 | `DatZmeny_W` | int | ANO |  |  |
| 42 | `DatZmeny_X` | datetime | ANO |  |  |
| 43 | `ZastupujiciClen` | bit | NE |  |  |
| 44 | `KRDatumPripad` | bit | NE |  |  |
| 45 | `HlavniOsCislo` | bit | NE |  |  |
| 46 | `SpecProPO` | bit | NE |  |  |
| 47 | `Preuctovat` | bit | NE |  |  |
