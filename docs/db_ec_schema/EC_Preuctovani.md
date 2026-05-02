# EC_Preuctovani

**Schema**: dbo · **Cluster**: Other · **Rows**: 9 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(50) | NE |  |  |
| 3 | `OsCislo` | int | NE |  |  |
| 4 | `Hodnota` | numeric(18,2) | NE |  |  |
| 5 | `SmerPlneni` | smallint | NE |  |  |
| 6 | `HodnotaSmer` | numeric(18,2) | NE |  |  |
| 7 | `DatumVyuct` | datetime | ANO |  |  |
| 8 | `CisloOrg` | int | ANO |  |  |
| 9 | `Descr` | nvarchar(100) | ANO |  |  |
| 10 | `CisloDokladu` | nvarchar(20) | ANO |  |  |
| 11 | `Poznamka1` | nvarchar(100) | ANO |  |  |
| 12 | `DatumVloz` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Preuctovani` (CLUSTERED) — `id`
