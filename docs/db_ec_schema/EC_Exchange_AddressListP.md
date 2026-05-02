# EC_Exchange_AddressListP

**Schema**: dbo · **Cluster**: CRM · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDAddressList` | int | NE |  |  |
| 3 | `Address` | nvarchar(255) | ANO |  |  |
| 4 | `RegEx` | bit | NE | ((0)) |  |
| 5 | `Description` | nvarchar(255) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Exchange_AddressListP` (CLUSTERED) — `ID`
