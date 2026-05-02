# EC_AutZprDokladHlav

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 6,850 · **Size**: 115.41 MB · **Sloupců**: 52 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `StatusPrevodu` | tinyint | ANO |  |  |
| 3 | `StatusPrevoduText` | varchar(21) | ANO |  |  |
| 4 | `InfoText` | nvarchar(255) | ANO |  |  |
| 5 | `IDDefinice` | int | ANO |  |  |
| 6 | `IDDoklad` | int | ANO |  |  |
| 7 | `IDDok` | int | ANO |  |  |
| 8 | `Realizovano` | bit | ANO | ((0)) |  |
| 9 | `DatumDoruceni` | datetime | ANO | (getdate()) |  |
| 10 | `FileName` | nvarchar(255) | ANO |  |  |
| 11 | `DokladTxt` | ntext | ANO |  |  |
| 12 | `DokladTxtOrig` | ntext | ANO |  |  |
| 13 | `TypDoklText` | nvarchar(70) | ANO |  |  |
| 14 | `Firma` | nvarchar(80) | ANO |  |  |
| 15 | `PocetPol` | smallint | ANO |  |  |
| 16 | `RozdilCenyDoklPol` | numeric(18,2) | ANO |  |  |
| 17 | `ICO` | nvarchar(15) | ANO |  |  |
| 18 | `CisloOrg` | int | ANO |  |  |
| 19 | `Objednavka` | nvarchar(20) | ANO |  |  |
| 20 | `CisloDokladu` | nvarchar(20) | ANO |  |  |
| 21 | `DatVystaveni` | datetime | ANO |  |  |
| 22 | `DatDUZP` | datetime | ANO |  |  |
| 23 | `DatSplatnosti` | datetime | ANO |  |  |
| 24 | `DodaciList` | nvarchar(100) | ANO |  |  |
| 25 | `DodaciListDatum` | datetime | ANO |  |  |
| 26 | `ObjednavkaDod` | nvarchar(20) | ANO |  |  |
| 27 | `ObjednavkaDodDatum` | datetime | ANO |  |  |
| 28 | `HmotnostBrutto` | numeric(18,2) | ANO |  |  |
| 29 | `HmotnostNetto` | numeric(18,2) | ANO |  |  |
| 30 | `PocetBaliku` | smallint | ANO |  |  |
| 31 | `Kurz` | numeric(10,3) | ANO |  |  |
| 32 | `Mena` | nvarchar(3) | ANO |  |  |
| 33 | `CelkemPol` | numeric(18,2) | ANO |  |  |
| 34 | `CelkemBezDPH` | numeric(18,2) | ANO |  |  |
| 35 | `DPH` | numeric(18,2) | ANO |  |  |
| 36 | `CelkemSDPH` | numeric(18,2) | ANO |  |  |
| 37 | `NazevUstavu` | nvarchar(100) | ANO |  |  |
| 38 | `CisloUctu` | nvarchar(40) | ANO |  |  |
| 39 | `KodUstavu` | nvarchar(15) | ANO |  |  |
| 40 | `IBAN` | nvarchar(40) | ANO |  |  |
| 41 | `SWIFT` | nvarchar(15) | ANO |  |  |
| 42 | `VariabilniSymbol` | nvarchar(20) | ANO |  |  |
| 43 | `VystavilJmeno` | nvarchar(50) | ANO |  |  |
| 44 | `VystavilTel` | nvarchar(20) | ANO |  |  |
| 45 | `VystavilEmail` | nvarchar(70) | ANO |  |  |
| 46 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 47 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 48 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 49 | `DatZmeny` | datetime | ANO |  |  |
| 50 | `IDEmail` | int | ANO |  |  |
| 51 | `Servis` | tinyint | ANO |  |  |
| 52 | `Sleva` | numeric(18,6) | ANO |  |  |

## Indexy

- **PK** `PK_EC_AutZprDokladHlav` (CLUSTERED) — `ID`
