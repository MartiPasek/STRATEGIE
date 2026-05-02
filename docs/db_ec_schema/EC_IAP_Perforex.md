# EC_IAP_Perforex

**Schema**: dbo · **Cluster**: Other · **Rows**: 5 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zakazka` | nvarchar(15) | NE |  |  |
| 3 | `Poznamka` | nvarchar(180) | NE |  |  |
| 4 | `PoznamkaVedouciVyroby` | nvarchar(180) | ANO |  |  |
| 5 | `ProgramCisloZam` | int | ANO |  |  |
| 6 | `ProgramPoznamka` | nvarchar(180) | ANO |  |  |
| 7 | `ProgramPodpisZL` | bit | NE | ((0)) |  |
| 8 | `MechanPraceDo` | datetime | ANO |  |  |
| 9 | `UkonceniVyroby` | datetime | ANO |  |  |
| 10 | `MechanPraceHotovo` | bit | NE | ((0)) |  |
| 11 | `ZamecnikCisloZam` | int | ANO |  |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |

## Cizí klíče (declared)

- `Zakazka` → `TabZakazka`.`CisloZakazky` _(constraint: `FK_EC_IAP_Perforex_TabZakazka`)_
- `ZamecnikCisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_IAP_Perforex_TabCisZam`)_

## Indexy

- **PK** `PK_EC_IAP_Perforex` (CLUSTERED) — `ID`
