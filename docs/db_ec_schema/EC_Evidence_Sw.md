# EC_Evidence_Sw

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 11 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `IDSw` | int | NE |  |  |
| 3 | `IDEPristroje` | int | ANO |  |  |
| 4 | `DatInstalace` | date | ANO |  |  |
| 5 | `DatAktualizace` | date | ANO |  |  |
| 6 | `DatOdinstalace` | date | ANO |  |  |
| 7 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDSw` → [`EC_Evidence_SeznamSw`](EC_Evidence_SeznamSw.md).`id` _(constraint: `FK_EC_Evidence_Sw_Sw`)_

## Indexy

- **PK** `PK__EC_Evide__3213E83F5A1730F5` (CLUSTERED) — `id`
