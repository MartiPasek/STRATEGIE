# EC_Dotaznik_Uzivatele

**Schema**: dbo · **Cluster**: Other · **Rows**: 3 · **Size**: 0.07 MB · **Sloupců**: 3 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `LoginId` | nvarchar(50) | NE |  |  |
| 3 | `Heslo` | nvarchar(200) | NE |  |  |

## Indexy

- **PK** `PK_EC_Dotaznik_Uzivatele` (CLUSTERED) — `ID`
- **UNIQUE** `IX_EC_Dotaznik_Uzivatele` (NONCLUSTERED) — `LoginId`
