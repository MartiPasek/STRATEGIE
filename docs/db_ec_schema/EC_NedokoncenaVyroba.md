# EC_NedokoncenaVyroba

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 3 | `Rok` | int | ANO |  |  |
| 4 | `Mesic` | int | ANO |  |  |
| 5 | `HodinyRealNV` | int | ANO |  |  |
| 6 | `NakladyNV` | numeric(18,6) | ANO |  |  |
| 7 | `VynosyNV` | numeric(18,6) | ANO |  |  |
| 8 | `CastkaNV` | numeric(18,6) | ANO |  |  |

## Indexy

- **PK** `PK_dbo.EC_NedokoncenaVyroba` (CLUSTERED) — `ID`
