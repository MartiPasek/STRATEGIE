# TabCisOrg_EXT

**Schema**: dbo · **Cluster**: Reference-Identity · **Rows**: 1,972 · **Size**: 1.35 MB · **Sloupců**: 67 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `_Objednavky_Email` | nvarchar(60) | ANO |  |  |
| 3 | `_Objednavky_Telefon` | nvarchar(20) | ANO |  |  |
| 4 | `_Objednavky_Fax` | nvarchar(20) | ANO |  |  |
| 5 | `_Objednavky_Formular` | smallint | ANO |  |  |
| 6 | `_Objednavky_Zpusob_uhrady` | nvarchar(30) | ANO |  |  |
| 7 | `_Objednavky_Poznamka` | nvarchar(160) | ANO |  |  |
| 8 | `_Zkratka_nazvu` | nvarchar(15) | ANO |  |  |
| 9 | `_Poptavky_Formular` | smallint | ANO |  |  |
| 10 | `_Faktury_formular` | smallint | ANO |  |  |
| 11 | `_Nabidky_Formular` | smallint | ANO |  |  |
| 12 | `_Fakturace_v_EUR` | bit | ANO |  |  |
| 13 | `_Creditcheck_ZaniklySub` | bit | ANO |  |  |
| 14 | `_Creditcheck_Stav` | int | ANO |  |  |
| 15 | `_Creditcheck_WebFree` | nvarchar(255) | ANO |  |  |
| 16 | `_Creditcheck_WebFull` | nvarchar(255) | ANO |  |  |
| 17 | `_Creditcheck_DatAktualizace` | datetime | ANO |  |  |
| 18 | `_Creditcheck_Neupozornovat` | bit | ANO |  |  |
| 19 | `_ISDOC_ElPosAgreementRef` | varchar(255) | ANO |  |  |
| 20 | `_Creditcheck_IdCc` | int | ANO |  |  |
| 21 | `_Creditcheck_Datum_Zmeny` | datetime | ANO |  |  |
| 22 | `_Objednavky_MinLimitEUR` | int | ANO |  |  |
| 23 | `_Objednavky_MinLimitCZK` | int | ANO |  |  |
| 24 | `_Objednavky_UpozVPLimitEUR` | int | ANO |  |  |
| 25 | `_PoznamkaOrg` | nvarchar(1000) | ANO |  |  |
| 26 | `_TiskCenObj` | bit | ANO |  |  |
| 27 | `_VF_Poznamka` | text | ANO |  |  |
| 28 | `_Jazyk` | nvarchar(2) | ANO |  |  |
| 29 | `_Varianta` | nvarchar(10) | ANO |  |  |
| 30 | `_ZpusobGenVS` | int | ANO | ((1)) | 0=DodFakKV, 1=DodFakKV bez písmen, 2= prázdné |
| 31 | `_ImportTyp` | smallint | ANO |  |  |
| 32 | `_GenObj` | smallint | ANO |  |  |
| 33 | `_Teritorium` | nvarchar(20) | ANO |  |  |
| 34 | `_AutomFinPlatba` | bit | ANO |  |  |
| 35 | `_DnyPredPlatbou` | int | ANO |  |  |
| 36 | `_DobaDopravy` | int | ANO | ((1)) |  |
| 37 | `_FormaDopravy` | nvarchar(30) | ANO |  |  |
| 38 | `_FormaUhrady` | nvarchar(30) | ANO |  |  |
| 39 | `_PlatebniPodminky` | nvarchar(30) | ANO |  |  |
| 40 | `_InfoNovaAdresa` | bit | ANO | ((0)) |  |
| 41 | `_KontrolaPotvrzeniVOBJ` | bit | ANO | ((1)) |  |
| 42 | `_DoSplatnosti` | int | ANO |  |  |
| 43 | `_KontrolaPFvsOBJ` | bit | ANO | ((1)) |  |
| 44 | `_CestaEDIVOBJ` | ntext | ANO |  |  |
| 45 | `_IDDefEDIVOBJ` | int | ANO |  |  |
| 46 | `_DodaniPocetPracDni` | int | ANO |  |  |
| 47 | `_ZobrazitVKonverzi` | bit | ANO | ((0)) |  |
| 48 | `_VytizeniBarva` | nvarchar(10) | ANO | (N'74FF72') |  |
| 49 | `_VytizeniExtVyroba` | bit | ANO | ((0)) |  |
| 50 | `_VypnoutKontroluVOBJbezPotvrzTerminu` | bit | ANO | ((0)) |  |
| 51 | `_Stredisko` | nvarchar(30) | NE | ('001') |  |
| 52 | `_PoznamkaObj` | varchar(1000) | ANO |  |  |
| 53 | `_PlatPrikazyAvizo` | bit | ANO | ((0)) |  |
| 54 | `_PoznamkaDoprava` | nvarchar(1000) | ANO |  |  |
| 55 | `_BezObalu` | bit | ANO | ((0)) |  |
| 56 | `_JeDopravce` | bit | ANO | ((0)) |  |
| 57 | `_KontrolovatOdeslaniRealizaciVOBJ` | bit | NE | ((1)) |  |
| 58 | `_KontrolovatKalkulace` | bit | ANO |  |  |
| 59 | `SystemRowVersionExt` | timestamp | NE |  |  |
| 60 | `SystemRowVersionExtText` | nvarchar(16) | ANO |  |  |
| 61 | `_ID_ES` | int | ANO |  |  |
| 62 | `_SumovatPolVOBJ` | bit | ANO | ((0)) |  |
| 63 | `_PoznamkaDetailOBJ` | ntext | ANO |  |  |
| 64 | `_DopravuZajistujeZakaznik` | bit | NE | ((0)) |  |
| 65 | `_PripravaMat_ReplaceTextList` | nvarchar(50) | ANO |  |  |
| 66 | `_PripravaMat_BeforeAddText` | nvarchar(5) | ANO |  |  |
| 67 | `_PripravaMat_PocetSloupcuStitky` | smallint | ANO |  |  |

## Indexy

- **PK** `PK__TabCisOrg_EXT__ID` (CLUSTERED) — `ID`
