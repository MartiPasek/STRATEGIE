# EC_Grid_SloupceVazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 476 · **Size**: 0.20 MB · **Sloupců**: 15 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDSloupce` | int | NE |  |  |
| 3 | `IDPodminky` | int | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |
| 8 | `DatPorizeni_D` | int | ANO |  |  |
| 9 | `DatPorizeni_M` | int | ANO |  |  |
| 10 | `DatPorizeni_Y` | int | ANO |  |  |
| 11 | `DatPorizeni_Q` | int | ANO |  |  |
| 12 | `DatPorizeni_W` | int | ANO |  |  |
| 13 | `DatPorizeni_X` | datetime | ANO |  |  |
| 14 | `Poradi` | tinyint | ANO |  |  |
| 15 | `IndRowSelect` | bit | NE | ((0)) |  |

## Cizí klíče (declared)

- `IDSloupce` → [`EC_Grid_Sloupce`](EC_Grid_Sloupce.md).`ID` _(constraint: `FK_EC_Grid_SloupceVazby_IDSloupce`)_
- `IDPodminky` → [`EC_DELPHI_TabObecnyPrehledPodminky`](EC_DELPHI_TabObecnyPrehledPodminky.md).`ID` _(constraint: `FK_EC_Grid_SloupceVazby_IDPodminky`)_

## Indexy

- **PK** `PK_EC_Grid_SloupceVazby` (CLUSTERED) — `ID`
