# EC_ZakazkyReference

**Schema**: dbo · **Cluster**: Finance · **Rows**: 28 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloZak` | int | ANO |  |  |
| 4 | `KonkretniZakazka` | nvarchar(50) | ANO |  |  |
| 5 | `ReferenceKladna` | bit | ANO |  |  |
| 6 | `ReferenceZaporna` | bit | ANO |  |  |
| 7 | `Priloha` | nvarchar(50) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 12 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZakazkyReference` (CLUSTERED) — `ID`
