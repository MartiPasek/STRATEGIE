# EC_CashFlow

**Schema**: dbo · **Cluster**: Finance · **Rows**: 100 · **Size**: 0.20 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Prijmy` | numeric(18,2) | ANO |  |  |
| 3 | `Vydaje` | numeric(18,2) | ANO |  |  |
| 4 | `Bilance` | numeric(18,2) | ANO |  |  |
| 5 | `DatSplatnostiDo` | datetime | ANO |  |  |
| 6 | `VF` | numeric(18,2) | ANO |  |  |
| 7 | `POBj` | numeric(18,2) | ANO |  |  |
| 8 | `FP` | numeric(18,2) | ANO |  |  |
| 9 | `FP_ES` | numeric(18,2) | ANO |  |  |
| 10 | `VOBj` | numeric(18,2) | ANO |  |  |
| 11 | `FakturaceSW` | numeric(18,2) | ANO |  |  |
| 12 | `Poznamka` | nvarchar(250) | ANO |  |  |
| 13 | `ZustatekNaUctu` | numeric(18,2) | ANO |  |  |
| 14 | `ZustatekKDatSplatnosti` | numeric(18,2) | ANO |  |  |
| 15 | `VFpoSplatnosti` | numeric(18,2) | ANO |  |  |
| 16 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 17 | `DatAktualizace` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_CashFlow` (CLUSTERED) — `ID`
