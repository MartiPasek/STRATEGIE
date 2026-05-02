# EC_Grid_Sloupce

**Schema**: dbo · **Cluster**: Other · **Rows**: 51,741 · **Size**: 5.88 MB · **Sloupců**: 16 · **FK**: 1 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `ColIndex` | smallint | ANO |  |  |
| 4 | `Visible` | bit | NE | ((1)) |  |
| 5 | `ColNazev` | nvarchar(50) | NE |  |  |
| 6 | `ColSirka` | smallint | NE | ((80)) |  |
| 7 | `ColPopis` | nvarchar(50) | ANO |  |  |
| 8 | `ColTittleColor` | int | ANO |  |  |
| 9 | `ColColor` | int | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `IndPodminky` | bit | ANO |  |  |
| 15 | `FilterString` | nvarchar(1000) | ANO | ('') |  |
| 16 | `FilterStringText` | nvarchar(1000) | ANO | ('') |  |

## Cizí klíče (declared)

- `IDHlav` → [`EC_Grid_SloupceHlav`](EC_Grid_SloupceHlav.md).`ID` _(constraint: `FK_EC_Grid_Sloupce_EC_Grid_SloupceHlav`)_

## Indexy

- **PK** `PK_EC_Grid_Sloupce` (CLUSTERED) — `ID`
- **INDEX** `IDHlav` (NONCLUSTERED) — `IDHlav`
- **INDEX** `IDHlav_Includes` (NONCLUSTERED) — `ColNazev, IDHlav`
