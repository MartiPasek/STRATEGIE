# EC_AutZprDefPol_XML

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 25 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPolDefinice` | int | ANO |  |  |
| 3 | `ParentElementName` | nvarchar(MAX) | NE | ('') |  |
| 4 | `AttributeName` | nvarchar(MAX) | NE | ('') |  |
| 6 | `FieldName_AutZprDokladPol` | nvarchar(MAX) | NE | ('') |  |

## Indexy

- **PK** `PK_EC_AutZprDokladPol_XML` (CLUSTERED) — `ID`
