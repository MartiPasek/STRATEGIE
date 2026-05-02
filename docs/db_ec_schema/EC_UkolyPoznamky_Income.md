# EC_UkolyPoznamky_Income

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 6.77 MB · **Sloupců**: 14 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUkol` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Poznamka` | ntext | ANO |  |  |
| 5 | `Tisk` | bit | NE | ((1)) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `DruhZmeny` | tinyint | ANO |  |  |
| 11 | `Poznamka_Bin` | varbinary(MAX) | ANO |  |  |
| 12 | `ZaznamVlozil` | nvarchar(126) | ANO | (suser_sname()) |  |
| 13 | `Zpracovano` | bit | ANO | ((0)) |  |
| 14 | `DatZpracovani` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDUkol` → [`EC_Ukoly`](EC_Ukoly.md).`ID` _(constraint: `FK_EC_UkolyPoznamky_Income_EC_Ukoly`)_

## Indexy

- **PK** `PK_EC_UkolyPoznamky_Income` (CLUSTERED) — `ID`
