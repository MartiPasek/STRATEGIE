# EC_Sklad_PosledniObjednani

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 13,576 · **Size**: 5.57 MB · **Sloupců**: 29 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `regcis` | nvarchar(30) | ANO |  |  |
| 3 | `nazev1` | nvarchar(100) | ANO |  |  |
| 4 | `Umístění` | nvarchar(15) | ANO |  |  |
| 5 | `Skladem` | numeric(20,6) | ANO |  |  |
| 6 | `CenaPrumer` | numeric(19,6) | NE |  |  |
| 7 | `CenaCelkem` | numeric(38,10) | ANO |  |  |
| 8 | `Blokovano` | tinyint | ANO |  |  |
| 9 | `Minimum` | numeric(19,6) | NE |  |  |
| 10 | `Maximum` | numeric(19,6) | NE |  |  |
| 11 | `CastSkladu` | nvarchar(15) | ANO |  |  |
| 12 | `PosledniObjednani` | datetime | ANO |  |  |
| 13 | `PosledniObjednavka` | int | ANO |  |  |
| 14 | `PosledniVydani` | datetime | NE |  |  |
| 15 | `Vyber1` | bit | ANO |  |  |
| 16 | `Vyber2` | bit | ANO |  |  |
| 17 | `Vyber3` | bit | ANO |  |  |
| 18 | `Vyber4` | bit | ANO |  |  |
| 19 | `Vyber5` | bit | ANO |  |  |
| 20 | `Objednano365dni` | numeric(38,6) | ANO |  |  |
| 21 | `ObjednanoSklad365dni` | numeric(38,6) | ANO |  |  |
| 22 | `Vydano365dni` | numeric(38,6) | ANO |  |  |
| 23 | `Vraceno365dni` | numeric(38,6) | ANO |  |  |
| 24 | `VydanoSVraceno365dni` | numeric(38,6) | ANO |  |  |
| 25 | `MinimumOpt` | numeric(38,6) | ANO |  |  |
| 26 | `MaximumOpt` | numeric(38,6) | ANO |  |  |
| 27 | `MinimumProc` | numeric(38,6) | NE |  |  |
| 28 | `MaximumProc` | numeric(38,6) | NE |  |  |
| 29 | `Dodavatel` | nvarchar(255) | ANO |  |  |
