# EC_Soubory

**Schema**: dbo · **Cluster**: CRM-Documents · **Rows**: 23 · **Size**: 4.58 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Typ` | nvarchar(10) | ANO |  | jpg,bmp,ico.... |
| 4 | `Cesta` | nvarchar(100) | ANO |  |  |
| 5 | `Nazev` | nvarchar(50) | ANO |  |  |
| 6 | `Soubor` | varbinary(MAX) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Popis` | nvarchar(255) | ANO |  |  |
| 10 | `VelikostSouboru` | int | ANO |  |  |
| 11 | `Poznamka` | ntext | ANO |  |  |

## Indexy

- **PK** `PK_EC_Soubory` (CLUSTERED) — `ID`
