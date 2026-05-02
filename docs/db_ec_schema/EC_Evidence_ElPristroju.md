# EC_Evidence_ElPristroju

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,190 · **Size**: 0.61 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloKarty` | int | NE |  |  |
| 3 | `IDSpotrebice` | int | ANO |  |  |
| 5 | `Typ` | nvarchar(100) | ANO |  |  |
| 6 | `VyrobniCislo` | nvarchar(100) | ANO |  |  |
| 7 | `VyrobceID` | int | ANO |  |  |
| 8 | `EvidencniCislo` | nvarchar(30) | ANO |  |  |
| 9 | `IDStredisko` | int | ANO |  |  |
| 10 | `IDSkupinaElPristroju` | int | ANO |  |  |
| 11 | `IDTridaOchrany` | int | ANO |  |  |
| 12 | `DatumOvereniRevize` | datetime | ANO |  |  |
| 13 | `LhutaPlatnosti` | int | ANO |  |  |
| 14 | `PlatnostDo` | datetime | ANO |  |  |
| 15 | `ProvedeneOpravy` | ntext | ANO |  |  |
| 16 | `DatUvedeniDoPrvozu` | datetime | ANO |  |  |
| 17 | `DatVyrazeniZProvozu` | datetime | ANO |  |  |
| 18 | `Adresar` | nvarchar(150) | ANO |  |  |
| 19 | `CisloEvidOnz` | int | ANO |  |  |
| 21 | `Kalibrace` | bit | ANO |  |  |
| 22 | `CisloZam` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Evidence_ElPristroju` (CLUSTERED) — `ID`
