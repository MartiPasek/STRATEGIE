# EC_UkolyPoznamky

**Schema**: dbo · **Cluster**: Other · **Rows**: 52,934 · **Size**: 790.91 MB · **Sloupců**: 10 · **FK**: 1 · **Indexů**: 2

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
| 10 | `Poznamka_Bin` | varbinary(MAX) | ANO |  |  |

## Cizí klíče (declared)

- `IDUkol` → [`EC_Ukoly`](EC_Ukoly.md).`ID` _(constraint: `FK_EC_UkolyPoznamky_EC_Ukoly`)_

## Indexy

- **PK** `PK_EC_UkolyPoznamky` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_UkolyPoznamka_IDUkol` (NONCLUSTERED) — `ID, Tisk, Autor, DatPorizeni, Zmenil, DatZmeny, Poznamka_Bin, CisloZam, IDUkol`
