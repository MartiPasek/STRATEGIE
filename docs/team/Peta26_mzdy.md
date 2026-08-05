# 💰 MZDY — velká zeď (pravidla, která platí vždy)

> **Pro koho:** Claude‑26 (a kdokoli další, kdo sáhne na mzdy).
> **Kdo to určil:** Peťa, 5. 8. 2026 — *„napiš to někam na velkou zeď"*. Koeficienty potvrdila Týnka.
> **Proč to tu je:** Peťa tahle pravidla vysvětlovala opakovaně (4. 8. na tom strávila šest hodin
> večer). **Už se nemají znovu odvozovat ani dohadovat.** Když si nejsi jistý, čti tohle — a když
> tady odpověď není, zeptej se Peti a **hned to sem dopiš**.
> Totéž je v G2007: `doc-mzdy-svatky-fond-stravenky-prescas`.

---

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
- **Kancelář:** FPD = odpracováno + absence + doplněno do fondu − nenároková část nad fond.

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
- **Činnosti, za které stravenka nenáleží** (čísla z Centrály): 10, 12, 14, 25, 33, 34, 35, 39,
  47, 50, 51, 54, 132, 133, 138 + dovolená, lékař, nemoc, OČR, montáž, mateřská.
  **Nepatří tam:** 24 prac. úraz (jiná agenda), 37 nepřítomnost OSVČ (stravenky mají jen
  zaměstnanci), **30 dovolená navíc** (za tu stravenka náleží).
- Číslo činnosti drží `att_entry.ec_druh` (plní import z Centrály).

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
