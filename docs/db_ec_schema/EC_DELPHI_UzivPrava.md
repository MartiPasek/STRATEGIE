# EC_DELPHI_UzivPrava

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 31,908 · **Size**: 3.23 MB · **Sloupců**: 27 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Soudecek` | int | ANO |  |  |
| 3 | `ID_Prehled` | int | ANO |  |  |
| 4 | `ID_Jadro` | int | ANO |  |  |
| 5 | `CisloZam` | int | ANO |  |  |
| 6 | `Soudecek` | bit | NE | ((1)) |  |
| 7 | `Prehled` | bit | NE | ((1)) |  |
| 8 | `Novy` | bit | NE | ((1)) |  |
| 9 | `Oprava` | bit | NE | ((1)) |  |
| 10 | `Zrusit` | bit | NE | ((1)) |  |
| 11 | `Zobraz` | bit | NE | ((1)) |  |
| 12 | `Tisk` | bit | NE | ((1)) |  |
| 13 | `Nastav` | bit | NE | ((1)) |  |
| 14 | `Akce` | bit | NE | ((1)) |  |
| 15 | `Adresar` | bit | NE | ((1)) |  |
| 16 | `MS_Office` | bit | NE | ((1)) |  |
| 17 | `UzivForm` | bit | NE | ((1)) |  |
| 18 | `Specialni` | bit | NE | ((1)) |  |
| 19 | `InfoProUzivatele` | nvarchar(128) | NE | ('') |  |
| 20 | `Stav` | tinyint | NE | ((0)) |  |
| 21 | `DatPrideleniZamitnutiPrava` | datetime | ANO |  |  |
| 22 | `KdoPridelilZamitnulPravo` | nvarchar(128) | ANO |  |  |
| 23 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 24 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmeny` | datetime | ANO |  |  |
| 27 | `ID_Skupina` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_DELPHI_UzivPrava` (CLUSTERED) — `ID`
