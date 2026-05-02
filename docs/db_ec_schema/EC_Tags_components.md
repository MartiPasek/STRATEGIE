# EC_Tags_components

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `tag_name` | nvarchar(100) | ANO |  |  |
| 3 | `ip` | nvarchar(15) | ANO |  |  |
| 4 | `login` | nvarchar(25) | ANO |  |  |
| 5 | `id_form` | nvarchar(25) | ANO |  |  |
| 6 | `id_component` | nvarchar(25) | ANO |  |  |
| 7 | `spid` | int | ANO | (@@spid) |  |
| 8 | `autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 9 | `dat_vytvoreni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Tags_components` (CLUSTERED) — `id`
