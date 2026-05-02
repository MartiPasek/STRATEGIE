# EC_EmailPomocnaTab

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `From` | nvarchar(100) | ANO |  |  |
| 2 | `To_` | nvarchar(250) | ANO |  |  |
| 3 | `CC` | nvarchar(250) | ANO |  |  |
| 4 | `Subject` | nvarchar(250) | ANO |  |  |
| 5 | `Body` | nvarchar(MAX) | ANO |  |  |
| 6 | `RTFBody` | nvarchar(MAX) | ANO |  |  |
| 7 | `HTMLBody` | nvarchar(MAX) | ANO |  |  |
| 8 | `Attachements` | nvarchar(MAX) | ANO |  |  |
| 9 | `Categories` | nvarchar(100) | ANO |  |  |
| 10 | `CreationDate` | datetime | ANO |  |  |
| 11 | `GUID` | uniqueidentifier | ANO |  |  |
