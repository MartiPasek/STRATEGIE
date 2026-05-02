# EC_FormDefComponentProperty

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 319 · **Size**: 0.20 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | int | NE |  |  |
| 3 | `Property` | nvarchar(50) | ANO |  |  |
| 4 | `Value` | nvarchar(50) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `FMX` | tinyint | ANO | ((1)) | 1 = VLC, 2 = FMX |

## Indexy

- **PK** `PK_EC_FormDefComponentPol` (CLUSTERED) — `ID`
