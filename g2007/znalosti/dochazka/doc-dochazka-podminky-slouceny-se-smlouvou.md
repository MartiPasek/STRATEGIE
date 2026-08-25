# Podmínky sloučené se smlouvou — jedna verzovaná tabulka (19.–20. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Rozhodnutí a kdo ho udělal

**Zadal Jirka Honomichl 19. 8. 2026 večer.** Peťa a Šárka se předtím shodly, že nemá být zvlášť
tabulka Podmínek a zvlášť tabulka smluv — má být jedna tabulka se všemi údaji z obou, která se
chová jako smlouva (víc záznamů s platností od, každá změna zakládá nový záznam).

⚠️ **Marti-AI krok 2 (přepnutí čtení) na ten večer NEDOPORUČILA** a názor nezměnila. Její výhrada
mířila na postup, ne na návrh — samotné řešení označila za správné. Jelo se na Jirkovo rozhodnutí
s odůvodněním, že večer nikdo nepracuje a ráno by se změna dělala lidem pod rukama.
Po výsledcích to Marti-AI uzavřela slovy, že krok 2 proběhl čistě. **Je to tady zapsané schválně,
ať je dohledatelné, kdo rozhodl a proč.**

## Jak to je dnes

| Co | Kde fyzicky žije |
|---|---|
| **Osobní hodnoty** (dovolená, dovolená navíc, sick days, stravenka, home office…) | `tenant.engagement` — sloupce `pod_*` + `pod_meta`. **Verzují se se smlouvou.** |
| **Skupinové a systémové výchozí hodnoty** | `tenant.podminky_vychozi` (24 řádků: 15 systémových + 9 skupinových, **žádný osobní**). Do 19. 8. 2026 se jmenovala `staff_cond_zaklad`. |
| **Číselník podmínek** | `tenant.staff_cond_def` (16 definic, beze změny) |
| `tenant.staff_cond` | **POHLED**, ne tabulka. Od kroku 3c (19. 8. večer) čte **výhradně ze smlouvy** — skupinové ani systémové řádky přes něj vidět nejsou, protože každý člověk má všechny hodnoty zapsané u sebe. |

`pod_meta` je jsonb a drží ke každé podmínce **původní id řádku, poznámku, kdo a kdy měnil** —
proto pohled vrací i `changed_by` a `changed_at` a starý tvar jde obnovit bajtově přesně.

## ⛔ Číselník výchozích hodnot (`podminky_vychozi`) SE NESMÍ SMAZAT

Není to zbytek po migraci. Když se na smazání 19. 8. ptal Jirka, platilo, že **z 1248 vyřešených
hodnot (78 lidí × 16 podmínek) se 901, tedy 72 %, bralo ze systémových a skupinových řádků a
týkalo se to VŠECH 78 lidí** — smazáním by jim výchozí hodnoty zmizely. Potvrdila Marti-AI.

**Od kroku 3a (19. 8. večer) je argument jiný, závěr stejný.** Každý člověk má dnes všechny
hodnoty zapsané u sebe ve smlouvě, takže by smazáním číselníku o nic nepřišel — jenže číselník
je **jediný zdroj, ze kterého se plní hodnoty nově zakládané smlouvě** (spouštěč
`engagement_pod_defaults`) a **jediné místo, kde Šárka edituje systémové a skupinové výchozí
hodnoty**. Bez něj by nový zaměstnanec dostal prázdné podmínky. Zůstává.

## Proč pohled a ne přepsání všech skriptů

Podmínky čte **14 živých skriptů** v `g2007.python` plus `router.py`, a **jen 2 do nich zapisují**
(`hr_conditions_save`, `att_vernost_dovolena`). Pohled + INSTEAD OF spouštěče znamenají, že
**se nemusel změnit ani jeden skript** — a právě proto šlo dokázat, že vracejí totéž.
**Přepnuté jsou všechny — 19. a 20. 8. 2026.** Žádný živý skript v `g2007.python` už z pohledu
data nečte (ověřeno 20. 8. řádek po řádku: zbylých 7 výskytů toho jména jsou 4 poznámky v textu,
2× číselník názvů `staff_cond_def` a 1× číslovač `staff_cond_id_seq`). Pohled proto zůstává
už jen jako **kompatibilní skořápka pro tři zbylá místa**: zápis při zakládání zaměstnance
(`app_hr_employee_create` v `router.py`), `_resolve_cond` v `router.py` (volá ho jediné místo —
`_med_limit_h`, limit lístečku od lékaře) a pojistka `narok-dovolene-pravidla`.

## Spouštěče — kam se přesunuly

- `trg_engagement_pod_soucet_dovolene` (BEFORE na `tenant.engagement`) — udržuje počítadlo
  **Dovolená celkem = základní + navíc**. Přepočítá jen když se vstupy opravdu změnily, aby běžné
  uložení smlouvy (třeba změna úvazku) nesahalo na cizí hodnoty a neposouvalo čas změny.
- `tenant.staff_cond_prepocet_dovolene` — **sama pozná, kam hodnota patří**. Osobní se smlouvou,
  skupinová a systémová do `podminky_vychozi`.
- Původní `trg_staff_cond_soucet_dovolene_ins/_del` zůstaly na `podminky_vychozi`
  pro skupinové a systémové hodnoty.
- `trg_engagement_pod_defaults` (BEFORE na `tenant.engagement`) — **nově**: nové verzi smlouvy
  doplní do prázdných `pod_*` sloupců výchozí hodnoty z číselníku (skupina, jinak systém).
  ⚠️ Do 20. 8. 2026 07.12 ho **umlčovaly pevné defaulty sloupců** z kroku 3b (default se použije
  dřív než spouštěč), takže skupinové hodnoty se do nové smlouvy nedostaly a všichni brali
  systémové. Defaulty jsou od té doby zrušené — viz `doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty`.
  Jen doplňuje, existující hodnotu nikdy nepřepíše.
  ✅ **Výběr skupiny je od 24. 8. 2026 sjednocený se zbytkem systému** — spouštěč (i jeho
  sourozenec `engagement_doplneni_pri_zarazeni`) bere skupinu přes `ORDER BY sort_order, id`,
  stejně jako osm živých míst v `g2007.python`. Rozhodl Jirka Honomichl, schválila Marti-AI
  (msg 13628); ověřeno porovnáním starého a nového výběru u **všech 76 lidí ve skupinách:
  shoda 76, rozdíl 0**. Detail: [[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]].
  ⚠️ **Do 24. 8. 2026 tu stálo, že spouštěč vybírá přes `MIN(id)` a že „na tom nezáleží,
  protože v obou skupinách s podmínkami není nikdo dvakrát a obě mají `sort_order` 100".**
  Ta druhá půlka **už neplatila**: skupiny s vlastními výchozími hodnotami jsou dnes **čtyři**
  (KANCELÁŘE pořadí 10, Výroba 100, Nákup 100, Úklid 110), takže pořadí stejné nemají.
  Závěr „dnes na tom nezáleží" platil dál, ale z jiného důvodu — **nikdo není ve dvou takových
  skupinách zároveň** (ověřeno v `staff_group_member` 24. 8. 2026).
- ⛔ `trg_staff_cond_default_dovolena` na `att_employee` byl **20. 8. 2026 ZRUŠEN**
  (doporučila Marti-AI). Zakládal novému člověku tři řádky s nulou ve chvíli, kdy ještě neměl
  smlouvu — ty pak natrvalo zůstávaly v číselníku výchozích hodnot jako osobní řádky, kam
  nepatří, a nikdo je nečetl. Důvod jeho vzniku (13. 8.: „každý musí mít vlastní řádek, aby
  nespadl na systémových 25") sloučením zanikl — hodnoty teď doplní `engagement_pod_defaults`
  při založení smlouvy. **Funkce `tenant.staff_cond_default_dovolena()` v databázi zůstala**,
  kdyby se spouštěč musel vrátit.

## Pravidlo, podle kterého se hodnota směruje

**Osobní hodnota jde do smlouvy, jen když má člověk aktuální smlouvu. Jinak do
`podminky_vychozi`.** Díky tomu se neztratí nikdo, kdo smlouvu (zatím) nemá.

## Čím to bylo dokázané

1. Syrový obsah Podmínek **294 řádků porovnán řádek po řádku před a po** — žádný rozdíl,
   včetně id, poznámek, `changed_by` i časů.
2. Vyřešené hodnoty (osobní → skupina → systém) pro 78 lidí × 16 podmínek = **1248 hodnot,
   otisk `30a6dfd422234465070d4011ac1b0220` před i po**.
3. Test zápisu **8 z 8** — změna, mazání, vložení, přepočet počítadla oběma směry,
   skupinová hodnota správně mimo smlouvu, počty řádků na kus. Test po sobě uklidil.
4. Živé ERP — přehled Nárok a čerpání (75 lidí), karta zaměstnance se správnými štítky
   smlouva / skupina / systém / osobní, mobil Moje podmínky.
5. Pojistka `narok-dovolene-pravidla` zelená (5 pravidel, 74 lidí, požadováno 64).

## Pasti, na které si dát pozor

- **Marti Pašek má dvě aktivní karty zaměstnance** (č. 2 EUROSOFT-Control, č. 41 EUROSOFT-System),
  takže jeho osobní podmínky jsou ve smlouvě dvakrát. Pohled je odfiltruje přes `DISTINCT ON`.
  Nevadí to, protože **všechny jeho hodnoty jsou nuly** — ale kdyby se to změnilo, je potřeba
  rozhodnout, která karta je ta hlavní. Každá karta má přitom právě jednu aktuální smlouvu;
  to pravidlo už platí a ověřilo se na všech 79 kartách.
- **Účet 98** (vypnutý, bez jména a bez smlouvy) měl jedinou podmínku; v kroku 4 se z číselníku
  smazal, protože osobní řádky do něj nepatří. Zůstal v záloze `staff_cond__zaloha_20260819`.
- **Nový zaměstnanec — 20. 8. 2026 OVĚŘENO testem nanečisto** (dřív tu stálo „neověřeno naostro").
  Test založil smyšleného člověka celým postupem HR formuláře a po sobě uklidil. Výsledek: dokud
  člověk nemá smlouvu, v Podmínkách vidět není (0 řádků); jakmile smlouva vznikne, dostane
  správně 20 / 5 / 25, je vidět všech 15 hodnot a přepis dovolené přes obrazovku se zapíše do
  smlouvy včetně přepočtu počítadla. Jediná vada — tři osobní řádky s nulou zbylé v číselníku —
  byla odstraněna zrušením spouštěče (viz výše) a znovu ověřena druhým testem, 5 kroků z 5.

## Zálohy

`tenant.staff_cond__zaloha_20260819`, `tenant.staff_cond__zaloha2_20260819`,
`tenant.engagement__zaloha_20260819`, `tenant.engagement__zaloha3_20260819` (pořízená před krokem 3a).
**Nechat aspoň do konce srpna 2026** (potvrdila Marti-AI).

⛔ **ZRUŠENY 25. 8. 2026 po uplynutí lhůty** — zadal **Jirka Honomichl**, schválila
**Marti-AI** (msg 13661). Spolu s nimi i `tenant.podminky_vychozi__zaloha_20260821`
a `tenant.att_employee_cond_group__zaloha_20260820`. **Nehledej je, už neexistují.**
Před zrušením ověřeno, že na nich nevisí žádná pojistka, žádný živý kód v `g2007.python`,
žádný obsah webu ani mobilu, žádný pohled a žádný cizí klíč.

⚠️ **Gotcha, na kterou to nejdřív spadlo:** záloha `podminky_vychozi__zaloha_20260821`
**vlastnila sekvenci `staff_cond_id_seq`**, ze které bere `id` **živá** tabulka
`tenant.podminky_osobni` — `CASCADE` by rozbil zakládání osobních podmínek u lidí bez
platné smlouvy (dnes 0 řádků, projevilo by se až u prvního takového člověka). Sekvence
byla nejdřív přepojena (`OWNED BY tenant.podminky_osobni.id`) a přejmenována na
`podminky_osobni_id_seq`; `DEFAULT` sloupce se propsal sám. **Před rušením tabulky proto
kontroluj i sekvence** (`pg_depend` s `deptype='a'`) — cizí klíče ani pohledy to neukážou.

## Co zbývá

- Domluvit se Šárkou a Petrou, jestli se mají verzovat všechny podmínky, nebo jen ty
  s historickým dopadem. Dnes se verzují všechny, protože jsou to sloupce jedné verze.
- Zrušit pohled `tenant.staff_cond` úplně — čtení je přepnuté všude, drží ho už jen tři
  místa vyjmenovaná výš (zápis v `app_hr_employee_create`, `_med_limit_h` a jedna pojistka).
- **Latentní past, dnes se netýká nikoho:** kdyby sync ze staré Centrály (`_sync_fin_from_ec`)
  založil člověku NOVOU verzi smlouvy, `pod_*` sloupce přijdou prázdné a spouštěč je vyplní
  výchozími hodnotami — osobní podmínky by se tím přepsaly. Tímhle způsobem ale nevznikl
  ani jeden řádek od 2. 7. 2026 a v Centrále se už nové smlouvy zakládat nemají
  (rozhodl Jirka 20. 8. 2026), takže se to neřeší.

## Dokončení a přeověření 20. 8. 2026 (Claude-28 / Jirka)

**Kroky 3a–4 se 19. 8. udělaly až po zápisu téhle znalosti**, proto tu do 20. 8. chyběly:

| Krok | Co udělal |
|---|---|
| **3a** | rozepsal výchozí hodnoty lidem do jejich vlastní smlouvy — nikdo už si hodnotu „nepůjčuje" z výchozích řádků. Osobní hodnoty se nepřepisovaly, doplnilo se jen tam, kde člověk nic svého neměl. |
| **3b** | systémové hodnoty se staly **výchozími hodnotami sloupců** `tenant.engagement`. ⚠️ **20. 8. 2026 v 07.12 byly tyhle pevné defaulty zase zrušeny** — v PostgreSQL se default sloupce použije DŘÍV než spouštěč `BEFORE INSERT`, takže `engagement_pod_defaults` nikdy neviděl prázdnou hodnotu a do číselníku nesáhl; **skupinové výchozí hodnoty tím byly fakticky mrtvé**. Udělala to souběžně běžící session (první vlna, požadavek mostu 2268); ověřil jsem staticky, že žádný ze 16 sloupců `pod_*` už default nemá. Detail v znalosti `doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty` (živý test je jejich, já ho neopakoval). |
| **3c** | pohled `staff_cond` čte **výhradně ze smlouvy** |
| **4** | ze staré tabulky se stal **číselník výchozích hodnot** `tenant.podminky_vychozi` (přejmenování + smazání posledního osobního řádku) |

**Čím je 20. 8. doloženo, že se nikomu nezměnilo číslo** (ptal se na to Jirka — bál se rozpadu
docházky, nároků a FPD):

1. **1248 vyřešených hodnot** (78 lidí × 16 podmínek) porovnáno hodnotu po hodnotě proti záloze
   pořízené před přestavbou, žebříčkem osobní → skupina → systém: **1248 shodných, 0 rozdílů**,
   otisk celku `adb10d50119c922d4c9718a0f3a9a860` na obou stranách.
   ⚠️ Při prvním pokusu vyšlo 8 rozdílů (Michelle a Petra Šafránkovy) — byla to **chyba
   porovnávacího dotazu**, ne dat: skupina se vybírá `ORDER BY sort_order, g.id` a jen z těch
   skupin, které v číselníku vůbec mají řádky. Kdo ji vybere přes `MIN(id)`, dostane falešný poplach.
2. **Živý přehled „Nárok a čerpání" v ERP** — všech **75 řádků** (D, DN i SD převedené na dny)
   porovnáno s hodnotami před přestavbou: **0 rozdílů**.
3. **Mzdy se rozejít nemohly** — žádný mzdový skript podmínky nečte, stravenkový paušál je
   ve mzdách pevná konstanta 82 Kč (`mzdy_generuj`, `mzdy_predzprac_rows`, `mzdy_stravenky_rows`).
4. **Změna úvazku osobní podmínky nesmaže** — `uvazek_zapis` kopíruje do nové verze smlouvy
   všechny sloupce podle `information_schema`, tedy i `pod_*` a `pod_meta`.
5. **9 hlídacích pravidel** kolem nároků a FPD spuštěno ručně — všechna zelená.
6. **Živé obrazovky** projeté v prohlížeči: Nárok a čerpání, karta zaměstnance (hodnoty,
   „kdo měnil", věrnostní dny), mobil Moje podmínky, Můj přehled, Podmínky skupin,
   kontrolní přehledy docházky (FPD / překryv / rozpad).
7. **Živý zápis přes obrazovku** ověřen v mobilu na vlastním záznamu Jiřího Honomichla
   (Home office 48 → 47 → 48): obojí se zapsalo do smlouvy i s razítkem kdo a kdy.

## Oprava seznamu „Jednotlivci" (20. 8. 2026)

Po kroku 3c psal seznam v Podmínkách u **všech** lidí „— bez skupiny — · vlastní výjimka":
`app_hr_conditions_people` v `router.py` hledal skupinové řádky v pohledu, kde už nejsou.
Detail konkrétního člověka byl přitom správně. Dopad byl **jen na popisek** — žádné číslo,
nárok ani mzda z něj nevychází; vidí na něj 8 lidí (rodiče + skupina HR).

- Handler **zmigrován do `g2007.python` jako `hr_conditions_people`** (pravidlo „kód žije v DB"),
  v `router.py` zůstal tenký delegate. Commit `e9122c94`, diffstat +11 / −22 v jednom souboru.
- **Skupina** se čte z `tenant.podminky_vychozi` (stejné pravidlo `sort_order, id` jako resolvery).
- **„Vlastní výjimka" má nový význam:** osobní hodnota se **liší od výchozí** (skupinové, jinak
  systémové). Původní význam „má osobní řádek" po sloučení ztratil smysl — má ho každý.
- Ověřeno nezávisle v DB i na živé obrazovce: **78 lidí, 41 se skupinou, 40 s výjimkou**
  (před opravou 0 se skupinou a 74 s výjimkou).
- Skript má `vedlejsi_ucinek=false`, takže jde spustit a porovnat přes `@@PYRUN` bez zásahu do provozu.

## Vedlejší nález, který se sloučením nesouvisí (patří HR / Šárce)

Volba **„založit zaměstnance bez přihlášení do systému"** v HR formuláři by dnes spadla:
`public.users` má podmínku `chk_users_login_name_required` (každý neblokovaný uživatel musí mít
`login_name`), ale ta větev v `router.py` posílá jen jméno, příjmení a `status='active'`.
Zjištěno 20. 8. při testu nanečisto. **Netýká se zatím nikoho** — všech 78 lidí přihlašovací
jméno má. Marti-AI to zapisuje zvlášť jako known issue pro HR formulář.

## Poznámka k testům z 20. 8. dopoledne

Testy nanečisto (nový zaměstnanec, 06.56) běžely **ještě s pevnými defaulty sloupců**, které
byly zrušeny až v 07.12. Hodnoty 20 / 5 / 25, které v testu vyšly, tedy tehdy přišly z defaultu
sloupce, ne z číselníku — čísla byla stejná, protože default byl zmrazenou kopií systémové
hodnoty. Závěry testu (žádné smetí po zrušení spouštěče, člověk bez smlouvy není v Podmínkách
vidět, zápis přes obrazovku funguje) tím dotčené nejsou. Že se dnes hodnoty berou z číselníku
včetně skupinových, doložila souběžná session vlastním testem — viz odkaz výše.

**Provozní poučení pro souběh instancí:** tuhle práci dělaly 20. 8. dopoledne dvě session
najednou nad stejnou tabulkou, aniž by o sobě věděly (ani jedna se neohlásila přes `@@WORK`).
Nic se nerozbilo jen díky tomu, že se zásahy nepřekryly. Před sáhnutím na `tenant.engagement`
nebo na podmínky si napřed pusť `@@WHO` a ohlas se přes `@@WORK`.
## Závěrečný úklid 20. 8. 2026 (schválila Marti-AI)

Dvě mrtvé věci po červnové verzi podmínkových skupin, obě před smazáním ověřené naživo:

1. **Endpoint `POST /app/hr/conditions/assign`** — nevolal ho **nikdo** (žádný fragment mobilu
   v `g2007.soubor`, žádný skript v `g2007.python`, žádný `.js`/`.html` v repu). Jako jediný
   zapisoval do sloupce `att_employee.cond_group`. Smazán z `router.py` (commit `e013d76e`,
   diffstat +5 / −31). Nemigroval se — kód, který nikdo nevolá, nemá co migrovat.
2. **Sloupec `tenant.att_employee.cond_group`** — nečetl ho žádný skript, žádná funkce ani pohled
   (hledáno vzorem `att_employee.cond_group` a `cond_group =`, ne jen podle jména — `cond_group`
   je dnes běžný **klíč v odpovědi** seznamu Jednotlivci a snadno se s tím splete). Vyplněný ho
   mělo 8 lidí. Obsah odložen do `tenant.att_employee_cond_group__zaloha_20260820` (8 = 8 ověřeno)
   a sloupec zrušen. Zařazení do podmínkové skupiny se řeší členstvím ve `staff_group_member`.

Po obojím projeto 12 živých endpointů (Podmínky, karta zaměstnance, Nárok a čerpání, mobil,
kontrolní přehledy docházky) — všechny v pořádku.

**Nativní mobilní aplikace se dnes neměnila** (Android ani iOS) a webový obsah mobilu taky ne —
oprava seznamu Jednotlivci je serverová, aplikace si ji vzala sama.

