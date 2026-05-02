# EC_IAP_TableProc

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | nvarchar(50) | NE | (NULL) |  |
| 3 | `Nazev` | nvarchar(70) | NE | (NULL) |  |
| 4 | `DatZalozeni` | datetime | NE | (NULL) |  |
| 5 | `DatZmeny` | datetime | ANO | (NULL) |  |
| 6 | `Definice` | nvarchar(MAX) | ANO | (NULL) |  |
| 7 | `ForeignKeys` | nvarchar(MAX) | ANO |  |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK__EC_IAP_T__3214EC276F9FB8A6` (CLUSTERED) — `ID`
