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
| `mzdy_generuj` | celý běh „čistá voda" |

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
