# EC_VztahKOsKomunikace

**Schema**: dbo · **Cluster**: Other · **Rows**: 430 · **Size**: 0.29 MB · **Sloupců**: 11 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DruhDokladu` | nvarchar(50) | ANO |  |  |
| 3 | `IDCisOrg` | int | ANO |  |  |
| 4 | `IDCisKOs` | int | ANO |  |  |
| 5 | `IDCisZam` | int | ANO |  |  |
| 6 | `DruhKomunikace` | nvarchar(50) | NE |  |  |
| 7 | `Poznamka` | ntext | ANO |  |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Cizí klíče (declared)

- `ID` → [`EC_VztahKOsKomunikace`](EC_VztahKOsKomunikace.md).`ID` _(constraint: `FK_EC_VztahKOsKomunikace_EC_VztahKOsKomunikace`)_

## Indexy

- **PK** `PK_EC_VztahKOsKomunikace` (CLUSTERED) — `ID`
