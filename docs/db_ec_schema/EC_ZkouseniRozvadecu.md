# EC_ZkouseniRozvadecu

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,271 · **Size**: 0.59 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Stav` | int | ANO |  |  |
| 3 | `VyzkousenoOk` | bit | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |
| 7 | `Zmenil` | nvarchar(20) | ANO |  |  |
| 8 | `PlanyNaZkousky` | datetime | ANO |  |  |
| 9 | `ZkusebniAMericiProtokoly` | nvarchar(2000) | ANO |  |  |
| 10 | `Zkousejici` | nvarchar(20) | ANO |  |  |
| 11 | `PrectenZl` | bit | ANO |  |  |
| 12 | `Poznamka` | nvarchar(2000) | ANO |  |  |
| 13 | `ZkouskyDatum` | datetime | ANO |  |  |
| 14 | `IDDoprava` | int | ANO |  |  |
| 15 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 16 | `Splneno` | bit | ANO |  |  |
| 17 | `KonecnaZkouska` | bit | ANO |  |  |
| 18 | `Zkousejici1` | int | ANO |  |  |
| 19 | `Zkousejici2` | int | ANO |  |  |
| 20 | `Zkousejici3` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ZkouseniRozvadecu` (CLUSTERED) — `ID`
