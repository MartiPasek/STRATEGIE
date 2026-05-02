# EC_Evidence_Prav

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `IDEPristroje` | int | ANO |  |  |
| 3 | `CisZam` | int | ANO |  |  |
| 4 | `IDPrava` | int | NE |  |  |
| 5 | `IDHistoriePrav` | int | ANO |  |  |
| 6 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDPrava` → [`EC_Evidence_SeznamPrav`](EC_Evidence_SeznamPrav.md).`id` _(constraint: `FK_EC_Evidence_Prav_Prav`)_
- `IDHistoriePrav` → [`EC_Evidence_HistoriePrav`](EC_Evidence_HistoriePrav.md).`id` _(constraint: `FK_EC_Evidence_Prav_Historie`)_

## Indexy

- **PK** `PK__EC_Evide__3213E83F7D287CCE` (CLUSTERED) — `id`
