# EC_KalkSkupiny

**Schema**: dbo · **Cluster**: Production · **Rows**: 141 · **Size**: 0.08 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Nazev` | nvarchar(200) | ANO |  |  |
| 4 | `Poradi` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Zamceno` | bit | NE | ((0)) |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |
| 11 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 12 | `DatZamceni` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_KalkSkupinyPolozek` (CLUSTERED) — `ID`
