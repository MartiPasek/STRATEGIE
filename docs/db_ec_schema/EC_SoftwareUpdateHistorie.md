# EC_SoftwareUpdateHistorie

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,088 · **Size**: 0.27 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `CisZam` | int | NE |  |  |
| 3 | `SoftwareID` | int | NE |  |  |
| 4 | `SoftwareVersion_Old` | int | ANO |  |  |
| 5 | `SoftwareVersion_New` | int | NE |  |  |
| 6 | `VysledekUpdate` | nvarchar(200) | ANO |  |  |
| 7 | `DateUpdate` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_SoftwareUpdateHistorie` (CLUSTERED) — `id`
