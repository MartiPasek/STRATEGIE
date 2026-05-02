# EC_Vytizeni_UdalostiSuma

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Barva` | nvarchar(100) | ANO |  |  |
| 4 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 5 | `CisloZakazky` | nvarchar(30) | ANO |  |  |
| 6 | `Datum` | date | ANO |  |  |
| 7 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `TypUdalosti` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_UdalostiSuma` (CLUSTERED) — `ID`
