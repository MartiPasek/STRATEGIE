# EC_Dotaznik_TestyObrazky

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 4 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IdPol` | int | NE |  |  |
| 3 | `Popis` | nvarchar(50) | ANO |  |  |
| 4 | `Url` | nvarchar(200) | NE |  |  |

## Cizí klíče (declared)

- `IdPol` → [`EC_Dotaznik_TestyPol`](EC_Dotaznik_TestyPol.md).`ID` _(constraint: `FK_EC_Dotaznik_TestyObrazky_EC_Dotaznik_TestyPol`)_

## Indexy

- **PK** `PK_EC_Dotaznik_TestyObrazky` (CLUSTERED) — `ID`
