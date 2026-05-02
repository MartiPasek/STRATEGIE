# EC_VydanePoptavky_InsertPolozek

**Schema**: dbo · **Cluster**: Other · **Rows**: 37 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCis` | nvarchar(126) | ANO |  |  |
| 3 | `Mnozstvi` | numeric(19,2) | ANO |  |  |
| 4 | `Poptavka` | nvarchar(100) | ANO |  |  |
| 5 | `Zpracovano` | bit | ANO | ((0)) |  |
| 6 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_VydanePoptavky_InsertPolozek` (CLUSTERED) — `ID`
