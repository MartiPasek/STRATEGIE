# EC_EDI_Zpracovani

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,118 · **Size**: 22.77 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `Poznamka` | ntext | ANO |  |  |
| 3 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 5 | `CisloZamMQTT` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_EDI_ZpracovaneDoklady` (CLUSTERED) — `id`
