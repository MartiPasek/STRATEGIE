# EC_ZamestFinan

**Schema**: dbo · **Cluster**: Other · **Rows**: 197 · **Size**: 0.02 MB · **Sloupců**: 7 · **FK**: 1 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloZam` | int | NE |  |  |
| 2 | `DatumPor` | datetime | ANO | (getdate()) |  |
| 3 | `KalkVykon` | numeric(2,1) | NE |  |  |
| 4 | `MinSazbaKc` | int | NE | ((0)) |  |
| 5 | `FixSazbaKc` | int | NE | ((0)) |  |
| 6 | `StupenZvyhod` | int | NE | ((0)) |  |
| 7 | `ID` | int | NE |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_ZamestFinan_TabCisZam`)_
