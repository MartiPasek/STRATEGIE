# EC_Vytizeni_Poznamky

**Schema**: dbo · **Cluster**: Production · **Rows**: 4 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 3 | `Datum` | date | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Typ` | int | ANO |  |  |
| 8 | `CisloZam` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Poznamky` (CLUSTERED) — `ID`
