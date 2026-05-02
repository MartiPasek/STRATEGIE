# EC_PohybyZbozi_EXT_Log

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 63,750 · **Size**: 19.13 MB · **Sloupců**: 35 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Log_ID` | int | NE |  |  |
| 2 | `Log_Author` | nvarchar(128) | NE | (suser_name()) |  |
| 3 | `Log_DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `Log_SPID` | smallint | ANO | (@@spid) |  |
| 5 | `Log_Location` | nvarchar(128) | ANO |  |  |
| 6 | `Log_Info` | nvarchar(1000) | ANO |  |  |
| 7 | `ID` | int | ANO |  |  |
| 8 | `_Cislo_Balik` | nvarchar(15) | ANO |  |  |
| 9 | `_KodPrac` | int | ANO |  |  |
| 10 | `_MnozVracenoCtecka` | numeric(19,6) | ANO |  |  |
| 11 | `_NC_Kc` | numeric(19,6) | ANO |  |  |
| 12 | `_NC_Val` | numeric(19,6) | ANO |  |  |
| 13 | `_Parametry` | ntext | ANO |  |  |
| 14 | `_DatUzivOK` | datetime | ANO |  |  |
| 15 | `_EDI` | bit | ANO |  |  |
| 16 | `_UzivInfo` | nvarchar(255) | ANO |  |  |
| 17 | `_UzivOK` | bit | ANO |  |  |
| 18 | `_ZamUzivOK` | int | ANO |  |  |
| 19 | `_PoznamkaTerminal` | nvarchar(MAX) | ANO |  |  |
| 20 | `_slevaFP` | numeric(19,6) | ANO |  |  |
| 21 | `_Color` | smallint | ANO |  |  |
| 22 | `_IDZdrojPol` | int | ANO |  |  |
| 23 | `_Datum_ProdZaruky` | datetime | ANO |  |  |
| 24 | `_TerminPripomenuti` | datetime | ANO |  |  |
| 25 | `_IDPredpisControling` | int | ANO |  |  |
| 26 | `_TerminPoznamka` | nvarchar(MAX) | ANO |  |  |
| 27 | `_MnozstviTisk` | numeric(18,2) | ANO |  |  |
| 28 | `_LOGsVP` | nvarchar(4000) | ANO |  |  |
| 29 | `_Urgence` | bit | ANO |  |  |
| 30 | `_AUTOPotvrzDatum` | datetime | ANO |  |  |
| 31 | `_AUTOMnozstvi` | numeric(19,2) | ANO |  |  |
| 32 | `_AUTOPoznamka` | nvarchar(1000) | ANO |  |  |
| 33 | `_HistorieZakazek` | nvarchar(500) | ANO |  |  |
| 34 | `_PotvrzDatDod_rucneZadano` | bit | ANO |  |  |
| 35 | `IDENT_Hlav` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_PohybyZbozi_EXT_Log` (CLUSTERED) — `Log_ID`
