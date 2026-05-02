# EC_DeveloperToolsType

**Schema**: dbo · **Cluster**: Other · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 3 | `ToolNazev` | nvarchar(256) | ANO |  |  |
| 4 | `ToolPopis` | nvarchar(2000) | ANO |  |  |
| 5 | `Autor` | nvarchar(256) | NE | (suser_name()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(256) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DeveloperToolsType` (CLUSTERED) — `ID`
