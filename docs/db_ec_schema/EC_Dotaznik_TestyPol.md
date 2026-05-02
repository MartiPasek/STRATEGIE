# EC_Dotaznik_TestyPol

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IdHlav` | int | NE |  |  |
| 3 | `Nazev` | nvarchar(200) | NE |  |  |
| 4 | `Popis` | nvarchar(MAX) | ANO |  |  |
| 6 | `OtevrenaOtazka` | bit | NE | ((0)) |  |
| 7 | `Poradi` | int | ANO |  |  |
| 8 | `Odpoved` | int | ANO |  |  |
| 9 | `Komentar` | nvarchar(200) | ANO |  |  |

## Cizí klíče (declared)

- `IdHlav` → [`EC_Dotaznik_TestyHlav`](EC_Dotaznik_TestyHlav.md).`ID` _(constraint: `FK_EC_Dotaznik_TestyPol_EC_Dotaznik_TestyHlav`)_

## Indexy

- **PK** `PK_EC_Dotaznik_TestyPol` (CLUSTERED) — `ID`
