# EC_KristynaTest

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | int | ANO |  |  |
| 3 | `SeznamDilu` | nvarchar(4000) | ANO |  |  |
| 4 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_KristynaTest` (CLUSTERED) — `ID`
