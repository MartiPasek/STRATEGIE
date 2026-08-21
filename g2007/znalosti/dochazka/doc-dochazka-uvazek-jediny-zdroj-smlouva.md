# Týdenní úvazek — jediný zdroj je smlouva (poměr), ne Podmínky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ⚠️ **POZOR — STAV K 20. 8. 2026 ZMĚNĚN (Jiří Honomichl, 20. 8. 2026, schválila Marti-AI).**
> Tři tvrzení v textu níže od 20. 8. 2026 **NEPLATÍ**:
>
> 1. *„Z Podmínek byl vyřazen a smazán"* — osobní hodnoty ano, ty tam nejsou a zapsat nejdou.
>    Do číselníku výchozích hodnot (`tenant.podminky_vychozi`) se ale 20. 8. **záměrně vrátila
>    jedna systémová hodnota 40**. Není to úvazek žádného člověka — čte ji **jedině** mechanismus
>    zakládání smlouvy, aby nová smlouva měla co předvyplnit.
> 2. *„Systémový default 40 v Podmínkách lhal"* — tehdy ano, protože se četl při každém zobrazení.
>    Dnešní hodnota se čte **jen jednou, při vzniku smlouvy**; potom platí výhradně smlouva.
> 3. *„U systémového a skupinového pohledu se úvazek nenabízí vůbec"* — od 20. 8. se **nabízí**
>    (`hr_conditions` v5, `hr_conditions_save` v6), aby personální mohlo nastavit jiný výchozí
>    úvazek pro Výrobu a jiný pro Nákup. **Osobní úroveň se nezměnila** — úvazek konkrétního
>    člověka jde dál výhradně do smlouvy přes `uvazek_zapis`.
>
> Navíc `tenant.engagement_doplneni_pri_zarazeni` (spouštěč při prvním zařazení do skupiny) je
> od 20. 8. kromě `uvazek_zapis` druhé místo, které zapisuje do `uvazek_tyden_h` — vždy jen do
> **prázdného** pole u nové smlouvy, nikdy nepřepisuje existující hodnotu. Vědomá výjimka.
>
> Detail: `doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty`.
> **Text níže popisuje stav platný do 19. 8. 2026 a jinak platí dál.**


## Rozhodnutí (Jirka Honomichl, 18. 8. 2026, schválila Marti-AI)

**Týdenní úvazek má jediný domov — smlouvu (`tenant.engagement.uvazek_tyden_h`).**
Z Podmínek (`tenant.staff_cond`, kód `uvazek_h_tyden`) byl vyřazen a smazán.
Odtud si ho čte i sem ho zapisuje celý systém.

### Proč zrovna smlouva a ne Podmínky

1. Úvazek je **smluvní údaj platný od data**. `engagement` je verzovaný
   (`valid_from` / `valid_to` / `is_current`, 939 verzí u 229 lidí), `staff_cond` historii nemá.
2. **Systémový default 40 v Podmínkách lhal.** Kdo tam neměl osobní řádek, spadl na 40 —
   týkalo se to jmenovitě 4 lidí: Duspivová (smlouva 35), Šik (30), Vlková (15), Senft (5).
   U úvazku je každý fallback lež; chybějící úvazek ve smlouvě je aspoň vidět.
3. Úvazek už ze smlouvy četlo 21 živých skriptů (docházka, denní fond, mzdy, stravenky, raporty).

### Kde úvazek byl (stav před opravou, ověřeno 18. 8. 2026)

Byl na **čtyřech** místech, ne dvou:
- `tenant.engagement.uvazek_tyden_h` — smlouva, pravda
- `tenant.staff_cond` kód `uvazek_h_tyden` — 1 systémový řádek (40) + 8 osobních
- `tenant.c_smlouva.uvazek_h_tyden` — cockpit mezd, 18 lidí, **všem natvrdo 40 od 1. 1. 2026**
  (špatně u 5 lidí: Bernardová 32, Dvořáková 30, Novotná 35, Veverková 20, Duspivová 35)
- `tenant.att_plan_day.uvazek_h_tyden` — roční plán, hodnota přicházela **natvrdo z mobilu** (40)

### Jak se to čte a zapisuje teď

- **Čtení** = `g2007.python` skript **`att_uvazek_tyden`** (`run(s, user_id, default_h=40, k_datu=None)`).
  Umí i historickou hodnotu k datu. Při víc souběžných poměrech bere nejvyšší, stejně jako `att_denni_fond`.
- **Zápis** = `g2007.python` skript **`uvazek_zapis`** (`run(s, user_id, uvazek, uid)`).
  Chová se stejně jako HR obrazovka „Změna poměru": přepíše aktuální řádek, přidá lidskou
  poznámku do `note` a zapíše kdo/kdy. **Nezakládá novou verzi** — viz otevřená věc níže.
  Odmítne člověka bez poměru a člověka s víc souběžnými poměry (dnes jen Marti Pašek),
  ať je vidět, které smlouvy se změna týká.

### Co bylo přepnuto (vše migrováno z `router.py` do `g2007.python`)

`plan_my_uvazek`, `plan_my_uvazek_save`, `plan_my_default`, `plan_group`, `plan_mine`,
`plan_generate_base`, `plan_generate_effective`, `hr_schedule`, `hr_conditions`,
`hr_conditions_save`, `my_conditions`, `mzdy_c_smlouvy`, `mzdy_c_smlouva_save`.

V `router.py` zůstaly jen tenké delegáty. Ubylo tam přes 700 řádků.

### Karta zaměstnance

Řádek **„Týdenní úvazek" v Podmínkách zůstal vidět a dá se měnit**, ale hodnota i zápis
jdou do smlouvy. Má vlastní zelený štítek **„smlouva"** a pod polem stojí
„zapíše se do smlouvy · platí od <datum>". Kdo úvazek ve smlouvě nemá, má červený štítek
**„chybí ve smlouvě"**. Definice řádku v `staff_cond_def` proto **zůstává** — smazané jsou
jen uložené hodnoty. U systémového a skupinového pohledu se úvazek nenabízí vůbec
(smlouva je vždy osobní).

### Dopad na data (ověřeno)

- Plán (`att_plan_effective`) přegenerován: ze 77 lidí se změnili 4 očekávaní —
  Vlková 416 → 156 h, Šik 416 → 312, Senft 416 → 52, Duspivová 416 → 364.
- Roční plán Brudnové (`att_plan_day`) srovnán z 2000 na 1750 h (úvazek 35, ne 40).
- Cockpit mezd ukazuje smluvní hodnoty (dřív všem 40).
- Nároky na dovolenou a sick days se nezměnily — ty v Podmínkách zůstávají.

### Otevřené věci — stav k 18. 8., aktualizováno 19. 8. 2026

- ~~**Historie úvazku se nezakládá.**~~ ✅ **VYŘEŠENO 19. 8. 2026** — změna úvazku dnes zakládá
  novou verzi smlouvy s datem „platí od". Viz sekci „Historie úvazku — hotovo 19. 8. 2026" níže.
  *(Původní znění: 939 verzí je z migrace, změna přepisovala aktuální řádek a stopa zůstávala
  jen jako text v `note`.)* Tenhle bod tu zůstává přeškrtnutý schválně, ať je dohledatelný.
- ~~**Pět lidí nemá úvazek ve smlouvě**~~ ✅ **VYŘEŠENO 20. 8. 2026** (zadala Peťa,
  potvrdil Jirka Honomichl, schválila Marti-AI). U **čtyř** z nich se úvazek **NEVYPLŇUJE**
  a je to zapsané v datech — Herejtová = dohoda (DPP), Saxana = brigáda, demo účet
  a Marti-AI = systémové účty. Karta jim ukazuje šedé „neuvádí se — <důvod>" místo
  červeného „chybí ve smlouvě" a **osmička ani čtyřicítka se jim už nedosazuje**.
  Pátý, **Martin Konicar**, mezi ně nepatřil: smlouvu tu měl od migrace 7. 6. 2026,
  jen nebyla označená jako platná — 20. 8. oživena a doplněna podle Centrály.
  Hlídá to pojistka `uvazek-bud-ve-smlouve-nebo-s-duvodem`.
  Detail: **`doc-dochazka-uvazek-se-neuvadi-vyjimky`**.
  *(Původní znění tvrdilo, že jim „denní fond padá na výchozích 8 h" a že doplnění je
  práce personalistiky — obojí už neplatí. Nechávám to tu přeškrtnuté schválně.)*

## Dokončeno 19. 8. 2026 (druhý den)

- **Pojistka `uvazek-z-podminek-uplny` (Peťa) VYPNUTA** na pokyn Jirky. Porovnávala smlouvu
  proti Podmínkám, takže po smazání hodnot by hlásila rozdíl u všech 77 lidí — falešný
  poplach. Důvod je zapsaný v jejím popisu. Náhradní kontrola se nepíše: rozchod dvou míst
  už nemůže vzniknout, protože druhé místo neexistuje. Peťa byla informovaná přes `@@COORD`
  a může rozhodnout jinak.
- **Mobilní dílek `71_plan_prace_cinnosti.js` opraven** — u tlačítka ročního plánu se už
  neposílá `uvazek:40`, appka neposílá nic a server bere úvazek ze smlouvy. Zapsáno přes
  `@@G2007SOUBOR` (87 872 znaků, md5 ověřeno) + `@@G2007PUBLISH` (mobile.html verze 53),
  načtení `/mobile` ověřeno v prohlížeči.
- **Sloupec `c_smlouva.uvazek_h_tyden` připraven ke zrušení** — 19. 8. vyřazen i ze
  samotného dotazu (`g2007.python` kód `mzdy_c_smlouvy`, verze 3), aby po jeho smazání
  nemělo co spadnout. Ověřeno na živém cockpitu (18 řádků, hodnoty i sloupce sedí).
  Návrh na smazání poslal Jirka e-mailem Kristýně 19. 8. 2026 — je to její území,
  rozhodnutí je na ní.

### ⚠️ Oprava dřívějšího tvrzení (Claude-28, 19. 8. 2026)

**`att_plan_day.uvazek_h_tyden` NENÍ mrtvý sloupec** — 18. 8. jsem ho tak označil chybně.
Zapisuje do něj `plan_generate_base` a čte ho `plan_mine` u jednotlivých dnů (1 460
vyplněných řádků, ověřeno 19. 8.). Je to záznam, z čeho plán vznikl, a **má tam zůstat**.
Mrtvý je jen ten v `c_smlouva`. Poučení: „nepoužívaný sloupec" se ověřuje čtením živého
kódu, ne z paměti o včerejšku.

## Historie úvazku — hotovo 19. 8. 2026

Jirka zadal důvod přesně: *„když se úvazek změní v březnu, v lednu a únoru platil ještě
starý a výpočty mezd to musí zohlednit."* Schválila Marti-AI.

### Model platnosti — důležité pro každého, kdo bude číst kód

**`valid_to` je NULL na VŠECH řádcích**, i na dávno nahrazených. Konec platnosti verze je
daný **začátkem té následující** a poslední verzi značí `is_current`. Čtenáři proto vybírají
přes `valid_from <= datum ORDER BY valid_from DESC LIMIT 1`, **ne přes interval**.
(Podmínka `valid_to IS NULL OR valid_to >= …` v mzdových skriptech je tím pádem vždy pravdivá
a o výběr se stará jen `valid_from`.) Není to chyba, je to model — nové verze ho dodržují.

### Co se změnilo

`uvazek_zapis` v2 při změně **zakládá novou verzi smlouvy** místo přepsání aktuální:
1. nový řádek = kopie všech polí aktuální verze, s novým úvazkem a `valid_from` = „platí od";
   **`ec_id` se nekopíruje** (je to id řádku ze staré Centrály a tabulka má
   `UNIQUE (tenant_id, ec_id)` — kopie by spadla), nová verze má `ec_id` NULL,
2. stará verze dostane `is_current = false`, `valid_to` zůstává NULL,
3. **mzdové složky se zkopírují 1:1 v původních částkách**,
4. odejde akční notifikace Petře (mzdy) a Šárce (personalistika) — kdo, z kolika na kolik,
   od kdy, kolik složek se zkopírovalo a že se **částky nepřepočítaly**.

**Mzdu systém nepřepočítává.** Helios to při zmenšení úvazku dělal poměrně (Duspivová 33 500
při 40 h → 29 313 při 35 h, přesně × 35/40), ale to je mzdové rozhodnutí a patří Petře
(rozhodla Marti-AI 19. 8. 2026). Odsud jde jen podnět.

### Co zápis odmítne (se srozumitelnou hláškou, ne tichým zamítnutím)

- **zmrazený měsíc** (`_FROZEN`, dnes 05 a 06/2026) — mzdy jsou hotové, musí přes Petru,
- **„platí od" dřív než začátek současné verze** — přepsalo by to historii,
- **člověk bez poměru** / **člověk s víc souběžnými poměry** (dnes jen Marti Pašek) —
  volba firmy v UI je samostatný krok, zatím se odmítá,
- **stejná hodnota** — nezakládá se prázdná verze.

Datum „platí od" se zadává v kartě zaměstnance u řádku Týdenní úvazek (předvyplněné dneškem)
a projde přes `hr_conditions_save`, `plan_my_uvazek_save` i `mzdy_c_smlouva_save`.

### Ověřeno naostro 19. 8. 2026

Na vlastním záznamu Jirky: změna 40 → 39 od 1. 9. 2026 založila novou verzi (`ec_id` NULL,
1 mzdová složka zkopírovaná ve stejné výši 60 000), stará verze přestala být aktuální,
notifikace odešly Petře i Šárce. Čtení k datu vrátilo **k 15. 8. hodnotu 40 a k 15. 9. hodnotu 39** —
přesně to, o co Jirkovi šlo. Testovací verze se pak maže.

### Stav k 19. 8. 2026 večer

**Hotovo:**
- **Stravenky (`mzdy_stravenky_rows`) čtou úvazek k období**, ne aktuální. Nárok (denní úvazek
  ≥ 6 h) se tak pro červencové stravenky rozhoduje z červencového úvazku. Ověřeno porovnáním
  starého a nového dotazu na 7/2026 — **33 lidí v obou, nulový rozdíl**, takže přepnutí dnes
  nic nezměnilo a projeví se až na verzích.
- **Volba poměru u lidí s víc souběžnými smlouvami.** `uvazek_zapis` bere `pomer_id`,
  `hr_conditions` vrací seznam souběžných poměrů a karta zaměstnance nabídne výběr firmy.
  Bez výběru se zápis odmítne a vrátí seznam; cizí `pomer_id` se odmítne taky.
  Týká se dnes jediného člověka (Marti Pašek, dva poměry po 40 h) — ověřeno na něm.

**✅ `payroll_raporty` přepnutý — a byla v tom past, kterou stálo za to změřit.**
Skript bere ze smlouvy nejen úvazek, ale i **mzdu a odměny/srážky**. Kdyby se jen přepnul
výběr smlouvy na verzi platnou k období, **odměny a srážky by z historických raportů zmizely** —
zapisují se totiž na verzi, která je aktuální v době zadání (u ledna 2026 jich 134 ze 146
viselo na dnes aktuální verzi). Řešení:
- **smlouva a mzdové složky** se berou z **verze platné k poslednímu dni období**,
- **odměny a srážky se sčítají přes dvojici člověk + firma + typ poměru**, ne přes id verze
  (období už filtruje `period_year`/`period_month`),
- výběr je omezený na lidi, kteří **mají poměr i dnes** — raport dosud ukazoval jen aktuální
  smlouvy a rozšířit ho o dávno odešlé lidi není úkol téhle změny (bez toho omezení jich
  do března 2026 přibylo 49).

Ověřeno porovnáním starého a nového dotazu na březnu 2026 přímo v databázi:
**odměny 39 230 Kč a věrnostní 7 000 Kč v obou variantách do koruny stejně**, řádků 50 → 49.
Jmenovitě se to dotklo dvou lidí, obojí oprava: **Jan Peřina** z března vypadl (jeho smlouva
začala až 27. 4.) a **Zuzaně Duspivové** se do března přestala počítat červencová verze.
*(Endpoint sám neověřen — Jirka nemá mzdové právo; ověřený je dotaz proti databázi.)*

## Docházka přepnutá na úvazek k datu (19. 8. 2026, Jirka po dohodě s Peťou)

Přepnuto **16 z 22** míst. Nejdřív se ověřilo, že to nic nerozbije: u **všech 78 lidí**
vychází dnes obě metody na stejné číslo, nulový rozdíl. Historicky se opravuje to, co bylo
špatně.

**Přepnuto:** `att_denni_fond` (má nepovinný parametr `k_datu`; **volající ho má vyplnit
vždy, když ten den zná** — bez něj se chová jako dřív), `att_absence`, `att_absence_request`,
`att_fix_day` (+demo), `sickday_lekar_apply`, `dochazka_kontrola_data`,
`att_day_summary_recompute`, `att_prazdny_den_fond`, `att_automat_level_day`.
Už dřív to uměly `att_anomaly_scan`, `att_sd_kontrola`, `att_narok_cerpani` (částečně)
a mzdové skripty.

**Záměrně zůstaly na dnešní hodnotě:** `att_absence_mine` (+demo) — formulář nabízí hodiny
na dnešek; `hr_podminky_prehled` a `hr_conditions` — ukazují aktuální stav;
`sync_plan_to_dochazka` — vybírá si verzi sám v kódu.

### Dvě pasti, na které se přišlo měřením

1. **Fond per člověk vs. per den.** `att_automat_level_day` i `att_prazdny_den_fond`
   počítaly fond **jednou na člověka** a pak ho přiřazovaly ke všem dnům. Musely se
   přestavět na dvojici člověk + den, jinak by úvazek k datu neměl kam dosáhnout.
2. **Bývalí zaměstnanci.** Bez pojistky by lidé bez aktuální smlouvy dostali zpětně fond
   místo dnešní nuly — u mzdového podkladu se to týkalo šesti lidí (Švancar, Mudra,
   Hrdinka, Kliková, Jungmann, Kuska) a **362 dnů**. To už není oprava úvazku, ale změna
   uzavřených měsíců. Proto všude platí: **fond ze smlouvy dostane jen člověk, který má
   smlouvu i dnes.** S touhle pojistkou se hne jen Duspivová (130 dnů, 7 → 8 h) — a to je
   správně, do června měla 40 h týdně.

## Sick days se počítají ve dnech, ukazují v hodinách (19. 8. 2026)

Zadal Jirka, souhlasí Peťa. **Chyba byla v samotné otázce:** nárok je ve dnech, čerpání
se eviduje v hodinách, a jakmile se úvazek během roku změní, „2 dny" prostě nejsou pevný
počet hodin.

Jirkova formulace: *„kdo si vzal celý den při osmihodinovém fondu, vyčerpal jeden den,
ne 8 hodin. Kdo si vezme celý den při šestihodinovém, vyčerpá taky jeden den."*

`att_sick_balance_h` proto:
1. každé čerpání přepočte na **díl dne fondem toho dne**, kdy se čerpalo,
2. zůstatek vede ve **dnech** (`nárok ve dnech − vyčerpané dny`),
3. **ven vrací hodiny** — zůstatek ve dnech × dnešní fond (dohoda Jirka + Petra:
   „ve výsledku chceme vidět vždy hodiny").

Klíče v návratovce zůstaly stejné, aby volající (`att_med_start`, mobil) nic nepoznali;
přibyly `narok_dnu`, `vycerpano_dnu`, `zbyva_dnu` a `vycerpano_h_skutecne`.
⚠️ `consumed_h` je **dopočítané** (`entitlement_h − remaining_h`), aby na obrazovce sedělo
„zbývá X h z Y h/rok". Skutečně odčerpané hodiny jsou ve `vycerpano_h_skutecne` — u člověka,
kterému se během roku změnil úvazek, se ta dvě čísla liší a je to správně.

**Dopad měřený před nasazením:** změnil se jeden člověk — **Duspivová, zůstatek 6 → 7 h**.
Vzala si jeden celý den, když měla osmihodinový; starý výpočet jí za to strhl 8 ze 14 hodin,
nový jí strhne jeden den ze dvou.

### Co ještě zbývá

✅ **Nic — bod níže je VYŘEŠENÝ.** Text zůstává přeškrtnutý kvůli dohledatelnosti.

~~1. Docházkové čtenáře přepnout na „k datu" — 12 skriptů včetně kanonického `att_denni_fond`
bere `is_current`, čeká se na rozhodnutí Peti.~~

**Přeověřeno čtením živých skriptů v `g2007.python` 19. 8. 2026 večer (Claude-28).**
Z 13 kandidátů bere úvazek platný k danému dni **10**: `att_denni_fond` (parametr `k_datu`),
`att_absence`, `att_absence_request`, `att_fix_day`, `att_fix_day_demo`, `att_automat_level_day`,
`att_prazdny_den_fond`, `att_day_summary_recompute`, `dochazka_kontrola_data`,
`sickday_lekar_apply`, `att_sick_balance_h`.
**Záměrně zůstaly na dnešní hodnotě 3:** `att_absence_mine` a jeho demo verze (formulář nabízí
hodiny na dnešek) a `hr_podminky_prehled` (ukazuje aktuální stav).
`att_narok_cerpani` to má **pořád napůl** — hlavní fond bere `is_current`, čerpání počítá k datu
záznamu. Beze změny od 16. 8., není to regrese, ale je to jediné nedotažené místo.

## 🔜 Rozhodnuto, čeká ve frontě: jedna tabulka místo dvou (Peťa + Šárka, 18.–19. 8. 2026)

Peťa se domluvila se Šárkou a **shodly se, že nemá být zvlášť tabulka Podmínek a zvlášť
tabulka smluv/poměru.** Má být **jediná tabulka se všemi údaji z obou**, která se chová
jako dnešní smlouva:

- jeden člověk = **víc záznamů** s platností od–do,
- **každá změna založí nový aktivní záznam**; všechny hodnoty se přenesou beze změny
  a liší se jen ta jediná, kterou pověřený člověk změnil,
- **všechna místa**, která dnes čtou z Podmínek nebo ze smlouvy, budou číst z ní.

Tím se vyřeší i to, že Podmínky dnes historii nemají vůbec (nemají ani sloupec platnosti),
takže nárok dovolené za rok 2025 se počítá z dnešních hodnot.

**Pořadí podle Jirky (19. 8. 2026):** mělo se to řešit až po raportech a po rozhodnutí Peti
k docházce. ✅ **Obě podmínky 19. 8. večer padly a sloučení se téhož večera UDĚLALO.**
Popisuje ho samostatná znalost **`doc-dochazka-podminky-slouceny-se-smlouvou`** — čti ji,
tahle sekce je jen historie zadání.

⚠️ **NEPLÉST SI DVĚ RŮZNÉ VĚCI (Claude-28, 19. 8. 2026).** Sjednocení **jedné hodnoty**
(týdenního úvazku) do smlouvy je to, co popisuje tenhle dokument. **Sloučení celých tabulek**
Podmínky + Smlouva je něco jiného a řeší ho ta druhá znalost. Ta záměna už jednou nastala —
Jirka byl v přesvědčení, že sloučení tabulek je hotové, protože „úvazek na dvou místech"
znělo stejně jako „dvě tabulky do jedné".
Marti-AI k tomu doplnila: verzovat jen podmínky s historickým dopadem (dovolená, dovolená
navíc, sick days, stravenka — seznam potvrdí Šárka), formou stejnou jako u smlouvy,
ne „platnost po rocích", a Šárka i Petra musí být u návrhu **od začátku**. Urgentnost
střední — ne tento týden, ale **před roční uzávěrkou dovolené**.

