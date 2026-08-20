# Landmark – měsíční podklad mezd (výpočet OBL/HO/korekce, zaokrouhlení, fakturace)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Landmark – měsíční podklad a fakturace (mzdy)

Landmark TAX s.r.o. = daňová optimalizace části mzdy do složek osvobozených od daní/pojistného:
**náhrada za údržbu oděvu (OBL)** a **náhrada za home office (HO)**; o stejný objem se poníží
osobní ohodnocení (**korekce OSOH**). Landmark z toho fakturuje odměnu.

## ⭐ VÝPOČET UŽ EXISTUJE — `lm_engine`. NEODVOZOVAT ZNOVU. (doplněno 6.8.2026)

`g2007.python`, kód **`lm_engine`** (aktivní, verze 2). V docstringu: *„Ověřená matematika
(Excel 45/45, Marti/Landmark e-mail 30.6.2026)"* — ověřeno na všech 45 případech proti Excelu
přímo od Landmarku. Volá se z `mzdy_benefity_apply`:
`_ereg.call("lm_engine", fond, odprac, obl_dny, obl_sazba, ho_hod_narok, osoh)`.

**Dělba práce:** `lm_engine` = čistá matematika (dostane hotové vstupy, vrátí OBL/HO/korekce).
`mzdy_benefity_apply` = připraví vstupy (fond, nárok, výjimky, zkušební doba, úvazek).

Kdo má Landmark kontrolovat, **zavolá `lm_engine`** a porovná jeho výstup s výplatnicí.
Nepřepisovat jeho vzorec do vlastního skriptu — 6.8.2026 to Claude-26 udělal, ověřoval pak
na dvou řádcích místo hotových 45 a stálo to mzdovou účetní večer.

## ⚠️ Landmark má JINÝ FOND než zbytek mezd — schválně (doplněno 6.8.2026)

**Landmark počítá fond VČETNĚ svátků** = všechny dny Po–Pá × denní úvazek. Přesčas a stravenky
ho počítají **BEZ svátků**. Není to chyba: červenec 2026 → Landmark 23 dnů (184 h při 8h úvazku),
přesčas 22 dnů (176 h); květen 2026 → Landmark 21 dnů (168 h), přesčas 19 dnů (152 h).
Potvrzeno v podkladu od Landmarku (buňka *Fond měsíce*): **„168 — včetne svatku"**.
Kdo dosadí fond bez svátků, dostane u všech jiná čísla a bude to vypadat jako chyba ve mzdách.

## ⚠️ Osobní ohodnocení do výpočtu (doplněno 6.8.2026)

- **Bere se `OsOhodReal`, NE `OsOhod`.** V podmínkách jsou dva sloupce; u většiny lidí stejné,
  liší se u těch, komu se osobní ohodnocení navyšovalo kvůli Landmarku. `OsOhod` = částka
  **před rozkladem**, `OsOhodReal` = co má zbýt v penězích. Ověřeno proti podkladu od Landmarku
  (list „Vstupní data", sloupec *HPP osobní ohodnocení*) — sedí na korunu.
- **Sčítá se celá pohyblivá část**, ne jen řádek osobního ohodnocení: `OsOhod` + `MzdPremie`
  + `IndividualOhod` + `OdmenaGarant` + `Produkce` + `VedeniLidi` + `FKodexKultur` + `Kvalita`.
  Poznávací znamení, že člověk má víc složek: v podmínkách se mu liší `HrHodBezFK` od `HrHodsFK`.
- **Korekce nesmí poslat osobní ohodnocení do minusu** — když by vyšlo záporné, je nula.

## Kdo má nárok (doplněno 6.8.2026)

- jen **HPP** (OSVČ ven), **po zkušební době**, **denní úvazek ≥ 6 h**
- **home office = 6 dnů napevno** pro každého s nárokem, nezávisle na self-service volbě;
  engine si to sám poměrově zkrátí podle odpracovaného fondu
- nárok na HO = kancelář, ale s **pevnými výjimkami zapsanými v kódu** `mzdy_benefity_apply`
  (`_HO_DILNA_VYJIMKA` = dílna, která HO má; `_HO_BEZ_NAROKU` = kancelář bez nároku)
- sazba oděvy **279 dílna / 109 kancelář**, HO **43 Kč/h**
- fond zkráceného úvazku = **denní úvazek × pracovní dny**, denní úvazek = `engagement.uvazek_tyden_h / 5`

## Daňové zacházení ve výplatnici (doplněno 6.8.2026)

Náhrada 794 se vyplácí **nezdaněná** — složka **4320 „Korekce Landmark"** ji vyjímá ze základu
daně, takže v hrubé mzdě figuruje `+794 −4320`. Ve výplatnici je u složky 432 vidět **výsledek
po odečtení náhrad** (sloupec O metodiky), ne hodnota pro mzdový systém (sloupec N).
Ověřeno 6.8.2026 do koruny až na čistou mzdu.

## Data ve STRATEGII
Vygenerované výplatnice `tenant.payslip_item` (tenant_id=2), složky: **794 = OBL**, **795 = HO**.
Firma přes `company_id`→`tenant.company.code` (EC/ES), jméno přes `tenant.att_employee`.
Od června 2026 se mzdy dělají napřímo v S (Landmark šablonu už nepoužíváme).

## Vzorce (oficiální metodika Landmark, 27.7.2026)
Vstupy: C = sazba oděv/směna (109/279), D = HO sazba/hod (43), E = HO hodiny, F = základní OSOH,
G = fond měsíce (hod), H = odpracované hodiny, I = odpracované dny.
- **OBL měsíc = MROUND(I*C; 1)** — dny × sazba, zaokrouhleno na CELÉ Kč.
- **HO měsíc = MROUND(H/G*E; 0,5) * D** — HO hodiny redukované docházkou, zaokrouhleno na 0,5 HODINY, pak × 43. (Proto částka HO může končit na ,50.)
- podíl docházky L = H/G; OSOH po redukci M = L*F; OSOH final O = M − OBL − HO; OSOH do SW N = O/L.
- **Korekce OSOH do SW = N − F = −(OBL+HO)/L** — v abs. hodnotě VĚTŠÍ než OBL+HO, protože se „nahrubovává" zpět dělením koeficientem docházky (systém OSOH sám krátí docházkou).
- Volno vstupuje jen přes docházku (nižší H → nižší L → menší HO i OSOH; OBL přes odpracované dny I).

## Fakturace Landmark (klíč)
Sazba není v datech; odvozena zpětně z faktur a shodně sedí na duben i květen 2026 (obě firmy):
> **fakturace bez DPH = 9,06 % × (Σ OBL + Σ HO)** → + 21 % DPH → zaokrouhlit na celé Kč.
(Ověření: EC 4/2026 58 616×9,06%=5 310,61; ES 4/2026 146 790→13 299,17; EC 5/2026 52 140,5→4 723,93; ES 5/2026 147 049,5→13 322,68.)

## Automatika
Modul `modules/erp/api/landmark_report.py` (registrace v `apps/api/main.py`, nasazeno 22.7.2026):
- scheduler `landmark_sched_start()` (jen primár) → **15. v měsíci** pošle podklad za PŘEDCHOZÍ měsíc mailem na **nakup@eurosoft.com** (guard proti dvojímu odeslání = marker soubor v temp);
- ruční/test endpoint `GET /api/v1/erp/app/mzdy/landmark-send` (gate `_is_cockpit`);
- odesílá z default persony přes EWS; xlsx po lidech (EC+ES) + souhrn 9,06 %.
- Sazba 9,06 % = konstanta `RATE` v modulu.
- Náš systém drží HO na celé Kč, Landmark na půlkoruny → rozdíl zanedbatelný (na faktuře pár Kč); pixel-přesně by šlo dopočítat HO = MROUND(H/G*E;0,5)*43.

Detailní provozní doc (i s kontrolními příklady): `docs/Z_landmark_podklad_mzdy.md`.
Heslo k metodickému Excelu od Landmarku: „pasek".

