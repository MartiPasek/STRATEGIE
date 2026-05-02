# EC_ImportXml

**Schema**: dbo · **Cluster**: Other · **Rows**: 7,576,836 · **Size**: 768.52 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDNadrazene` | int | ANO |  |  |
| 2 | `Popis` | nvarchar(50) | ANO |  |  |
| 3 | `Hodnota` | nvarchar(128) | ANO |  |  |
| 4 | `ID` | int | NE |  |  |
| 5 | `IDHlav` | int | NE |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO |  |  |

## Indexy

- **INDEX** `IX_EX_ImportXML` (NONCLUSTERED) — `IDNadrazene, IDHlav`
- **INDEX** `IX_EC_ImportXML_2` (NONCLUSTERED) — `ID, IDHlav`
- **INDEX** `IX_ImportXml_PopisIndex` (NONCLUSTERED) — `Popis, IDHlav`
