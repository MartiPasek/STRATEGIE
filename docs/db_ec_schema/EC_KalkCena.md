# EC_KalkCena

**Schema**: dbo · **Cluster**: Production · **Rows**: 2,029 · **Size**: 0.45 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `Typ` | tinyint | NE | ((0)) |  |
| 4 | `TypText` | varchar(3) | NE |  |  |
| 5 | `KalkCena` | numeric(18,6) | ANO |  |  |
| 6 | `Mena` | nvarchar(3) | NE | (N'EUR') |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Blokovano` | bit | NE | ((0)) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `IndArchiv` | int | NE |  |  |

## Indexy

- **PK** `PK_EC_KalkCena` (CLUSTERED) — `ID`
