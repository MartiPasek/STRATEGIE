# EC_FinPriplatkySrazkyDefinice

**Schema**: dbo · **Cluster**: Finance · **Rows**: 11,397 · **Size**: 2.65 MB · **Sloupců**: 31 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZdroj` | int | ANO |  |  |
| 3 | `Typ` | int | NE | ((0)) |  |
| 4 | `Schvaleno` | bit | NE | ((1)) |  |
| 5 | `CisloZamNavrhl` | int | ANO |  |  |
| 6 | `CisloZam` | int | ANO |  |  |
| 7 | `Přeneseno` | int | NE |  |  |
| 8 | `IdMzdoveSlozky` | int | ANO |  |  |
| 9 | `Mesicne` | bit | NE | ((0)) |  |
| 10 | `Fix` | bit | NE | ((0)) |  |
| 11 | `Mesic` | int | ANO |  |  |
| 12 | `Rok` | int | ANO |  |  |
| 13 | `PlatnostOd` | datetime | ANO |  |  |
| 14 | `PlatnostDo` | datetime | ANO |  |  |
| 15 | `Hodiny` | numeric(9,2) | ANO |  |  |
| 16 | `Sazba` | int | ANO |  |  |
| 17 | `Castka` | numeric(9,0) | ANO |  |  |
| 18 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 19 | `DatVyplaceni` | datetime | ANO |  |  |
| 20 | `Vyplaceno` | int | NE |  |  |
| 21 | `Vyplatil` | nvarchar(128) | ANO |  |  |
| 22 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 23 | `Zdroj` | nvarchar(200) | ANO |  |  |
| 24 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 25 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 26 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 27 | `DatZmeny` | datetime | ANO |  |  |
| 28 | `IDPolVobj` | int | ANO |  |  |
| 29 | `IDPolPF` | int | ANO |  |  |
| 30 | `PropsatPoznamkuDoVOBJ` | bit | ANO | ((0)) |  |
| 31 | `CastkaVypocetHodSazby` | numeric(9,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_FinOdmenyJednorazove` (CLUSTERED) — `ID`
