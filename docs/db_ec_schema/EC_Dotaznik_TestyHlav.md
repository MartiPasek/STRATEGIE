# EC_Dotaznik_TestyHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nchar(200) | NE |  | Název testu |
| 3 | `Ukonceno` | bit | NE | ((0)) | Příznak o tom, jestli byl test dokončen |
| 4 | `Aktivni` | bit | NE |  | Příznak o tom, jestli má uživatel aktivní test |

## Indexy

- **PK** `PK_EC_Dotaznik_TestyHlav` (CLUSTERED) — `ID`
