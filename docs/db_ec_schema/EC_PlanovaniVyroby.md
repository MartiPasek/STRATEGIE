# EC_PlanovaniVyroby

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,810 · **Size**: 0.39 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloZakazky` | varchar(15) | ANO |  |  |
| 4 | `DatumOd` | datetime | ANO |  |  |
| 5 | `DatumDo` | datetime | ANO |  |  |
| 6 | `ZamPoznamka` | varchar(80) | ANO |  |  |
| 7 | `VedPoznamka` | varchar(80) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_PlanovaniVyroby` (CLUSTERED) — `ID`
