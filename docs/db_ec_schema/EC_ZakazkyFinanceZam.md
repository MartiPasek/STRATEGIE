# EC_ZakazkyFinanceZam

**Schema**: dbo · **Cluster**: Finance · **Rows**: 23,065 · **Size**: 4.83 MB · **Sloupců**: 27 · **FK**: 1 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatumPorizeni` | datetime | NE | (getdate()) |  |
| 3 | `CisloZakazky` | varchar(15) | NE |  |  |
| 4 | `CisloZam` | int | NE |  |  |
| 5 | `HodSazba` | int | ANO |  |  |
| 6 | `FixPremie` | int | ANO |  |  |
| 7 | `PocetHodin` | numeric(8,2) | ANO |  |  |
| 8 | `PenizeCelkem` | numeric(20,2) | ANO |  |  |
| 9 | `Uzavreno` | bit | ANO |  |  |
| 10 | `Vyplatit` | int | ANO |  |  |
| 11 | `Vyplaceno` | int | NE | ((0)) |  |
| 12 | `ZbyvaVyplatit` | int | ANO |  |  |
| 13 | `DatPosledniPlatby` | datetime | ANO |  |  |
| 14 | `Efektivita` | int | ANO |  |  |
| 15 | `PoznamkaVV` | nvarchar(500) | ANO |  |  |
| 16 | `PoznamkaVP` | nvarchar(500) | ANO |  |  |
| 17 | `PoznamkaSefmonter` | nvarchar(500) | ANO |  |  |
| 18 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 19 | `IDPolVobj` | int | ANO |  |  |
| 20 | `IDPolPF` | int | ANO |  |  |
| 21 | `Sefmonter` | bit | ANO |  |  |
| 22 | `PremieOsobaSpec` | numeric(19,6) | ANO |  |  |
| 23 | `PremieSefmonter` | numeric(19,6) | ANO |  |  |
| 24 | `PremieOsobaFinal` | numeric(19,6) | ANO |  |  |
| 25 | `PremieOsobaEf` | numeric(19,6) | ANO |  |  |
| 26 | `SrazkaOsoba` | numeric(19,6) | ANO |  |  |
| 27 | `PremieOsoba` | numeric(19,6) | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_ZakazkyFinanceZam_TabCisZam`)_

## Indexy

- **INDEX** `Eix_EC_ZakazkyFinanceZam_CisloZakazky` (NONCLUSTERED) — `CisloZakazky`
