# EC_Mzdy_LandMarkVstupniData

**Schema**: dbo · **Cluster**: HR · **Rows**: 3,279 · **Size**: 0.79 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Mesic` | int | ANO |  |  |
| 3 | `Rok` | int | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `PracUvazekT` | int | ANO |  |  |
| 6 | `FondMes` | numeric(18,2) | ANO |  |  |
| 7 | `PocetDniPrace` | numeric(18,2) | ANO |  |  |
| 8 | `PraceHod` | numeric(18,2) | ANO |  |  |
| 9 | `DovolenaHod` | numeric(18,2) | ANO |  |  |
| 10 | `PrescasyHod` | numeric(18,2) | ANO |  |  |
| 11 | `NarizeneVolnoHod` | numeric(18,2) | ANO |  |  |
| 12 | `NeplaceneVolno` | numeric(18,2) | ANO |  |  |
| 13 | `Zaklad` | numeric(18,2) | ANO |  |  |
| 14 | `OsOhod` | numeric(18,2) | ANO |  |  |
| 15 | `Firma` | int | ANO |  |  |
| 16 | `Smlouva` | nvarchar(20) | ANO |  |  |
| 17 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 18 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Mzdy_LandMarkVstupniData` (CLUSTERED) — `ID`
