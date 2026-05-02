# EC_TabEmailAttachments

**Schema**: dbo · **Cluster**: CRM · **Rows**: 24,305 · **Size**: 5.43 MB · **Sloupců**: 10 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDEmail` | int | NE |  |  |
| 3 | `DisplayName` | nvarchar(500) | ANO |  |  |
| 4 | `FileName` | nvarchar(500) | ANO |  |  |
| 5 | `PathName` | nvarchar(1000) | ANO |  |  |
| 6 | `CreationTime` | datetime | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `IDEmail` → [`EC_TabEmails`](EC_TabEmails.md).`ID` _(constraint: `FK_EC_TabEmailAttachments_EC_TabEmails`)_

## Indexy

- **PK** `PK_EC_TabEmailAttachments` (CLUSTERED) — `ID`
