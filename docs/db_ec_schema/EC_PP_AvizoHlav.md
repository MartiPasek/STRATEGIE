# EC_PP_AvizoHlav

**Schema**: dbo · **Cluster**: Other · **Rows**: 44 · **Size**: 0.07 MB · **Sloupců**: 31 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TypPP` | int | ANO |  |  |
| 3 | `TypPPtext` | varchar(4) | NE |  |  |
| 4 | `IDOrg` | int | ANO |  |  |
| 5 | `Zobrazeno` | bit | ANO |  |  |
| 6 | `DatZobrazeni` | datetime | ANO |  |  |
| 7 | `KdoZobrazil` | nvarchar(128) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | ANO |  |  |
| 10 | `A_SumaCelkem` | numeric(19,6) | ANO |  |  |
| 11 | `A_KodUstavu` | nvarchar(15) | ANO |  |  |
| 12 | `A_CisloUctu` | nvarchar(40) | ANO |  |  |
| 13 | `A_OrgNazev` | nvarchar(200) | ANO |  |  |
| 14 | `A_CelkovaCastka` | nvarchar(30) | ANO |  |  |
| 15 | `A_VariabilniSymbol` | nvarchar(40) | ANO |  |  |
| 17 | `A_Ulice` | nvarchar(200) | ANO |  |  |
| 21 | `A_Misto` | nvarchar(200) | ANO |  |  |
| 22 | `A_ICO` | nvarchar(30) | ANO |  |  |
| 23 | `A_IBAN` | nvarchar(41) | ANO |  |  |
| 24 | `A_DENgenerovani` | datetime | ANO |  |  |
| 26 | `B_CisloUctu` | nvarchar(40) | ANO |  |  |
| 27 | `B_IBAN` | nvarchar(41) | ANO |  |  |
| 28 | `B_SWIFT` | nvarchar(15) | ANO |  |  |
| 29 | `B_OrgNazev` | nvarchar(200) | ANO |  |  |
| 30 | `B_Ulice` | nvarchar(200) | ANO |  |  |
| 31 | `B_Misto` | nvarchar(200) | ANO |  |  |
| 32 | `B_Vygeneroval` | nvarchar(200) | ANO |  |  |
| 33 | `Odeslano` | bit | ANO |  |  |
| 34 | `DatumOdeslani` | datetime | ANO |  |  |
| 35 | `KdoOdeslal` | nvarchar(128) | ANO |  |  |
| 38 | `A_DENgenerovaniDATE` | nvarchar(4000) | ANO |  |  |

## Implicitní vztahy (heuristic, NE declared FK)

- `IDOrg` → pravděpodobně `TabCisOrg`

> _Marti-AI: Heliosové tabulky často nepoužívají declared FK. Vztah je dohadován z naming convention. Pro jistotu ověř před joiny._

## Indexy

- **PK** `PK_EC_PP_AvizoHlav` (CLUSTERED) — `ID`
