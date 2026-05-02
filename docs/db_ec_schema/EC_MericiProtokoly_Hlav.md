# EC_MericiProtokoly_Hlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 3,184 · **Size**: 0.85 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `VyrobniCislo` | nvarchar(20) | ANO |  |  |
| 3 | `Nazev` | nvarchar(255) | ANO |  |  |
| 4 | `Zarizeni` | nvarchar(255) | ANO |  |  |
| 5 | `Technik` | nvarchar(128) | ANO |  |  |
| 6 | `Jazyk` | nvarchar(3) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `IDZP` | int | ANO |  |  |
| 12 | `Podpis` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_MericiProtokoly_Hlav` (CLUSTERED) — `ID`
