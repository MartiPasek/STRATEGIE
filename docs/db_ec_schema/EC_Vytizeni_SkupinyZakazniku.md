# EC_Vytizeni_SkupinyZakazniku

**Schema**: dbo · **Cluster**: Production · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 4 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | ANO |  |  |
| 3 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Vytizeni_SkupinyZakazniku` (CLUSTERED) — `ID`
