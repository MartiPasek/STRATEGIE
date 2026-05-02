# EC_ObaloveHospodarstvi

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,122 · **Size**: 0.45 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 3 | `StrecovaFolie_kg` | numeric(18,6) | ANO |  |  |
| 4 | `KartonRittal_kg` | numeric(18,6) | ANO |  |  |
| 5 | `KrabicePribal_kg` | numeric(18,6) | ANO |  |  |
| 6 | `Palety_kg` | numeric(18,6) | ANO |  |  |
| 7 | `VazaciPaska_kg` | numeric(18,6) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 9 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObaloveHospodarstvi` (CLUSTERED) — `ID`
