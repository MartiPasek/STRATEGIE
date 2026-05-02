# EC_SWuzivAktualizace

**Schema**: dbo · **Cluster**: Other · **Rows**: 16 · **Size**: 0.20 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `ID_SW` | int | NE |  |  |
| 5 | `MuzeAktualizovat` | bit | ANO | ((1)) |  |
| 6 | `VynucenyDowngrade` | bit | ANO |  |  |
| 7 | `MusiPrejitNaVerziID` | int | ANO |  |  |
| 8 | `IdPosledniVerze` | int | ANO |  |  |
| 9 | `IdPredchoziVerze` | int | ANO |  |  |
| 10 | `CasRazitko` | nvarchar(800) | ANO |  |  |
| 11 | `DatumPosledniAktualizace` | datetime | ANO |  |  |
| 12 | `DatumPredchoziAktualizace` | datetime | ANO |  |  |
| 13 | `DatumPoslednihoPrihlaseni` | datetime | ANO |  |  |
| 14 | `JeDeveloper` | bit | NE | ((0)) |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SWuzivAktualizace` (CLUSTERED) — `ID`
