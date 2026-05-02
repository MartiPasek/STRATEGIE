# EC_Regaly_Typy

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Typ` | int | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 6 | `Popis` | nvarchar(1000) | ANO |  |  |
| 7 | `PoradiZobrazeni` | tinyint | ANO |  |  |

## Indexy

- **PK** `PK_EC_Regaly_Typy` (CLUSTERED) — `ID`
