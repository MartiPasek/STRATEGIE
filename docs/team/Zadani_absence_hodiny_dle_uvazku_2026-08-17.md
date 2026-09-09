# Hodiny absence podle úvazku — zadání pro opravu

**Od:** Peťa (zpracoval Claude‑26) · **Pro:** Jirka + Claude‑28 · **17. 8. 2026**
Souvisí s koordinační nástěnkou, položka 30.

---

## 1. Vezměte si to celé vy

Soubor `modules/erp/api/dochazka_absence_sprava.py` **nemám rozdělaný** — v gitu je
čistý. Zápis ve `WORK_LOCK.txt` z 23. 7., ze kterého jste to nejspíš vzali, se týká
jiného souboru: `apps/api/static_db/dochazka-po-zakazkach.html` (ta obrazovka, ne
backend). Toho se držte dál, jinak vám nic nepřekáží.

## 2. Bod 3 neberu jako volbu mezi A a B

Ani jedna z těch variant sama o sobě nestačí. Má to umět tohle:

**Předvyplnit** denní fond člověka podle úvazku (Zuzka 7 h, ne 8).

**Nepustit nesmysl.** Ruční přepis smí měnit hodnotu jen na to, co pro daného
člověka a typ dává smysl. U Zuzky (fond 7 h):

| Typ | Smí projít |
|---|---|
| Dovolená i dovolená navíc | 7 (celý den) nebo 3,5 (půlden), nic mezi tím |
| Sick day | po celých hodinách, nejvýš 7 |
| Nemoc, OČR, neplacené | 7 |
| Lékař | skutečně chybějící čas, nezaokrouhluje se |

*Dovolená i dovolená navíc jdou do docházky jako jeden typ (`vacation`) — liší se
jen nárokem v Podmínkách, hodiny na den mají stejné.*

**Hlídat vyčerpání** nároku (D, DN, SD) před zápisem.

**Platit ze všech tří vstupů** — mobilní appka, Správa docházky, Opravy docházky.
Tohle je to hlavní. Osmička nebyla nikdy jen na jednom místě: opravovala se
31. 7. (sick day v appce), 3. 8. (žádost z appky), 12. 8. (rámec 8–16) a teď
Správa docházky. Nechci pátou.

## 3. Vzor už máte hotový — nepište to počtvrté

Přesně takhle už funguje sick day: pravidlo žije v `g2007.python` jako
**`att_sd_kontrola`** a volá ho mobil, formulář „Úprava absence" i Opravy docházky
(`att_fix_entry`, ř. 224–238) — kdo ho obejde, dostane odmítnutí **před** zápisem.
Hlídání stropu nároku je na tom stejně (`att_limit_kontrola` → `att_narok_osoba`
→ `att_narok_cerpani`).

Udělejte pro denní fond totéž: jedna funkce, tři dveře ji volají. Zaokrouhlovací
logika už existuje odzkoušená v `att_absence_request`, blok „POJISTKA: SROVNAT NA
POVOLENOU HODNOTU" — vytáhněte ji odtamtud.

Ve Správě docházky jsou natvrdo osmičky na třech místech:
`/save` ř. 715, `/new` ř. 845, `abs_promitni_zadost` ř. 504 (fallback při prázdném
`hours_per_day`). A protože se ten soubor stejně otevře — podle pravidla z 2. 8.
patří **nejdřív migrace do `g2007.python`**, pak teprve oprava.

---

## 4. Co jsme ověřili (a kde jsme se spletli)

**⚠️ POZOR — Duspivová má 7 h/den až od července.** Do června byla na plný úvazek
(potvrzuje Peťa; v `engagement` jsou dnes vedle sebe dva starší záznamy na 40 h
a jeden platný na 35 h). **Za leden až červen je u ní 8 h za den absence správně
a nesmí se to opravovat.**

Prakticky to znamená: kontrolu roku 2026 lze proti dnešnímu dennímu fondu dělat
jen **od července**. Za starší měsíce by srovnání s aktuálním úvazkem vyrobilo
falešné nálezy — a přesně to se nám stalo. Náš dotaz vypsal 7 řádků u Duspivové
(2. 1., 2.–6. 3., 10. 4.), a **všech sedm je v pořádku**, protože v té době ještě
měla osmihodinový úvazek.

**Ve správném okně (od července) váš závěr sedí** — jiný případ tam není.

*Poznámka k metodě, ať to nikdo nedělá po nás znovu špatně: první kontrolu jsme
udělali s filtrem `is_active` a vyšla nula. Absence se ale ukládají s
`is_active = false` (normální — není to běžící směna), takže se vyřadily všechny.
Po opravě dotazu vyšlo 7 řádků výše plus 57 ve stavu `superseded` (nahrazené,
v pořádku). Druhá past je právě ta historičnost úvazku výše. `att_den_hodiny`
mimochodem vyřazuje jen `superseded` a `announced` — `pending` se do mzdového
podkladu i do čerpání počítá.*

**Dvě věci z minulé verze zadání jsou naopak vyřešené, nemusíte je řešit:**

- **Zdroj pravdy pro úvazek je `engagement.uvazek_tyden_h`.** V Podmínkách je sice
  taky `uvazek_h_tyden`, ale u všech osmi lidí sedí na stejné hodnotě a v docházce
  ho nečte nic — sahají po něm jen mzdové smlouvy (`mzdy_c_smlouvy`,
  `mzdy_c_smlouva_save`) a mobil. Není to živé riziko.
- **Větev `sick` v `att_absence_request` je Nemoc (PN), ne sick day** — sickday
  v tom slovníku (`_ABS_TYP`, ř. 10) vůbec není, tudy se zadat nedá. Komentář
  „sick day = celé hodiny" tam tedy sedí na špatném typu a zaokrouhlení ukousne
  hodiny každému, kdo nemá celý fond. Dnes je takový jediný — Andrea Bernardová
  (6,40 h), a nemoc letos neměla, takže to zatím nekouslo. Opravte to při
  vytahování pravidla ven.

---

*Claude‑26 / Peťa*
