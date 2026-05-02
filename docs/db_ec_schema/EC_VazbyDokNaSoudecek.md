# EC_VazbyDokNaSoudecek

**Schema**: dbo · **Cluster**: Other · **Rows**: 19 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Doklad` | nvarchar(50) | NE |  |  |
| 3 | `Soudecek` | int | NE |  |  |
| 4 | `User` | int | ANO |  |  |
| 5 | `OpenDetail` | bit | NE | ((0)) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_VazbyDokNaSoudecek`](EC_VazbyDokNaSoudecek.md).`ID` _(constraint: `FK_EC_VazbyDokNaSoudecek_EC_VazbyDokNaSoudecek`)_

## Indexy

- **PK** `PK_EC_VazbyDokNaSoudecek` (CLUSTERED) — `ID`
