# EC_GlobKonstUziv

**Schema**: dbo · **Cluster**: Other · **Rows**: 283 · **Size**: 0.13 MB · **Sloupců**: 30 · **FK**: 2 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `LoginName` | nvarchar(128) | NE | (suser_sname()) |  |
| 3 | `PrednastavenySklad` | nvarchar(30) | ANO |  |  |
| 4 | `PrednastaveneObdobi` | int | ANO |  |  |
| 5 | `VybraneObdobi` | int | ANO |  |  |
| 6 | `VybranySklad` | nvarchar(30) | ANO |  |  |
| 7 | `ZobrazVsechSoudeckuStromu` | bit | NE | ((0)) |  |
| 8 | `Oblast` | nvarchar(256) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |
| 13 | `AktualniID` | int | ANO |  |  |
| 14 | `UniLog` | int | ANO | ((0)) |  |
| 15 | `AktualniSkupinaSvetel` | int | ANO |  |  |
| 16 | `AktualniAdresaSkupiny` | int | ANO |  |  |
| 17 | `StahniVseDoLokal` | bit | ANO | ((1)) |  |
| 18 | `ProcentoPlaceniKonta` | smallint | ANO |  |  |
| 19 | `EasterEggs` | bit | ANO | ((0)) |  |
| 20 | `DochazkaRychlyLogin` | int | ANO | ((0)) |  |
| 21 | `IdPracDoba` | int | ANO |  |  |
| 22 | `JeSpravceDochazky` | bit | ANO |  |  |
| 23 | `PovolitDochVCentrale` | bit | NE | ((1)) |  |
| 24 | `DochKontrolovatSvacinu` | bit | ANO | ((0)) |  |
| 25 | `DochKontrolaObedHod` | numeric(5,2) | ANO | ((6)) |  |
| 26 | `DochZobrazitJmeno` | bit | ANO | ((0)) |  |
| 27 | `SeznamSkupinText` | nvarchar(400) | ANO |  |  |
| 28 | `VytizeniJenMoje` | bit | ANO |  |  |
| 29 | `StatistikaVPOd` | date | ANO |  |  |
| 30 | `StatistikaVPDo` | date | ANO |  |  |

## Cizí klíče (declared)

- `PrednastaveneObdobi` → `TabObdobi`.`Id` _(constraint: `FK__EC_TabUziv__PrednastaveneObdobi`)_
- `PrednastavenySklad` → `TabStrom`.`Cislo` _(constraint: `FK__EC_TabUziv__PrednastavenySklad`)_

## Indexy

- **PK** `PK_EC_TabUziv` (CLUSTERED) — `ID`
