# EC_Vytizeni_Vypomoci

**Schema**: dbo · **Cluster**: Production · **Rows**: 44 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | nvarchar(10) | ANO |  |  |
| 3 | `Datum` | date | ANO |  |  |
| 4 | `PocetHodin` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `Poznamka` | nvarchar(4000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Vypomoci` (CLUSTERED) — `ID`
