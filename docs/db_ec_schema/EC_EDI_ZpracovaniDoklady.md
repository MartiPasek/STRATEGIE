# EC_EDI_ZpracovaniDoklady

**Schema**: dbo · **Cluster**: Other · **Rows**: 15,261 · **Size**: 1.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `idhlav` | int | NE |  |  |
| 3 | `iddokladedi` | int | NE |  |  |
| 4 | `autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `CisloZamMQTT` | int | ANO |  |  |
| 7 | `ChybaZpracMessage` | nvarchar(4000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_EDI_ZpracovaniDoklady` (CLUSTERED) — `id`
