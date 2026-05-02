# EC_PP_AvizoPol

**Schema**: dbo · **Cluster**: Other · **Rows**: 309 · **Size**: 0.07 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `TypPP` | int | ANO |  |  |
| 4 | `TypPPtext` | varchar(4) | NE |  |  |
| 5 | `IDOrg` | int | ANO |  |  |
| 6 | `IDBankSpojeni` | int | ANO |  |  |
| 7 | `ID_HlavPP` | int | ANO |  |  |
| 8 | `ID_PolPP` | int | ANO |  |  |
| 9 | `Zobrazeno` | bit | ANO |  |  |
| 10 | `DatZobrazeni` | datetime | ANO |  |  |
| 11 | `KdoZobrazil` | nvarchar(128) | ANO |  |  |
| 12 | `Odeslano` | bit | ANO | ((0)) |  |
| 13 | `DatumOdeslani` | datetime | ANO |  |  |
| 14 | `KdoOdeslal` | nvarchar(128) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | ANO | (suser_name()) |  |
| 16 | `DatumPorizeni` | datetime | ANO | (getdate()) |  |
| 17 | `A_Poradi` | int | ANO |  |  |
| 18 | `A_VariabilniSymbol` | nvarchar(20) | ANO |  |  |
| 19 | `A_DENgenerovani` | datetime | ANO |  |  |
| 20 | `A_Castka` | numeric(19,6) | ANO |  |  |
| 21 | `A_Mena` | nvarchar(4) | ANO |  |  |

## Implicitní vztahy (heuristic, NE declared FK)

- `IDOrg` → pravděpodobně `TabCisOrg`

> _Marti-AI: Heliosové tabulky často nepoužívají declared FK. Vztah je dohadován z naming convention. Pro jistotu ověř před joiny._

## Indexy

- **PK** `PK_EC_PP_Avizo` (CLUSTERED) — `ID`
