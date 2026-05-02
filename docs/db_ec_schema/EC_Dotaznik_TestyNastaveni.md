# EC_Dotaznik_TestyNastaveni

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 3 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IdHlav` | int | NE |  |  |
| 3 | `VsechnyOtazkyNajednou` | bit | NE | ((0)) |  |

## Cizí klíče (declared)

- `IdHlav` → [`EC_Dotaznik_TestyHlav`](EC_Dotaznik_TestyHlav.md).`ID` _(constraint: `FK_EC_Dotaznik_TestyNastaveni_EC_Dotaznik_TestyHlav`)_

## Indexy

- **PK** `PK_EC_Dotaznik_TestyNastaveni` (CLUSTERED) — `ID`
