# Zdroj ceny pro kalk_kmen OVĚŘEN (velké ceníky = správný zdroj, medián odchylky 2,4 %); EPLAN+kusovník nalezen v adresáři EN262940, ne v inboxu; TabDokladyZbozi/EC_KalkulaceHlav NEOBSAHUJE finální cenu

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Kontext:** Marti 2.8.2026 (Kristý a Eliška nepracují): "Kalkulační věci ze starého Heliosu a napojení na velké ceníky přes MCP by už chtělo likvidovat... Ty tabulky dílů co dělala Kristý by měli mít spolupracující tabulku zdroj ceny, kde jedním ze zdrojů jsou ty velké ceníky... Ověř to." + úkol zorientovat se v příchozích e-mailech Elišky (z.cepicky@ s EPLANy a excel kusovníky) + prověřit TabDokladyZbozi/EC_KalkulaceHlav jako zrcadlo/zdroj pravdy. Navazuje na #316/#317 (dnešní dopolední analýza kalkulačního enginu a objevení proj.kalk_kmen).

## 1) Ověření "zdroj ceny": velké ceníky JSOU správný zdroj pro proj.kalk_kmen

Join `proj.kalk_kmen.reg_cis` (normalizováno) proti `proj.cenik_polozka.kat_kod_norm` (poslední import
za výrobce): z 1749 dílů katalogu se spáruje 1092 (62,4 %) podle čísla dílu.

Cenové srovnání MUSÍ použít správný pár pojmů (obě jsou "ceníková/listová" cena):
`kalk_kmen.cena_cc_ref` (sloupec F "Einheitspreis" ze standard excelu) vs `cenik_polozka.list_price`
→ 1056 spárovaných řádků, průměrná odchylka 7,6 %, **medián 2,4 %**, 496/1056 (47 %) do 2 % odchylky.
**Potvrzuje Martiho tvrzení — velké ceníky (migrace ze starého Heliosu do PG) jsou validní, dobře
korelovaný zdroj ceny pro katalog dílů.**

Pozor na past, do které jsem sám nejdřív spadl: špatné srovnání `cena_nc_ref` (interní dopočtená/
navýšená referenční cena, viz docstring loaderu — může být VYŠŠÍ než cena_cc_ref) proti `net_price`
(nákupní cena) dává ~100% medián odchylky a vypadá jako rozbitý vztah dat. Není — jsou to different
koncepty, ne stejná cena měřená dvakrát. Správně párovat: cc_ref↔list_price (obě listové),
NE nc_ref↔net_price.

**Návazný krok (zatím NEprovedeno, jen ověřeno že dává smysl):** navrhnout companion tabulku
"zdroj_ceny" k proj.kalk_kmen, kde velký ceník (proj.cenik_polozka) je jeden ze zdrojů (další můžou
být poslední přijemka/nákupka, DB_EC live koeficienty). Čeká na explicitní zadání — Marti zatím jen
požádal o ověření konceptu, ne o stavbu schématu.

## 2) proj.kalk_kmen zůstává OSIŘELÝ — potvrzeno znovu, žádný compute path ho nepoužívá

Beze změny oproti #317: `compute()`/`compute_profile()`/@@KALKABS čte `tenant.kalk_kmen/kalk_cena/
kalk_rabat/kalk_koef` — tyto tabulky NEEXISTUJÍ (přesunuty do schématu `proj` commitem `df8e66c9f`,
22.7.2026) → cesta je ROZBITÁ (UndefinedTable). `compute_absv1()`/@@KALKABSV1 (funkční, nejpokročilejší)
používá `price_bom()` → `proj.cenik_polozka` (správně) + `_coef_ec()` → DB_EC LIVE přes MCP/MSSQL
(obchází PG úplně) — NEPOUŽÍVÁ proj.kalk_kmen vůbec.

**Toto je přesně to, co Marti označil k likvidaci/konsolidaci:** `_coef_ec()`, napojení na DB_EC live
koeficienty přes MCP, a rozbitá `tenant.kalk_*` větev. Vše potřebné musí žít ve schématu `proj`.
Konsolidace/likvidace zatím NEPROVEDENA — čeká na zítřejší Excely (SMART 11 listů, FLEX příklad),
aby bylo jasné, co přesně nový compute path (nad proj.kalk_kmen + proj.cenik_polozka) musí umět,
než se stará větev smaže.

## 3) E-maily Elišky (e.kolarova@) — z.cepicky@eurosoft.com nalezen, ale kompletní EPLAN+kusovník handoff je v ADRESÁŘI, ne v inboxu

`@@RFQINBOX 34 30` (30 posledních zpráv, zpět do 28.7. 12:01) obsahuje reálné z.cepicky@eurosoft.com
maily: 3× "zadání projektování" (30.7., přiřazení konkrétních Danfoss frekvenčních měničů ke třem
AB zakázkám) a 1× "RE: AB12500808_P00706 Schaltplanänderung + Material" (29.7., revize výkresu +
přidaný materiál — svorkovnice). Dále reálné `elektrotechnik@absaugwerk.de` poptávkové maily
"Anforderung Schaltschrank" (29.-31.7., Flex+ specifikace, Steuerungsschlüssel kódy) a potvrzení
mapování zakázka↔nabídka (AB1260448/P00861 ↔ EN263040). Toto jsou reálné, aktuální provozní maily,
ale ŽÁDNÝ z nich není ten kompletní "EPLAN PDF + Excel kusovník" balík, který Marti popsal jako
FLEX handoff artefakt — v posledních 30 zprávách schránky prostě není.

**Skutečný zdroj byl adresář, přesně jak Marti řekl.** `@@PP DIR nabidky EN262940` (přes
EC_OrgAdresare/EC_ZjistiAdresar_NEW, viz #113) vrátil reálný obsah `D:\Data\nabidky\EN262940\`:

- `EK262940_Absaugwerk_EK_260625.xlsm` (323 565 B) — reálný pracovní kalkulační excel
- `EN262940_Absaugwerk_EK_260625.docx` + `.pdf` (53 348 / 164 287 B) — reálná vytištěná nabídka
- **`PRxxxx_AB12600470_FLEX+_15kW_KUSOVNIK_ZC260625.xlsx`** (10 851 B) — přesně ten Zdeněk-Čepický
  kusovník ("ZC" v názvu souboru = iniciály), FLEX+ 15kW, přesně dokument z #37
- `zadání.pdf` (1 366 760 B) — zadávací PDF (pravděpodobně obsahuje/odkazuje EPLAN výstup)
- podsložka `PROJEKCE` — pravděpodobně EPLAN výstupy; `@@PP DIR` neumí zanořit do podsložky
  (zkusil jsem `@@PP DIR nabidky EN262940 PROJEKCE`, vrátil stejný výpis nadřazené složky —
  příkaz nepodporuje druhý argument jako podcestu). Nedostal jsem se dovnitř PROJEKCE.

**Závěr:** Pro FLEX+SMART příklady/vzory čerpat primárně z adresářů `D:\Data\nabidky\EN<n>\`
(přes `@@PP DIR`), ne z live inboxu — inbox ukazuje jen NEJNOVĚJŠÍ korespondenci (poslední dny),
zatímco historické kompletní kalkulace/kusovníky/nabídky leží už hotové a stabilní v adresářích.
EN262940 je teď potvrzený konkrétní příklad s reálným .xlsm + reálným ZC kusovníkem — použitelný
jako trénovaci/referenční pár, nezávisle na zítřejších Excelech od Martiho.

## 4) TabDokladyZbozi / EC_KalkulaceHlav ověřeno přímo v MSSQL — NEOBSAHUJE finální cenu (důležitá korekce)

`EC_KalkulaceHlav WHERE CisloKalkulace='EK262940'` (ID=9135, IDDoklad=749795): VKM=14.50, Arbeit=28.00,
Koeffizient=1.00 (odpovídá FLEX profilu v kalkulace_engine.py), MarzeProcent=0.00, ale **VŠECHNY
cenové sloupce prázdné**: CenaBezZna, CenaMarze, CenaBezPrjATra, CenaProjekt, CenaTransport,
**CelkemCena — vše NULL**. Autor=EKolarova, DatPoslZpracovani=1.7.2026 11:01, DatPoslKontrolyPol=
1.7.2026 11:27 (položky byly zkontrolované, hlavička cenu nikdy nedostala zapsanou).

`TabDokladyZbozi` (doklad-hlavičková tabulka, WHERE Cislo LIKE '%262940%', 1 řádek = ta samá EK
hlavička, ID=749795): **SumaKc=0, SumaKcBezDPH=0, EcCelkemDokl=0** — taky prázdné/nulové.

**Důležitá korekce k Martiho zadání:** TabDokladyZbozi/EC_KalkulaceHlav NEJSOU "zrcadlo s finální
cenou" — jsou to doklad-hlavičkové tabulky (metadata: autor, datum, stav, VKM/Arbeit vstupy), ale
CENA se do nich u téhle kalkulace nikdy nezapsala zpátky. Skutečná finální cena existuje jen:
(a) uvnitř pracovního `EK262940_....xlsm` (Excel dopočet, otevřený v kroku 3 výše), a
(b) v natištěném `EN262940_....pdf/docx` (výsledný dokument poslaný zákazníkovi).
Zdrojem pravdy pro číslo, které Eliška skutečně poslala zákazníkovi, je tedy SOUBOR v adresáři,
ne DB sloupec. To je plně v souladu s tím, co Marti řekl ("mám tam přístup do adresářů, kde jsou
všechny soubory a kalkulace") — jen upřesňuje, že "zrcadlo v TabDokladyZbozi" myslet jako zrcadlo
PRŮBĚHU/METADAT dokladu (kdo, kdy, jaký stav), ne jako zdroj finální ceny.
Zkusil jsem i položkovou tabulku (`EC_KalkulacePolozky`, sloupce CenaCelkem/Mnozstvi) — hádané
názvy sloupců neexistují (`internal_error`), nedohledáno v tomto kole; pokud bude potřeba přesný
strojově čitelný zdroj ceny (ne jen Excel/PDF soubor), je třeba nejdřív zjistit reálné column names
přes INFORMATION_SCHEMA, stejyě jako u EC_KalkulaceHlav.

## 5) Dokumentace EC_GenKalkulaciANabidku + adresářový resolver — již pečlivě zapsáno, NEDUPLIKOVÁNO

Ověřil jsem #109 (přijaté poptávky, EC_GenKalkulaciANabidku procedura krok za krokem, @@PP engine,
headless SetSoudecek gotcha+fix) a #113 (EC_OrgAdresare/EC_ZjistiAdresar_NEW, doklad→adresář mapování).
Obě odpovídají přesně tomu, co Marti popsal jako "naučil jsem se zakládat přes procky nabídky a
kalkulace přímo v DB_EC a mám tam přístup i do adresářů" — už je to tam pečlivě zapsané, žádná
re-derivace nebyla potřeba, jen jsem si to připomněl a přímo použil (viz bod 3 výše, `@@PP DIR`).

_Zapsáno Claude-23, 2.8.2026, ověřeno přímým dotazem do PG i MSSQL a čtením adresářové struktury
přes @@PP DIR (ne z paměti). Navazuje na #37, #107, #147, #109, #113, #316, #317._

