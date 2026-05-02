# EC_Terminy

**Schema**: dbo · **Cluster**: Other · **Rows**: 54 · **Size**: 0.07 MB · **Sloupců**: 27 · **FK**: 3 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Skup` | int | NE |  |  |
| 3 | `ID_Nasled` | int | ANO |  |  |
| 4 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `CisloZam` | int | ANO |  |  |
| 6 | `Datum` | datetime | ANO |  |  |
| 7 | `Cas` | datetime | ANO |  |  |
| 8 | `Nejasne` | bit | NE | ((0)) |  |
| 9 | `Splneno` | bit | NE | ((0)) |  |
| 10 | `Poznamka` | nvarchar(100) | ANO |  |  |
| 11 | `Popis` | nvarchar(400) | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |
| 16 | `DatPorizeni_D` | int | ANO |  |  |
| 17 | `DatPorizeni_M` | int | ANO |  |  |
| 18 | `DatPorizeni_Y` | int | ANO |  |  |
| 19 | `DatPorizeni_Q` | int | ANO |  |  |
| 20 | `DatPorizeni_W` | int | ANO |  |  |
| 21 | `DatPorizeni_X` | datetime | ANO |  |  |
| 22 | `DatZmeny_D` | int | ANO |  |  |
| 23 | `DatZmeny_M` | int | ANO |  |  |
| 24 | `DatZmeny_Y` | int | ANO |  |  |
| 25 | `DatZmeny_Q` | int | ANO |  |  |
| 26 | `DatZmeny_W` | int | ANO |  |  |
| 27 | `DatZmeny_X` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `CisloZakazky` → `TabZakazka`.`CisloZakazky` _(constraint: `FK_EC_Terminy_TabZakazka`)_
- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_Terminy_TabCisZam`)_
- `ID_Skup` → [`EC_TerminySkup`](EC_TerminySkup.md).`ID` _(constraint: `FK_EC_Terminy_EC_TerminySkup`)_

## Indexy

- **PK** `PK_EC_Terminy` (CLUSTERED) — `ID`
