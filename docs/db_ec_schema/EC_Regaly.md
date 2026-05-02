# EC_Regaly

**Schema**: dbo · **Cluster**: Other · **Rows**: 290 · **Size**: 0.20 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevSkladu` | nvarchar(8) | NE |  |  |
| 3 | `CisloSloupce` | int | NE |  |  |
| 4 | `PocetPolic` | tinyint | NE | ((1)) |  |
| 5 | `PoziceMimoRegal` | tinyint | ANO |  |  |
| 6 | `EvidencniCislo` | int | ANO |  |  |
| 7 | `NosnostPolice` | int | ANO |  |  |
| 8 | `Popis` | nvarchar(200) | ANO |  |  |
| 9 | `Poznamka` | ntext | ANO |  |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Regaly` (CLUSTERED) — `ID`
