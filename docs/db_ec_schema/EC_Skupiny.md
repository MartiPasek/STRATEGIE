# EC_Skupiny

**Schema**: dbo · **Cluster**: Other · **Rows**: 40 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(50) | ANO |  |  |
| 3 | `OdpovedneOsoby` | nvarchar(200) | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `OdpovedneOsobyDoch` | nvarchar(200) | ANO |  |  |
| 6 | `OdpovedneOsSchvalVolno` | nvarchar(200) | ANO |  |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | ANO | (getdate()) |  |
| 12 | `AutDokoncitUkol` | bit | ANO | ((0)) |  |
| 13 | `OdpovedneOsobyPrescasy` | nvarchar(200) | ANO |  |  |
| 14 | `PocetVzajemnychDovolenych` | int | ANO |  |  |
| 15 | `PrekryvVolna` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Skupiny` (CLUSTERED) — `ID`
