# 💰 MZDY — velká zeď (pravidla, která platí vždy)

> **Pro koho:** Claude‑26 (a kdokoli další, kdo sáhne na mzdy).
> **Kdo to určil:** Peťa, 5. 8. 2026 — *„napiš to někam na velkou zeď"*. Koeficienty potvrdila Týnka.
> **Proč to tu je:** Peťa tahle pravidla vysvětlovala opakovaně (4. 8. na tom strávila šest hodin
> večer). **Už se nemají znovu odvozovat ani dohadovat.** Když si nejsi jistý, čti tohle — a když
> tady odpověď není, zeptej se Peti a **hned to sem dopiš**.
> Totéž je v G2007: `doc-mzdy-svatky-fond-stravenky-prescas`.

---

## 0. ⭐ VŠECHNY VSTUPY JDOU ZE STRATEGIE, NE Z CENTRÁLY

Peťa 5. 8. 2026: *„většina docházky už v červenci v Centrále není, proto nedává smysl se tam
na něco koukat."*

| co | odkud |
|---|---|
| hodiny, fond, přesčas | `tenant.att_den_hodiny` (naše docházka včetně oprav) |
| stravenky | `tenant.att_entry` podle **čísla činnosti** (`ec_druh`) |
| pracovní dny a svátky | `tenant.firemni_kalendar` (doplňuje se sám) |
| základ, osobko, **hodinová sazba přesčasu** | `tenant.helios_wage_snapshot` (sazba = `HrHodsFK`, tedy **s FK**) |
| příplatky, odměny, srážky | `tenant.wage_movement` |
| prémie ze zakázek | příplatky → složka **651** (stará docházková cesta **vypnutá**) |
| jednatelé a DPP | `tenant.mzdy_rucni_slozka` |
| denní souhrn docházky | `tenant.att_day_summary` — **od 6. 8. 2026 počítaný z naší docházky** (viz níže) |

Hlídá to pojistka **`mzdy-vstupy-ze-strategie`** a je to napsané i v hlavičce skriptu
`mzdy_generuj`, takže to vidí každý, kdo ho otevře.

### ⚠️ OPRAVENO 6. 8. 2026 — zrcadlo docházky se plnilo z Centrály

Do 6. 8. tady stálo, že *„zrcadlo `att_day_summary` se do mezd nepoužívá"*. **To nebyla
pravda** — používalo se, a plnilo se přitom ze staré Centrály. Viselo na něm:

- **dovolená do Heliosu** (složka 211) — dny z `att_entry`, ale **hodiny ze zrcadla**
- **Landmark náhrady** (oblečení 794, home office 795, korekce 432) — **absence ze zrcadla**
- **náhradní volno** v kaskádě přesčasu

Rozsah: hodiny se lišily u **39 lidí o 84,8 h**, absence u 10. Zeman měl v Centrále 24 h
dovolené, u nás 104 h — do mzdy mu šlo 24 h a náhrady se mu krátily, jako by skoro nechyběl.

**Od 6. 8. se zrcadlo plní přepočtem z naší docházky** (`att_day_summary_recompute`,
tlačítko „Přepočítat" v Mzdových podkladech) — a to na všech cestách: při generování mezd,
přes `@@DOCHSUM`, i z řídicího pultu. Ověřeno na červencových výplatnicích: Zeman má
složku 211 = **104 h / 13 dnů / 38 178 Kč**.

Rozhodly Peťa + Kristý + Týnka. Kristý: *„tabulku můžeme použít, to je ok, ale musí být
plněná daty ze STRATEGIE."* Detail: G2007 `doc-mzdy-zrcadlo-dochazky-ze-strategie`.

**KVĚTEN 2026 je výjimka** — zůstává z Centrály (Peťa: *„ten květen ne, ten je z centrály
správně"*, květnové mzdy se dělaly ještě z Centrály). Květen i červen 2026 jsou proto
v seznamu zmrazených měsíců přímo v přepočtu, takže je nepřepíše ani ruční spuštění.

### Co se pro mzdy ČTE z Centrály (stav k 6. 8. 2026)

Jediné dvě věci:

1. **Mzdové podmínky a hodinová sazba** — `helios_wage_snapshot`, snímek
   z `EC_FinZamPodminky` (plní se **ruční** akcí, ne automatem)
2. **Květen 2026** — viz výše, zůstává z Centrály

**Všechno ostatní mzdy čtou ze STRATEGIE.**

⚠️ **Nepleť „odkud mzdy čtou" s tím, „jak se tam data dostala"** (Peťa 6. 8. 2026).
Příplatky a srážky mzdy berou z `tenant.wage_movement`, **tedy ze STRATEGIE** — a je
jedno, že tam část přišla Jirkovým importem z Centrály a část jsme 5. 8. doplnili
ručně z Excelu (65 řádků). Pro mzdy je zdroj naše tabulka, ne Centrála.

## 1. Odkud se berou hodiny — ZE STRATEGIE

Hodiny pro mzdy se berou **z naší docházky**: funkce **`tenant.att_den_hodiny(2, od, do)`**.
Ta počítá to, co Peťa vidí v aplikaci — slučuje překrývající se úseky, odečítá přestávky uvnitř
práce a přičítá doplnění do fondu.

⛔ **NIKDY ne ze zrcadla Centrály `tenant.att_day_summary`.** Opravy docházky se dělají u nás
a do Centrály nedotečou.

**Důkaz (7/2026):** Svatoš měl v zrcadle **123,85 h / 17 dnů**, v naší docházce **185,66 h / 23 dnů**.
Kdyby se četlo zrcadlo, přišel by o 9,66 h přesčasu — z toho 7,92 h odpracovaných ve svátek
za dvojnásobek.

Hlídá to pojistka **`mzdy-hodiny-ze-strategie`**.

## 2. FPD (fond pracovní doby) = odpracováno + absence

- **Výroba:** FPD = **odpracováno + absence** (dovolená, nemoc, lékař, OČR… plní fond).
  → v datech: `hodiny_mzdove + hodiny_absence`
- **Kancelář:** FPD = odpracováno + absence + doplněno do fondu − **nenároková část nad fond**.
  → v datech: `hodiny_mzdove + hodiny_absence − hodiny_nad_fond`
  (doplnění do fondu je **už uvnitř** `hodiny_mzdove`, proto se nepřičítá zvlášť)

**Ověřeno na červenci 2026:**

| kdo | | mzdové | absence | nad fond | **FPD** |
|---|---|---|---|---|---|
| Veverka | kancelář | 177,01 | 0,00 | 0,77 | **176,24** |
| Svatoš | výroba | 185,66 | 0,00 | 0,00 | **185,66** |
| Diviš | výroba | 135,94 | 48,00 | 0,00 | **183,94** |

Veverkových 176,24 h sedí přesně na to, co ukazuje aplikace.

**Přesčas = FPD − měsíční fond.** Ne „odpracováno − fond" — na tom by Diviš (6,02 h odpracovaných
ve svátek) nedostal příplatek vůbec.

## 3. Měsíční fond = pracovní dny BEZ svátků

Svátek, který padne na pracovní den, se **proplatí, ale nemá se odpracovat**:

- do mzdy se **připočte**, aby byl zaplacený,
- do **fondu pro výpočet přesčasu nepatří** → červenec 2026 = 22 dnů = **176 h** (ne 184).

Peťa: *„těch 8 hodin nemají odpracovat, to se jim jen zaplatí."*

## 4. Stravenky

- **Za svátek stravenka NENÁLEŽÍ** (není to odpracovaný den). Do 5. 8. 2026 se počítala všechna
  Po–Pá, takže za 6. 7. dostal stravenku navíc úplně každý a člověk na mateřské vyšel 1 místo 0.
- **Nárok:** HPP + po zkušební době + denní úvazek ≥ 6 h.
- **Sazba 82 Kč/den.**
- **Činnosti, za které stravenka nenáleží — 21 čísel** (čísla z Centrály, ověřeno 5. 8. 2026
  proti číselníku `EC_DilnaCinnosti` + `EC_Dochazka_CinnostiRezie`):

  | č. | název | | č. | název |
  |---|---|---|---|---|
  | 9 | Služební cesta / montáž | | 39 | Neplacené volno |
  | 10 | Nařízené volno | | 47 | Volno 70 % |
  | 12 | Nahrazení volna | | 50 | Volno 80 % |
  | 14 | Služeb. cesta/montáž – čas na cestě | | 51 | Volno 90 % |
  | 20 | Dovolená | | 54 | Nepřítomen pro APS |
  | 21 | Lékař | | 132 | Soukromé záležitosti |
  | 22 | Nemoc | | 133 | Náhradní volno |
  | 23 | OČR | | 138 | Překážka v práci |
  | 25 | Paragraf | | | |
  | 33 | Otcovská | | | |
  | 34 | Ostatní/Nepřítomen – s náhradou mzdy | | | |
  | 35 | Volno 60 % | | | |
  | 36 | Mateřská dovolená | | | |

- **Stravenka NÁLEŽÍ** (záměrně vynechané): **8** home office · **24** prac. úraz (jiná agenda) ·
  **30 dovolená navíc** · **31** sick day (= přítomnost) · **37** nepřítomnost OSVČ (stravenky
  mají jen zaměstnanci).
- Když u záznamu číslo činnosti chybí, rozhodne **typ záznamu**: dovolená, lékař, nemoc, OČR,
  mateřská, neplacené, volno 70/80/90 %.
- Číslo činnosti drží `att_entry.ec_druh` (plní import z Centrály).

### ⚠️ Náš seznam je ŠIRŠÍ než Centrála — a je to tak schválně (Peťa 5. 8. 2026)

Procedura Centrály `EC_Mzdy_PrepocetMesicZam` odečítá jen **14** činností:
9, 20, 21, 22, 23, 33, 34, 35, 36, 39, 47, 50, 51, 138.

**My navíc vylučujeme 7:** 10 nařízené volno · 12 nahrazení volna · 14 čas na cestě ·
25 paragraf · 54 nepřítomen pro APS · 132 soukromé záležitosti · 133 náhradní volno.
Peťa 5. 8. 2026: *„nech to tak, mně to dává smysl."*

**Nemoc (22):** Centrála ji odečítá až nad 2 hodiny (kdo odpracoval víc než 6 h, stravenku má),
my ji odečítáme vždy. Peťa 5. 8. 2026: *„nech to jak to máme."*

Rozdíl proti Centrále je tedy **vědomý, není to chyba k opravě**.
Hlídá pojistka **`stravenky-vyloucene-cinnosti`**.

## 5. Příplatky za přesčas (jen VÝROBA)

| kdy přesčas vznikl | koeficient | „nahrazený" (kryje placené volno) |
|---|---|---|
| **svátek** | **2,00** | 1,10 |
| **víkend** (So/Ne) | **1,35** | 0,45 |
| **zbytek** (běžný den) | **1,25** | 0,35 |

- Rozděluje se **kaskádou**: nejdřív hodiny odpracované ve svátek, pak víkendové, zbytek je
  běžný den. Stejnou kaskádou zvlášť část krytá nahrazeným volnem.
- „Nahrazený" = doplácí se jen rozdíl + 0,1 = zádržné 10 % z hodinovky.
- Všechno jde do mzdové složky **651**.
- Historie: koeficient za svátek byl do roku 2023 **2,25**, od té doby **2,00**.
- **Kancelář přesčas nedostává** — kategorie „Volná kancelářská doba (bez přesčasů)" (23 lidí).
  Centrála jim ho jen dopočítává do sloupců, ale nevyplácí.

## 6. Kalendář se doplňuje sám

Skript **`kalendar_zajisti`** dopočítá české svátky včetně pohyblivých Velikonoc (Meeus) do
`tenant.firemni_kalendar`. Je idempotentní, **ruční firemní výjimky nepřepisuje** a volá se
automaticky ze stravenek i z přesčasů — **leden 2027 se doplní sám**, nikdo to nemusí řešit.

## 7. Kde to je v kódu (`g2007.python`)

| skript | co dělá |
|---|---|
| `kalendar_zajisti` | doplnění kalendáře na rok |
| `mzdy_stravenky_rows` | stravenky — pracovní dny z kalendáře, vyloučené činnosti |
| `mzdy_loajalita_rows` | přesčas — FPD z `att_den_hodiny`, fond bez svátků, koeficienty `_KOEF_*` |
| `mzdy_absence_rows` | absence do Heliosu (dovolená 211, nemoc 200, lékař 243, OČR 251, mateřská 255) |
| `mzdy_benefity_apply` | Landmark náhrady (oblečení 794, home office 795, korekce 432) |
| `mzdy_generuj` | celý běh „čistá voda" |

## 7b. ⛔ ZRUŠENÉ ZÁZNAMY DOCHÁZKY SE DO MEZD NEPOČÍTAJÍ (Peťa 6. 8. 2026)

**Pravidlo:** každý mzdový výpočet, který čte `tenant.att_entry`, MUSÍ vyfiltrovat zrušené
záznamy:

```sql
AND COALESCE(a.status,'') NOT IN ('superseded','announced')
```

**Proč to tu je.** Když se tatáž nepřítomnost dostane do docházky víckrát (plán z Centrály +
docházka z Centrály + ruční oprava), přebytečné řádky se označí `superseded` a platný zůstane
jeden. **Data jsou tím pádem v pořádku** — chyba byla v tom, že mzdy ten příznak ignorovaly
a sčítaly i zrušené.

**Co se stalo (červenec 2026):**

| kdo | vykázáno | správně | dopad |
|---|---|---|---|
| Jirkovský ES 486 | 48 h nemoci (3 záznamy × 8 h × 2 dny) | 16 h | **−5 043 Kč** na základu |
| Šafránková ES 381 | 232 h mateřské | 176 h | 0 Kč (mateřskou platí stát) |

**Proč to trefilo jen je dva:** dovolená (211) bere hodiny z `att_day_summary`, kde se
duplicity neprojeví, a dny přes `COUNT(DISTINCT entry_date)`. Ale **nemoc (200), lékař (243),
OČR (251), neplacené (246) a mateřská (255) se sčítají přímo z `att_entry`** — tam filtr
chyběl. Proto Zeman, Kolářová, Hájek ani Brudnová postižení nebyli, i když duplicity měli taky.

**Stav filtru k 6. 8. 2026** (ověřeno čtením z `g2007.python`):

| skript | filtr |
|---|---|
| `mzdy_absence_rows` | ✅ doplněn 6. 8. |
| `mzdy_benefity_apply` | ✅ doplněn 6. 8. |
| `mzdy_stravenky_rows` | ✅ měl už dřív |
| `payroll_raporty` (podklad) | ✅ měl už dřív |

> **Poznámka k diagnostice:** právě proto **podklad seděl a výplatnice ne**. Když se ti něco
> takového rozejde, podívej se nejdřív na filtry zrušených záznamů — ne na cesty zápisu.
> (Claude‑26 to nejdřív svedl na tři cesty zápisu; byla to slepá ulička.)

### Tři cesty, kterými se nepřítomnost dostane do docházky

Užitečné vědět, proč duplicity vůbec vznikají:

| značka (`source`) | odkud | kontrola duplicit |
|---|---|---|
| `plan_ec` | plán nepřítomností z Centrály (`sync_plan_to_dochazka`) | ✅ nepřepisuje obsazený den |
| `manual` | docházka z Centrály, řádek pořízený ručně v Centrále (`LoginFrom='C'`) | jen sama vůči sobě (přes `source_id`) |
| `manual_fix` | ruční oprava ve „🛠 Správě docházky" | ✅ pojistka z 6. 8. (nepřekročí denní úvazek) |
| `absence` | schválená žádost | ✅ pojistka z 6. 8. (jedna žádost, jedno schválení) |

Duplicity v červenci vznikly tak, že plán z Centrály přišel 28. 6., skutečnost z Centrály
30. 7. a ruční opravy pak 3.–6. 8. Každá vrstva o té předchozí nevěděla. **Nic je nepřidává
znovu samo** — jsou to jednorázové akce, které se navrstvily.

## 7c. Landmark — z čeho se počítá osobní ohodnocení (ověřeno 6. 8. 2026)

**Do výpočtu jde `OsOhodReal`, NE `OsOhod`.** V podmínkách (`podminky.xlsx`, `helios_wage_snapshot`)
jsou dvě různá čísla a u většiny lidí jsou stejná — liší se jen u těch, kterým se osobní
ohodnocení navyšovalo kvůli Landmarku:

| | OsOhod | OsOhodReal ← *tohle bere výpočet* |
|---|---|---|
| Dvořáková ES 49 | 16 300 | **5 550** |
| Brudnová ES 356 | 11 500 | **7 162** |
| Bernardová EC 475 | 10 681 | **4 047** |
| ostatní (Svatoš, Artim…) | 7 500 | 7 500 |

Peťa to vysvětlila poznámkou u Brudnové: *„Úprava osobního ohodnocení byla navýšena kvůli
navýšení sazby za náhradu oblečení. Od 1. 1. 2024 úprava rozkladu mzdy kvůli Landmarku."*
Čili `OsOhod` je částka **před rozkladem**, `OsOhodReal` je to, co má zbýt v penězích.

**Ověřeno proti podkladu přímo od Landmarku** (`MZDY_EUROSOFT SYSTEM_2026_5.xlsm`, květen 2026,
list „Vstupní data", sloupec *HPP osobní ohodnocení*): Dvořáková 5 550, Brudnová 7 162,
Čiviš 8 500, Diviš 8 500, Bláha 9 500, Artim 7 500 — **sedí na korunu s tím, co počítá systém.**

**Pozor: do výpočtu jde celá pohyblivá část, ne jen osobní ohodnocení.** Trunec = 6 500 osobní
+ 1 000 prémie + 2 000 individuální = **9 500**; Čiviš a Diviš = 7 500 + 1 000 = **8 500**;
Veverka = **15 500**. Kdo počítá jen s `OsOhod`, dostane špatně a bude to vypadat jako chyba
ve mzdách (Claude‑26 na to 6. 8. naletěl a hlásil šest neexistujících chyb).

**Vzorec** (Petin Excel, ověřeno na jejích referenčních řádcích i na červencových datech):

```
poměr    = odpracováno / fond
oděvy    = ZAOKROUHLIT(počet odpracovaných dnů × sazba)      sazba 279 dílna / 109 kancelář
home off = ZAOKROUHLIT.NA.NÁSOBEK(poměr × nárok h; 0,5) × 43
složka 432 = poměr × osobní ohodnocení − oděvy − home office
```

Ve výplatnici je vidět **výsledek po odečtení** (sloupec O), ne hodnota pro mzdový systém
(sloupec N). Náhrada 794 se vyplácí **nezdaněná** — složka **4320** ji vyjímá ze základu daně,
proto v hrubé mzdě figuruje `+794 −4320`. Ověřeno u Svatoše do koruny až na čistou mzdu
(základ daně 47 858 → záloha 7 185 → na účet 45 642).

**Osobní ohodnocení nesmí jít do minusu** (Peťa 6. 8.) — když by vyšlo záporné, je nula
(Bernardová).

## 8. Ostatní ověřené věci

- **Jednatelé:** EC 2 Pašek, EC 47 Mózer, **ES 41 Pašek** (číslo 15 neexistuje). Mají ruční
  složku 693 + plné stravné za celý fond měsíce. Pojistka `jednatele-cisla`.
- **Slevu na poplatníka a na děti, daň i pojistné počítá Helios sám** z mzdové karty —
  STRATEGIE je neposílá. Oprava se dělá v Heliosu na kartě.
- **OSVČ do mezd nejdou** — vedou se u nás jen kvůli historii.

## Ověření (5. 8. 2026)

Rozdělení přesčasu ověřeno proti Centrále na **červnu 2026: 14 z 16 lidí sedí na setiny**
(zbylí dva jsou kancelář, kterou vylučujeme). Červenec 2026 po opravě: přesčas má **18 lidí**
— nejvíc Čiviš 16,34 h, Svatoš 9,66 h (7,92 ve svátek), Diviš 7,94 h (6,02 ve svátek).
Stravenky 61 008 → 52 398 Kč.
