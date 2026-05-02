# EC_ImportPolozek

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,244,231 · **Size**: 433.45 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | nvarchar(50) | NE |  |  |
| 3 | `IDCilPol` | int | ANO |  |  |
| 4 | `IDZdrojPol` | int | ANO |  |  |
| 5 | `RegCis` | nvarchar(60) | ANO |  |  |
| 6 | `Mnozstvi` | numeric(19,6) | ANO |  |  |
| 7 | `MJ` | nvarchar(20) | ANO |  |  |
| 8 | `EAN` | nvarchar(100) | ANO |  |  |
| 9 | `Zpracovano` | bit | ANO | ((0)) |  |
| 10 | `DatZpracovani` | datetime | ANO |  |  |
| 11 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 14 | `PotvrzDatum` | datetime | ANO |  |  |
| 15 | `IdDoklad` | int | ANO |  |  |
| 16 | `Poradi` | int | ANO |  |  |
| 17 | `DopravaDoklad` | nvarchar(128) | ANO |  |  |
| 18 | `TypVysledek` | int | ANO | ((0)) |  |
| 19 | `xPotvrzDatum` | datetime | ANO |  |  |
| 20 | `_AUTOPotvrzDatum` | datetime | ANO |  |  |
| 21 | `TypVysledekText` | varchar(29) | NE |  |  |

## Indexy

- **PK** `PK_EC_ImportPolozek` (CLUSTERED) — `ID`
