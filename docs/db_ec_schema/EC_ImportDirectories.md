# EC_ImportDirectories

**Schema**: dbo · **Cluster**: Other · **Rows**: 27 · **Size**: 0.27 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `enable` | bit | NE | ((0)) |  |
| 3 | `path` | nvarchar(500) | ANO |  |  |
| 4 | `ext` | nvarchar(100) | ANO |  |  |
| 5 | `POPIS` | nvarchar(1000) | ANO |  |  |
| 6 | `pathArchive` | nvarchar(500) | ANO |  |  |
| 7 | `typImportu` | tinyint | NE | ((1)) |  |
| 8 | `ExtToolPath` | nvarchar(500) | ANO |  |  |
| 9 | `NameStoredProc` | nvarchar(100) | ANO |  |  |
| 10 | `DbProImport` | nvarchar(100) | ANO |  |  |
| 11 | `ProceduraProZprac` | nvarchar(100) | ANO |  |  |
| 12 | `CisloOrg` | int | ANO |  |  |
| 13 | `SqlSelectDoExcel` | nvarchar(1000) | ANO | ('') |  |
| 14 | `PopisImportu` | ntext | ANO |  |  |
| 15 | `ExePath` | nvarchar(500) | ANO |  |  |

## Indexy

- **PK** `PK_EC_ImportDirectories` (CLUSTERED) — `id`
