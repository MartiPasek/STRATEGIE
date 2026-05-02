# EC_DilnaUtahMom

**Schema**: dbo · **Cluster**: Other · **Rows**: 62 · **Size**: 0.13 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Vyrobce` | nvarchar(60) | ANO |  |  |
| 2 | `ID` | int | NE |  |  |
| 3 | `Typ` | nvarchar(60) | ANO |  |  |
| 4 | `Nazev` | nvarchar(60) | ANO |  |  |
| 5 | `TypSilSvorky` | nvarchar(60) | ANO |  |  |
| 6 | `VelikostSroubuProUpevneni` | nvarchar(50) | ANO |  |  |
| 7 | `UtahMomentSilSvorkyNm` | nvarchar(50) | ANO |  |  |
| 8 | `UtahMomentUpevSroubuNm` | nvarchar(50) | ANO |  |  |
| 9 | `Manual` | nvarchar(200) | ANO |  |  |
| 10 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DilnaUtahMom` (CLUSTERED) — `ID`
