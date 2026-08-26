# Centrala: nocni kontrola bezi denne ve 2.30 a SAMA opravuje dochazku (13 zasahu, 4 nevratne) - overeno 26. 8. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nocni kontrola Centraly sama meni dochazku, nez zacne hledat chyby

**Overeno 26. 8. 2026 primo v Centrale (db=mssql). Nic nebylo zmeneno — zjisteni pred prenosem
prehledu "Cely den - VV" do STRATEGIE.**

## Kdy a jak casto (do 25. 8. to byla otevrena otazka)

| co | zjisteni |
|---|---|
| kdy | **kazdou noc ve 2.30** |
| jak casto | **jednou denne**; podruhe tyz den se sama nespusti (pojistka na zaznam v `EC_LogKontrol`) |
| co zpracuje | **vzdy jen vcerejsek** (`@DatumPripadu = getdate()-1`) |
| kdo spousti | naplanovana uloha SQL serveru **"Nocni kontrola"**, zapnuta, plan "V noci v 2hod 30min" (denne, jednou, start 02.30) |
| co vola | jediny krok `EXEC EC_NocniKontrola` v DB_EC |
| rucne | ano, "kontrola dne" z prehledu (`@SpustenaRucne=1`) — dva kroky se pak chovaji jinak |

⚠️ **`EC_NocniKontrola` je nocni kontrola CELE FIRMY** — vola pres 100 procedur (zakazky, sklad,
faktury, ukoly, kvalifikace, ISO). Dochazky se tyka hlavne **`EC_KontrolaDochazky`** (52 KB,
opravy i hledani chyb), dale `EC_KontrolaDochazky_Dlouhodoba`, `EC_KontrolaDochSkupIT`,
`EC_Events_PropsatDoDoch`, `EC_Event_OpravaDDN`, `EC_Dochazka_InfoOPrescasech`.
**Pri prenosu do STRATEGIE se to nesmi splest s ostatnimi.**

⚠️ **Kontrola v Centrale porad bezi a chyby zaklada dal**, i kdyz tam nikdo nepicha —
posledni nalez byl 26. 8. 2026 ve 2.30.

## 13 automatickych zasahu do dat (poradi v procedure)

Cast kroku se opakuje v cyklu pres jednotlive lidi. **Nikde se na nic nepta, nikde to neukaze.**

| # | co udela | podrobnost | maze | zavedl |
|---|---|---|---|---|
| 1 | smaze zaznamy uzivatele "Centrala" (c. 10000) starsi nez tyden | vznikaji pri blokaci dochazky | **ANO** | Kristyna 27. 8. 2023 |
| 2 | zaokrouhli vsechny casy na cele minuty | prace i prestavky, dny od 1. 12. 2020 | ne | Swobi 30. 10. 2020 |
| 3 | doplni chybejici konec podle cinnosti | kdyz ma cinnost `DogenerovatCasMin`; zaznam zneaktivni | ne | Swobi 10. 9. 2020 |
| 4 | prepise zakazku na rezijni | podle zakazky nastavene u cinnosti | ne | Swobi 25. 9. 2020 |
| 5 | smaze zaznamy s nulovym casem | prace i prestavky, jen bez poznamky zamestnance | **ANO** | Kristyna 8. 9. 2025 |
| 6 | prepocita denni soucty | `EC_Dochazka_DenniSumace` + `EC_ZamStatistikaHodAFin` | ne | — |
| 7 | prodlouzi konec pri odchodu na sluzebni cestu (cinnost 125) | dorovna den na 8 h. **Jen pri nocnim behu, pri rucnim NE** | ne | Swobi 18. 11. 2020, zmena 17. 3. 2026 |
| 8 | orizne dochazku podle pracovni doby (`EC_Dochazka_OriznoutDlePracDoby`) | co cele skoncilo pred zacatkem prac. doby, smaze; co presahuje, posune zacatek | **ANO** | Jan Svoboda 28. 10. 2020 |
| 9 | zneaktivni neukonceny zaznam | aby se clovek mohl druhy den prihlasit | ne | Swobi 13. 10. 2020 |
| 10 | prodlouzi kratky obed na 30 min (`EC_Dochazka_ProdluzObed`) | praci, co do obeda spadne, **smaze** (napred ji zapise poznamku "Smazano kvuli prodlouzeni obedu"), navazujicimu posune zacatek; jen pri jedinem obede za den | **ANO** | datum nedohledano |
| 11 | srovna mezery kratsi nez 90 vterin (`EC_Dochazka_SrovnejCasy`) | konec predchoziho posune na zacatek nasledujiciho, prace i prestavky | ne | Swobi 7. 10. 2020 |
| 12 | dopise k obedu poznamku | "Neprobehla kontrola obedu kvuli malemu poctu hodin" | ne | Swobi 30. 10. 2020 |
| 13 | propise poznamku z minula k nove chybe | z posledniho vyskytu teze chyby u tehoz cloveka a dne | ne | Swobi 3. 11. 2020 |

**Ctyri kroky (1, 5, 8, 10) jsou nevratne** — mazou zaznamy a neni z ceho poznat, co tam bylo.
**Krok 10 navic meni odpracovany cas, ktery jde primo do mezd.**

"Swobi" = Jan Svoboda (autor `EC_Dochazka_OriznoutDlePracDoby` je "Jan Svobda", u chyby c. 15
v ciselniku stoji "reknete Honzovi").

## ⚠️ PAST pri cteni tohoto kodu

**`DELETE EC_Dochazka WHERE …` se v Centrale pise BEZ `FROM`.** Kdo hleda "DELETE FROM",
napocita **nula mazani** a usoudi, ze kontrola nic nemaze. Je to hruba chyba — mazani jsou ctyri.
Hledej `\bDELETE\b`, ne `DELETE FROM`.

## Stanovisko Marti-AI (msg 13781, 25. 8. 2026)

Vyjadrovala se k **sedmi** zasahum, ne ke vsem 13:
- ✅ automaticky: zaokrouhleni casu, zneaktivneni neukonceneho dne, doplneni konce podle cinnosti,
  prepis zakazky na rezijni (u vsech krome zaokrouhleni + zapis do historie)
- ⛔ jen navrh ke schvaleni: smazani zaznamu s nulovym casem, prodlouzeni kratkeho obedu,
  srovnani mezer pod 90 vterin

> "Kdyz mzda nesedi, nikdo nedokaze rict proc. Centrala to delala tise, protoze byl jiny standard.
> STRATEGIE muze byt lepsi." — Marti-AI

**Sest zasahu jeste neposoudila:** mazani zaznamu uzivatele "Centrala", prepocet dennich souctu,
prodlouzeni sluzebni cesty, oriznuti podle pracovni doby, poznamka k obedu, propsani poznamky z minula.

## Co z toho dela STRATEGIE — NEOVERENO

Systematicky neprochazeno. Overene je jen: STRATEGIE kazdych 5 minut zneaktivni zaznam, ktery uz
skoncil nebo ma zacatek v budoucnu (obdoba kroku 9), a prazdny pracovni den doplnuje do fondu
(`att_prazdny_den_fond`, u kancelare). **Zbytek nikdo neprochazel.**

## Jak se to cte znovu

Ulohy: `msdb.dbo.sysjobs` / `sysjobsteps` / `sysjobschedules` / `sysschedules`.
⚠️ Slozitejsi dotazy nad `msdb` pres most padaji na `internal_error` — **ptej se jednoduse,
po jedne tabulce.** Text procedur: `sys.sql_modules` JOIN `sys.objects`.

## Souvisi

- `doc-dochazka-anomaly-ciselnik-druhu-chyb-chybi` — druhy chyb a jejich ciselnik
- `doc-dochazka-kontroly-centrala-vs-strategie-parovani` — ktere kontroly mame a ktere ne
- `doc-dochazka-prehled-cely-den-vv-centrala-rozbor` — prehled, kvuli kteremu se to resi
- `doc-system-strategie-centrala-definice-prehledu-jak-cist` — jak cist definice prehledu Centraly

