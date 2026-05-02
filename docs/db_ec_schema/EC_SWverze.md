# EC_SWverze

**Schema**: dbo · **Cluster**: Other · **Rows**: 254 · **Size**: 0.26 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_SW` | int | NE |  |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `Status` | tinyint | NE | ((0)) |  |
| 5 | `StatusText` | varchar(21) | ANO |  |  |
| 6 | `CasRazitko` | nvarchar(800) | ANO |  |  |
| 7 | `DatUvolneni` | datetime | ANO |  |  |
| 8 | `AutorUvolneni` | nvarchar(128) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SWverze` (CLUSTERED) — `ID`
