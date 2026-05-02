# EC_Exchange_UserFolders

**Schema**: dbo · **Cluster**: CRM · **Rows**: 1 · **Size**: 0.08 MB · **Sloupců**: 3 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUser` | int | NE |  |  |
| 3 | `FolderName` | nvarchar(128) | ANO |  |  |

## Cizí klíče (declared)

- `IDUser` → [`EC_Exchange_Users`](EC_Exchange_Users.md).`ID` _(constraint: `FK_EC_Exchange_UserFolders_EC_Exchange_Users`)_

## Indexy

- **PK** `PK_EC_Exchange_UserFolders` (CLUSTERED) — `ID`
