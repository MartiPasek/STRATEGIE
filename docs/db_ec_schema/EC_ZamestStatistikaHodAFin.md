# EC_ZamestStatistikaHodAFin

**Schema**: dbo · **Cluster**: Other · **Rows**: 307 · **Size**: 0.13 MB · **Sloupců**: 32 · **FK**: 1 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloZam` | int | NE |  |  |
| 2 | `DatumPoslAktualizace` | datetime | ANO |  |  |
| 3 | `AktualniPredpVykonnost` | numeric(4,2) | ANO |  |  |
| 4 | `CelkemHodZaAktDen` | numeric(5,2) | ANO |  |  |
| 5 | `CelkemHodZaMinDen` | numeric(5,2) | ANO |  |  |
| 6 | `CelkemHodZaAktTyden` | numeric(5,2) | ANO |  |  |
| 7 | `CelkemHodZaMinTyden` | numeric(5,2) | ANO |  |  |
| 8 | `CelkemHodZaAktMesic` | numeric(5,2) | ANO |  |  |
| 9 | `CelkemHodZaMinMesic` | numeric(5,2) | ANO |  |  |
| 10 | `CelkemHodZaPredminMesic` | int | ANO |  |  |
| 11 | `CelkemHodZaAktRok` | int | ANO |  |  |
| 12 | `CelkemHodZaMinRok` | int | ANO |  |  |
| 13 | `CelkemHodNevyuct` | int | ANO |  |  |
| 14 | `CelkemHodKProplaceni` | int | ANO |  |  |
| 15 | `CelkemHodProplaceno` | int | ANO |  |  |
| 16 | `CelkemFinKProplaceni` | int | ANO |  |  |
| 17 | `CelkemFinProplaceno` | int | ANO |  |  |
| 18 | `DatumPoslednihoProplaceni` | datetime | ANO |  |  |
| 19 | `CisloDokladuPoslednihoProplaceni` | varchar(30) | ANO |  |  |
| 20 | `DatumPoslednihoVyuctovani` | datetime | ANO |  |  |
| 21 | `HodSazbaPrumerZaAktMesic` | int | ANO |  |  |
| 22 | `HodSazbaPrumerZaMinMesic` | int | ANO |  |  |
| 23 | `HodSazbaPrumerZaPredminMesic` | int | ANO |  |  |
| 24 | `HodSazbaPrumerZaAktRok` | int | ANO |  |  |
| 25 | `HodSazbaPrumerZaMinRok` | int | ANO |  |  |
| 26 | `CelkemNevyucHodNaPoslZakazce` | int | ANO |  |  |
| 27 | `PredpHodSazbaNaPoslZakazce` | int | ANO |  |  |
| 28 | `CelkemPredpFinNaPoslZakazce` | int | ANO |  |  |
| 29 | `PoslZakazka` | varchar(15) | ANO |  |  |
| 30 | `PoslCinnost` | int | ANO |  |  |
| 31 | `PoslPoznamka` | varchar(80) | ANO |  |  |
| 32 | `RozdilOdpracovanoVsFPD` | numeric(5,2) | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_ZamestStatistikaHodAFin_TabCisZam`)_
