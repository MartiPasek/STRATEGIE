# EC_DokladyZbozi_EXT_Log

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 214,893 · **Size**: 90.98 MB · **Sloupců**: 81 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Log_ID` | int | NE |  |  |
| 2 | `Log_Author` | nvarchar(128) | ANO |  |  |
| 3 | `Log_DatPorizeni` | datetime | ANO |  |  |
| 4 | `Log_SPID` | smallint | ANO |  |  |
| 5 | `Log_Location` | nvarchar(128) | ANO |  |  |
| 6 | `Log_Info` | nvarchar(1000) | ANO |  |  |
| 7 | `ID` | int | ANO |  |  |
| 8 | `_ExportCtecka` | bit | ANO |  |  |
| 9 | `_ExportDatum` | datetime | ANO |  |  |
| 10 | `_ExportUser` | nvarchar(25) | ANO |  |  |
| 11 | `_ImportCtecka` | bit | ANO |  |  |
| 12 | `_ISDOCGUID` | varchar(36) | ANO |  |  |
| 13 | `_OptimalizaceKusovniku` | bit | ANO |  |  |
| 14 | `_NovaFa` | bit | ANO |  |  |
| 15 | `_EmailOdeslan` | bit | ANO |  |  |
| 16 | `_OznPrjZakaznik` | nvarchar(100) | ANO |  |  |
| 17 | `_PopisPrjZakaznik` | nvarchar(80) | ANO |  |  |
| 18 | `_NazevSouboru` | nvarchar(80) | ANO |  |  |
| 19 | `_Kontrola` | bit | ANO |  |  |
| 20 | `_RTF_Popis` | ntext | ANO |  |  |
| 21 | `_EmailOdeslanDatum` | datetime | ANO |  |  |
| 22 | `_EmailOdeslanUzivatel` | nvarchar(50) | ANO |  |  |
| 23 | `_EmailOdeslanPocitac` | nvarchar(50) | ANO |  |  |
| 24 | `_TextPredPolozkami` | ntext | ANO |  |  |
| 25 | `_TextZaPolozkami` | ntext | ANO |  |  |
| 26 | `_EmailPredmet` | ntext | ANO |  |  |
| 27 | `_EmailText` | ntext | ANO |  |  |
| 28 | `_Odeslano` | bit | ANO |  |  |
| 29 | `_Oznaceno` | bit | ANO |  |  |
| 30 | `_EmailAttachments` | nvarchar(255) | ANO |  |  |
| 31 | `_EmailCc` | nvarchar(255) | ANO |  |  |
| 32 | `_EmailFrom` | nvarchar(255) | ANO |  |  |
| 33 | `_EmailTo` | nvarchar(255) | ANO |  |  |
| 34 | `_Hmotnost` | numeric(19,6) | ANO |  |  |
| 35 | `_Hmotnost2` | numeric(19,6) | ANO |  |  |
| 36 | `_IndRozpisDPH` | bit | ANO |  |  |
| 37 | `_Jazyk` | nvarchar(2) | ANO |  |  |
| 38 | `_PocetKusu` | nvarchar(100) | ANO |  |  |
| 39 | `_TiskCenObj` | bit | ANO |  |  |
| 40 | `_Varianta` | nvarchar(10) | ANO |  |  |
| 41 | `_DodaciAdresa` | ntext | ANO |  |  |
| 42 | `_Oblast` | nvarchar(256) | ANO |  |  |
| 43 | `_NazevDok` | nvarchar(255) | ANO |  |  |
| 44 | `_EDI` | bit | ANO |  |  |
| 45 | `_ZobrazNadpis` | bit | ANO |  |  |
| 46 | `_InterniPoznamka` | text | ANO |  |  |
| 47 | `_UzivInfo` | nvarchar(255) | ANO |  |  |
| 48 | `_DodList` | nvarchar(255) | ANO |  |  |
| 49 | `_PoznamkaExt` | ntext | ANO |  |  |
| 50 | `_FinZakaz` | bit | ANO | ((0)) |  |
| 51 | `_FinSchvaleni` | bit | ANO | ((0)) |  |
| 52 | `_NavrhPlatby` | bit | ANO | ((0)) |  |
| 53 | `_Podpis` | smallint | ANO | ((1)) |  |
| 54 | `_PoznamkaVyvojar` | ntext | ANO |  |  |
| 55 | `_datumOBJ` | datetime | ANO |  |  |
| 56 | `_KontrolovatPotvrzeniVOBJ` | bit | ANO | ((1)) |  |
| 57 | `_Nefakturovat` | bit | ANO |  |  |
| 58 | `_contrVazba` | nvarchar(1) | ANO |  |  |
| 59 | `_pomDatum1` | datetime | ANO |  |  |
| 60 | `_NabPrij_Vyrobce` | nvarchar(255) | ANO |  |  |
| 61 | `_NabPrij_Dodavatel` | nvarchar(255) | ANO |  |  |
| 62 | `_NabPrij_NabidkaVystavenaDne` | date | ANO |  |  |
| 63 | `_NabPrij_PlatnostNabidkyDo` | date | ANO |  |  |
| 64 | `_NabPrij_Produkt` | nvarchar(255) | ANO |  |  |
| 65 | `_NabPrij_Popis` | nvarchar(255) | ANO |  |  |
| 66 | `_NabPrij_NabidkaID` | int | ANO |  |  |
| 67 | `_NabPrij_ZakazkaID` | int | ANO |  |  |
| 68 | `_NabPrij_Zakaznik` | nvarchar(255) | ANO |  |  |
| 69 | `_NabPrij_KoncovyZakaznik` | nvarchar(255) | ANO |  |  |
| 70 | `_NabPrij_KontaktniOsobaJmeno` | nvarchar(255) | ANO |  |  |
| 71 | `_NabPrij_KontaktniOsobaEmail` | nvarchar(255) | ANO |  |  |
| 72 | `_NemenitPoradiPolozek` | bit | ANO | ((0)) |  |
| 73 | `_UzivOK` | bit | ANO |  |  |
| 74 | `_PocetPoptPol` | int | ANO | ((0)) |  |
| 75 | `_PoznamkaSplneno` | nvarchar(4000) | ANO |  |  |
| 76 | `_NeuvadetDoFaPotvrzTermin` | bit | ANO |  |  |
| 77 | `_CashflowNepocitat` | bit | ANO |  |  |
| 78 | `_DatPrvniRealizace` | datetime | ANO |  |  |
| 79 | `_CashflowNepocitatDo` | datetime | ANO |  |  |
| 80 | `_NavazneObjednavkyList` | nvarchar(1000) | ANO |  |  |
| 81 | `IDENT_Hlav` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_DokladyZbozi_EXT_Log` (CLUSTERED) — `Log_ID`
