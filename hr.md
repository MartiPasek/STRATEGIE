# HR / Mzdy / Docházka — pracovní kontext

> Zakládá Claude (id=23), 11. 6. 2026 večer, na žádost Martiho:
> „Založ hr.md a podrobně to popiš, ať v pondělí, až to budeme ladit,
> nevycházíme opět z nuly."
>
> **Účel:** kompletní stav analýzy mezd + docházky, aby pondělní ladění
> s Kristý a Peťou navázalo bez ztráty kontextu. Čti shora dolů; sekce
> „OTEVŘENÉ OTÁZKY NA PONDĚLÍ" a „CO DÁL" jsou nejdůležitější.

---

## 1. Tři systémy, které se musí srovnat

| Systém | Co je | Role |
|---|---|---|
| **STRATEGIE** | náš nový systém (PostgreSQL `data_db`, tenant 2) | cílový — sem vše importujeme a počítáme |
| **Centrála docházka (EC)** | MSSQL `DB_EC`, čteno přes EUROSOFT MCP / SQL bridge | **zdroj pravdy pro docházku** (odpracováno, absence, konto přesčasů) |
| **Helios** | mzdový systém (DB_EC + DB_IS, cross-db) | **zdroj pravdy pro vyplacené mzdy** (skutečně proplaceno) |

Cíl: STRATEGIE má sedět s Heliosem **na haléř**. Není to odhad, je to
deterministická matematika (Martiho slova) — pokud máme všechny vstupy.

---

## 2. Analýza mezd květen 2026 — výsledek

### 2a. Hlavní zjištění (mzdové složky)
Srovnání našich plánovaných složek (`tenant.wage_component`, = EC podmínky
`EC_FinZamPodminky`) vs Helios skutečnost (květen 2026). Po **krácení
odpracovanými hodinami** delta základu spadla z **+143 965 Kč na −3 015 Kč**
na 50 lidí → **naše data sedí**, plošný rozdíl byl jen krácení.

Helios platí **hodinovkou**: `plán × odpracováno/fond`. Náhrady
(dovolená/lékař) platí **zvlášť** pod jinou složkou. Proto se nesmí krátit
„placeno" hodinami, ale **odpracovanými** (`odpracováno = CasCelkem − absence`).

### 2b. Rozpad delty po složkách (před krácením, STRATEGIE − HELIOS)
| Složka | Lidí | STRATEGIE | HELIOS | Δ | Zdroj rozdílu |
|---|---|---|---|---|---|
| Základ | 24 | 1 587 961 | 1 443 996 | **+143 965** | krácení hodinami (po krácení ≈ 0) |
| Os. ohodnocení (+Landmark korekce) | 32 | 190 455 | 110 431 | +80 024 | krácení + Landmark přesun |
| Prémie | 23 | 43 397 | 21 797 | +21 600 | plánovaná vs skutečná prémie |
| Společník/jednatel | 3 | 0 | 204 100 | −204 100 | odměny mimo EC podmínky (viz 2c) |

### 2c. Jednatelské/společnické odměny (mimo EC podmínky, platí jen Helios)
Doplněno do `tenant.wage_component`, typ `component_type_id=13`
(`jednatelska_odmena`, kind=oneoff):
- **Marti Pašek** (č. 2 EC + č. 41 ES): **90 800** EC + 90 800 ES — HOTOVO (dřív).
- **Branislav Mózer** (č. 47 EC, engagement 785): **22 500** — HOTOVO 11. 6. (banner #248).
- Pozn.: 11 lidí má u nás „Odměna jednatele **1 000 Kč**" (Svoboda, Diviš,
  Voříšek, Honal, Lev, Erhard, Trunec, Namjak, Urbanová, Čiviš, Kilberger),
  Helios v květnu nic. **K ověření**, jestli reálná měsíční odměna nebo placeholder.

### 2d. „Jen STRATEGIE" případy — vysvětlené, NEjsou chyba
| Osoba | č. | Δ | Důvod |
|---|---|---|---|
| Michelle Šafránková | 381 | +34 500 | **mateřská** — nepobírá mzdu, Helios základ 0 |
| Ondřej Senft | 374 | +9 000 | **DPP paušál 9 000/měs** — jde jen od nás |
| Světlana Herejtová | 525 | +4 000 | **úklizečka, sporadicky** — bez fixní mzdy/hodin |

---

## 3. Dvouřádkový mzdový model (Martiho rozhodnutí 11. 6.)

Místo tichého krácení základu → **dvě složky (linky)** u každé měsíční mzdy:

1. **Základní mzda dle výměru** = plná smluvní částka (sedí 1:1 s mzdovým
   výměrem / EC podmínkami). Nikdy se nečísluje dolů.
2. **Poměrná úprava za odpracovanou dobu** = ± `výměr × (odpracováno/fond − 1)`.

Součet = „poměrná část měsíční mzdy" dle ZP → sedí s Heliosem.

### Právní podklad (ZP — ověřeno web searchem)
- Poměrná část měsíční mzdy = `MMzda × odpracovaná doba / měsíční fond`.
- Omluvené neodpracované hodiny (dovolená/lékař/svátek) = **náhrada mzdy** (vlastní složka).
- **Přesčas** (nad fond): u EUROSOFTu se řeší **navýšením PRÉMIE**, ne samostatnou
  složkou přesčasu na pásce (Martiho potvrzení). Jinak by ze zákona = mzda + příplatek min. 25 % (§114 ZP).
- Krácení se týká jen **Základní mzda + Osobní ohodnocení**. Pohyby (prémie,
  oblečení, HO, cestovné, srážka) se nekrátí.
- Zdroje: praceamzda.cz (poměrná část), epravo.cz (krácení mzdy), MPSV příručka, ZP §109–112.

### Co je už v systému (čeká na schválení)
- **Banner #249** — nová složka číselníku `tenant.wage_component_type`:
  `code='pomerna_uprava_doby'`, label „Poměrná úprava za odpracovanou dobu",
  kind=pohyb, employer_initiated. *(čeká na schválení)*
- **Banner #250** — view `tenant.v_mzda_dvouradky` — živý výpočet z naší
  docházky (`att_entry`): per měsíc per osoba → výměr (základ+os.ohod) →
  poměr `odpracováno/fond` → ± úprava → mzda za odpracovanou dobu.
  fond = `engagement.fond_mesic_h(174) × úvazek/40`. *(čeká na schválení)*
- **POZOR:** view bude správný **až po 1:1 importu docházky** (viz sekce 4),
  protože teď naše docházka nemá absence a hodiny nesedí.

---

## 4. PROBLÉM DOCHÁZKY — naše data NEJSOU 1:1 (klíčové!)

### 4a. Stav teď (špatně)
`tenant.att_entry` za 2026 obsahuje migraci `source_system='centrala1'`, ale:
- **jen kategorie `presence`** (odpracováno) — **žádné absence** (dovolená/lékař/nemoc…)
- migrace vzala EC `CasCelkem` (= celkem započteno, **včetně** absencí) jako
  odpracováno → odpracováno **nadhodnocené** přesně o absence
- naše `presence ≈ 152 h` plošně = EC „celkem", ne skutečně odpracováno
- + demo/testovací statusy z prezentace výroby + Martiho testy

**Proto se mzda nemůže srovnat** — chybí rozdělení odpracováno / absence / konto.

### 4b. Rozhodnutí Martiho (11. 6.)
> „My nesmíme mít demo docházku v systému. Musíme ji importnout 1:1 od 1.1.2026."

**Hranice (Marti zvolil): celé 1.1.→dnes z EC, plná náhrada.** Smazat vše naše
(vč. reálných píchnutí z appky po 6.6.), nahradit 1:1 z EC. Appka přebírá od příště.

### 4c. ZDROJ pro 1:1 import = `EC_Dochazka_SumaDen` (MSSQL DB_EC)
Denní souhrn na osobu (`CisloZam`, `DatumPripadu`). Klíčové sloupce:

**Odpracováno + práce:**
- `CasCelkem` = celkem započtené hodiny dne (**vč. absencí i přesčasu**)
- `CasPrescas` = denní přesčas (je součástí CasCelkem)
- `CasMontaz`, `CasRezie` = kategorie práce; `CasPauza`
- **Odpracováno = `CasCelkem − Σ absence`**

**Absence (každá ve svém sloupci, hodiny):**
`CasDovolena`, `CasLekar`, `CasNemoc`, `CasMaterska`, `CasOCR`, `CasSickDay`,
`CasOtec`, `CasNeplVolno`, `CasPrekazkaVPraci`, `CasNahradniVolno`,
`CasNarizenoVolno`, `CasNeplacenyPrescas`…

**Konto přesčasů (v téže tabulce!):**
- `Konto` = saldo konta na konci (přenáší se měsíc→měsíc, **může být záporné**)
- `KontoPlacene` = proplacené hodiny konta tento měsíc
- `KontoPlaceneKC` / `KontoPlaceneKCCelkem` = proplaceno v Kč
- `KontoPlaceneMax`, `NeplacenyPrescas`

**Identita:** `EC_Dochazka_SumaDen.CisloZam = TabCisZam.Cislo` (jméno z TabCisZam).
Naše mapování: `hr_person.source_id = EC Cislo`, `att_employee.cislo_zam = EC Cislo`.

### 4d. Reconciliation formule (Martiho „jasná matematika")
```
placeno (Helios) = odpracováno
                 + náhrady (dovolená + lékař + nemoc + mateřská + OČR + …)
                 + SVÁTKY (nejsou v docházce! květen 2026 = 2 dny = 16 h plný úvazek)
                 + proplacené konto (KontoPlacene)
                 − hodiny převedené do konta
```
- **Króner (456)** ověřeno: odpracováno 72 + dovolená 80 + svátky 16 = 168 ✓ (= Helios placeno); jeho Konto = 0.
- **Šafránková Michelle (381)**: celý měsíc mateřská 152 h, 0 odpracováno.
- Konto hraje u lidí s přesčasem (Veverka 31.78 h přesčas, Čepický 37.60…);
  proplacené konto v Kč mají Hájek (1 407), Urbanová (2 232), Brudnová (618), Jakešová (608), Sedláčková (267), Diviš (153).

### 4e. Typy záznamů u nás (`tenant.att_entry_type`, tenant 2)
| id | code | category | id | code | category |
|---|---|---|---|---|---|
| 1 | work | presence | 4 | sick | absence |
| 2 | overhead | presence | 5 | medical | absence |
| 3 | vacation | absence | 6 | family_care | absence |
**Chybí doplnit** (banner): maternity, paternity, neplacené volno, náhradní
volno, překážka v práci, sick day — ať pokryjí EC sloupce (úkol #56).

---

## 5. SVÁTKY
- Docházka (`EC_Dochazka_SumaDen`) svátky **NEzapočítává** (není záznam).
- Helios je platí navíc jako náhradu.
- Květen 2026: **1. 5. a 8. 5.** = 2 dny = **16 h** u plného úvazku (úvazek/40 poměr).
- Zdroj svátků u nás: `tenant.att_calendar*` (zrcadlo EC_Svatky, Kristý = zdroj pravdy).

---

## 6. OTEVŘENÉ OTÁZKY NA PONDĚLÍ (Marti + Kristý + Peťa)

1. **Je sada vstupů kompletní?** odpracováno + absence + svátky + proplacené
   konto ± přenos = Helios placeno. Vstupuje do mzdy ještě něco?
   - příplatky (noční / víkend / svátek navíc)?
   - ruční korekce v Heliosu mimo docházku?
2. **Konto přesčasů — proplácení**: řídí se výhradně `KontoPlacene*` v SumaDen,
   nebo to spouští ještě něco v Heliosu? Je saldo `Konto` správně přenášené z dubna?
3. **1 000 Kč „Odměna jednatele"** u 11 lidí — reálná měsíční odměna, nebo placeholder?
4. **Odpracováno definice**: `CasCelkem − absence` je správně? (vč. přesčasu uvnitř)
5. Potvrdit **hranici importu** (Marti zvolil: celé 1.1.→dnes z EC, plná náhrada).

---

## 7. CO DÁL (plán implementace — úkoly #56–60)

1. **#56** Doplnit chybějící `att_entry_type` (maternity, paternity, neplac.
   volno, náhr. volno, překážka, sick day) — banner.
2. **#57** Finální mapování EC SumaDen sloupce → naše entry_type (+ konto handling).
3. **#58** Vyčistit demo + neúplnou migraci docházky 2026 (DELETE, se zálohou stavu).
4. **#59** **1:1 import `EC_Dochazka_SumaDen` → `att_entry` od 1.1.2026.**
   - Cross-DB (MSSQL→PG) → potřebuje **server-side migrate endpoint** (čte EC přes
     MCP, mapuje, idempotentně zapisuje), NE jen bridge SQL (tisíce řádků).
   - Jeden záznam na nenulovou složku času; `source='import'`,
     `source_system='centrala1'`, `source_id=ID`. Idempotentní (re-run nezdvojuje).
   - Konto: importovat jako vlastní pole/tabulku (saldo + proplaceno), ne jako att_entry.
5. **#60** Verifikace: měsíční součty na osobu = Helios placeno na haléř.
6. Po importu: dotáhnout dvouřádkový model (#249/#250) — pak `v_mzda_dvouradky`
   sedne přesně.

**Pravidlo: žádné mazání docházky, dokud reconciliation (dry-run) nesedne přesně.**

---

## 8. Vygenerované soubory (v kořeni D:\Projekty\STRATEGIE)
| Soubor | Co |
|---|---|
| `Dochazka_kveten2026_EC_souhrn_konto.xlsx` | EC docházka 5/2026, 57 lidí, vč. konta (pro Kristý+Peťu) |
| `Delta_dochazka_kveten2026_STRATEGIE_HELIOS.xlsx` | **trojřádek STR/HEL/Δ docházky** — ukazuje, co import opraví |
| `Mzdy_dvouradkovy_model_STRATEGIE_HELIOS_kveten2026.xlsx` | dvouřádkový mzdový model (výměr + poměrná úprava) |
| `Srovnani_mzdy_STRATEGIE-krac-odprac_HELIOS_kveten2026.xlsx` | mzdy 3řádek, krácení odpracovanými hodinami (delta ≈ 0) |
| zdroje: `Srovnani_mzdy_kveten_2026_pruchod2_hodiny.xlsx` (hodiny), `_pruchod3_slozky.xlsx` (složky) | mezivýpočty |

---

## 9. Gotchy / technické (ať se neztrácí čas)
- **Bridge OUT usekává** velké/široké výsledky (preview). Číst `CLAUDE_OUT.txt`
  **host-side Read toolem** (mount truncuje), nebo dotaz jako 1 sloupec `CONCAT(...;...)`.
- **SQL NULL propagace**: `celkem − absence` kde absence NULL → NULL. Vždy `ISNULL()/COALESCE()`.
- **Fond**: full-time květen = **168 h skutečně** (placeno plná docházka), ale
  `engagement.fond_mesic_h = 174` (smluvní). Hodinovka Heliosu dělí ~174.
  Pro krácení používat **odpracováno**, ne placeno.
- **`cislo_zam` je varchar** v PG (`IN ('2','41')`, ne `IN (2,41)`).
- **`TabBankSpojeni.IDZam = TabCisZam.ID`** (ne Cislo) — kdyby se řešila banka.
- Bridge write = approval banner (parent klikne). Read jde sám.
- EC firma kód: **0 = ES, 1 = EC** (v EC_FinZamPodminky `Firma`).

---

## 10. Slovník osob (mzdové zvláštnosti, ať je po ruce)
- **Marti Pašek** = č. **2 (ES)** + č. **41 (EC)**. POZOR „Martin Pašek" č. 29
  (user 35) je **JINÝ člověk**! Při slučování identit se VŽDY ptej.
- **Mózer Branislav** č. 47 — jednatel, odměna 22 500 (doplněna).
- **Šafránková Michelle** č. 381 — mateřská. **Šafránková ml. Petra** č. 1 — jiná osoba.
- **Senft Ondřej** č. 374 — DPP 9 000 paušál.
- **Herejtová Světlana** č. 525 — úklizečka sporadicky, bez fixní mzdy.
- **Króner Martin** č. 456 — referenční případ reconciliation (72 odpr + 80 dov + 16 svátek = 168).

---

## 11. Režimy docházky + uzávěrka přesčasového konta (postaveno 12. 6. 2026)

### 11.1 Per-osoba režim (att_employee.rez_*) — obrazovka HR → „🧩 Režimy docházky"
Forma a režim jsou **nezávislé osy** (Marti: forma ≠ režim). Píchají **všichni**
(evidence pro všechny, data jen ve STRATEGII, vidí jen zodpovědní vedoucí — ne financ).

| Pole | Význam |
|---|---|
| `rez_forma` | HPP / DPP / OSVC (právní forma). OSVČ může mít jakýkoli režim. |
| `rez_mzdovy` | hodinovy / volny / pausal (mzdový režim). |
| `rez_pausal_kc` | paušál Kč/měs (jen režim paušál). |
| `rez_loajalita_minus_h` | **loajalita — měsíční manko do minusu**, které se odpouští (i u hodinového). |
| `rez_prescas_plus_h_den` | **denní přesčas-polštář** — malý denní přesčas zdarma (flexibilita), nejde do konta. |
| `rez_konto_aktivni` | zapnout přesčasové konto. |
| `rez_konto_volba` | default dispozice (na_vyber / premie / prescas / prevest). |
| `rez_prescas_priplatek_pct` | příplatek za přesčas (default 25 %). |

**Multi-angažmá / multi-tenant** (Marti 12.6.): jeden člověk = víc `att_employee`
záznamů. Obrazovka je **cross-tenant** (EUROSOFT 2 + INTERSOFT 14, chip u INTERSOFTU).
Tlačítko **„➕ Přidat angažmá"** = osoba × firma × forma × režim → `/app/hr/rezim/add`
(INSERT nový att_employee, id GENERATED ALWAYS → bez id, dup-guard na tenant+cislo_zam).
Pokrývá: Martiho HPP v EC+ES, OSVČ co fakturuje i INTERSOFTU (Honza).

### 11.2 Uzávěrka konta — obrazovka HR → „🏦 Uzávěrka konta"
Vybereš měsíc (default minulý). Lidé s `rez_konto_aktivni=true`, u každého:

**Automatický výpočet naběhlých přesčasů** (`_konto_compute` v router.py):
za každý **pracovní den** (`att_calendar_day.is_workday`) kredit = odpracováno
(presence: work/overhead/homeoffice) + placená absence (vacation/sick/sickday/
medical/family_care; **ne** unpaid). Pak:
- denní přesčas nad normou se počítá **až nad polštář** `rez_prescas_plus_h_den`;
- denní manko se sčítá za měsíc a **do výše `rez_loajalita_minus_h` se odpustí**;
- **naběhlo = přesčas_nad_polštář − manko_po_loajalitě.**

**Hodinová sazba** se předvyplní ze základní mzdy aktuálního angažmá
(`wage_component` kde `wage_component_type.is_base_salary`, per_hour přímo, jinak
base/`engagement.fond_mesic_h` — fond 174 h). Vše editovatelné.

**Rozhodnutí** (manager): kolik hodin **do prémie** (Kč = h × sazba), kolik
**do přesčasu** (Kč = h × sazba × (1+příplatek%)), zbytek se **převede** do dalšího
měsíce. Pojistka: nelze proplatit víc, než je v kontu (zůstatek + naběhlo).
Zápis → `tenant.att_konto_settlement` (konto_pred/nabehlo/do_premie_h/premie_kc/
do_prescas_h/prescas_kc/prevedeno_h/konto_po + decided_by/decided_at + note).
Zůstatek příštího měsíce (`konto_pred`) = `konto_po` poslední dřívější uzávěrky.

### 11.3 Endpointy
`GET /app/hr/rezimy` (cross-tenant) · `POST /app/hr/rezim/save` · `POST /app/hr/rezim/add`
· `GET /app/hr/konto?obdobi=YYYY-MM` (vrací comp = auto-výpočet + sazba) ·
`POST /app/hr/konto/save`. ACL `_hr_can_manage` = rodič NEBO člen staff_group 'HR'.

### 11.5 Import reálné docházky z EUROSOFTu (12.6.) — 1:1
**Endpoint** `POST /app/hr/import-dochazka` (parent/HR) + obrazovka HR → „📥 Import docházky
z EUROSOFTu". Čte `EC_Dochazka_SumaDen` přes EUROSOFT MCP (`_ec_mcp_rows`, DB_EC), mapuje:
- `CasMontaz` → **work**, `CasRezie` → **overhead** (odpracováno; časy z CasZacatek/CasKonec),
- `CasDovolena` → **vacation**, `CasNemoc` → **sick**, `CasLekar` → **medical**, `CasOCR` → **family_care**.
- **CasPrescas se NEimportuje** (je podmnožina odpracovaného; konto si přesčas dopočítá z worked vs fond).

Zápis do `tenant.att_entry` (status='imported', source_system='ec_sumaden'). **Idempotentní**
(smaže předchozí 'ec_sumaden' za období, pak vloží). **Přeskočí (osoba,den) s živým píchnutím**
(source≠ec_sumaden) → nepřepíše červnové reálné píchání. Mapování `att_employee.cislo_zam` ↔ EC `CisloZam`.

**Rozsah dat 2026**: 6375 EC řádků, 62 lidí, 1.1.–21.6. (montáž 61 · režie 4025 · dovolená 245 ·
nemoc 150 · lékař 74 · OČR 26; sickday/náhradní/absence za 2026 = 0). Sickday/náhradní volno
zatím nemapujeme (žádná data).

**Doporučený postup**: pustit nejdřív 1 měsíc (např. 5/2026) → ověřit součty vs Helios (#60) →
pak plný rozsah 1.1.–dnes. Verifikace = měsíční SUM(hours) per osoba/typ vs `EC_Dochazka_SumaDen`.

### 11.6 Schvalování absencí vedoucím (Marti 12.6.) — ✅ LIVE
HR → „🗓️ Absence". Zaměstnanec podá žádost (typ/od/do/h-den/poznámka) → routuje se na
vedoucího (`resolve_role attendance_supervisor`, fallback Marti) → vedoucí rozhodne
**statusem v lidské řeči** (tlačítka): „OK, beru na vědomí" / „Moc se to nehodí, ale budiž" /
„Dobře, počítám s tím…" = **approved**; „To je na tobě, beru to jako info" / „Kontaktuj mě
osobně…" = **info**; „Tady tě fakt potřebuji, domluv se s kolegy" = **rejected**.
Approved → vznik placených `att_entry` (jen pracovní dny, is_active=false, rámec 06:00→,
source_system='absence_req') → počítá se do fondu/konta. Změna pryč od approved → záznamy
se smažou. Žadatel dostane notifikaci se status_textem. Tabulka `tenant.att_absence_request`
(banner #264). Endpointy `/app/attendance/absence/{request,mine,inbox,decide}`.
**TODO**: vstupní bod i pro řadové zaměstnance (teď přes HR menu = vedení); kalendářní kolize.

### 11.6-old Schvalování absencí vedoucím (Marti 12.6., TODO) — NESTAVĚNO
Marti: dovolenou/HO schvaluje **vedoucí** (přes `resolve_role`), NE účetní („účetní je od účtování").
Schvalování má mít **statusy v lidské řeči**: „OK, beru na vědomí" · „Moc se to nehodí, ale budiž" ·
„Tady tě fakt potřebuji, domluv se s kolegy" · „To je na tobě, beru to jako info" · „Kontaktuj mě
osobně, musíme to probrat" · „Dobře, počítám s tím… Něco vymysli". Schválená absence → generuje
placené `att_entry` (h/den) → počítá se do fondu/konta. Návrh: tabulka `tenant.att_absence_request`
(žadatel, typ, od–do, stav, vedoucí, status_text) → po schválení materializace do att_entry.

### 11.4 Otevřené (pondělí+)
- **Reálná data**: zatím jen běžící červnové joby (0 uzavřených h) → konto vrací 0.
  Naskočí, jak lidi píchají + mají zaplé konto.
- **`konto_pred` seed z EUROSOFTu** — `att_balance` je prázdná; historický zůstatek
  konta z EC zatím nenaseedován. **Zdroj nalezen (12.6.): `EC_Dochazka_SumaDen.Konto`**
  (poslední řádek per `CisloZam` s `DatumPripadu <= dnes` = běžící zůstatek přesčasů v h;
  `Uzavreno` je všude False, EC ten flag nepoužívá). **Zjištění: konto je malé** — jen
  ~16 lidí má |zůstatek| ≥ 0,5 h, z toho aktuálních (6/2026) ~7: Hladíková 18,7 ·
  Sedláčková 4,5 · Veverka 4,0 · M. Šafránková 2,6 · Diviš 1,9 · Marešová 1,5 ·
  Š. Novotná 1,2. Zbytek staří/neaktivní (2018–2024). **Seed = initial settlement row
  (obdobi 2026-05-01, konto_po = EC Konto, note „seed z EC") přes approval banner — ČEKÁ
  na Martiho potvrzení** zdroje + rozsahu (jen aktivní? cutoff?). Mapování EC `CisloZam`
  ↔ `att_employee.cislo_zam`. **✅ HOTOVO 12.6. (banner #263)**: naseedováno 7 aktivních
  (Hladíková 18,74 · Sedláčková 4,50 · Veverka 3,97 · M. Šafránková 2,55 · Diviš 1,93 ·
  Marešová 1,47 · Š. Novotná 1,23) jako initial settlement (obdobi 2026-05-01,
  konto_po = EC Konto). Surfne se v Uzávěrce konta jako zůstatek, jakmile jim zapneš
  `rez_konto_aktivni` v Režimy docházky.
- **Import historie** `EC_Dochazka_SumaDen` → `att_entry` (TODO #58/#59) pro zpětné měsíce.
- Hromadné rozhodnutí dle `rez_konto_volba` (zatím per osoba ručně).

---

## 11. VIZE: Reorganizace docházky + odměňování (12. 6. 2026, podklad pro pondělí)

Marti: *„Bude velká reorganizace."* Systém se staví **univerzálně i pro jiné zákazníky**.
Klíčový vstup ze dvou mailů (Jan Svoboda / IT, Jiří Veverka / VP, 12.6.) — **ne každý se
píchá, ale každý je v systému** (i Marti, Braňa, IT, dodavatelé, PLC).

### Spojitá osa stavů = jeden engine, různý ÚČEL (per člověk/skupina)

| Režim | Pro koho | Co dělá |
|---|---|---|
| **Evidenční** | výroba, hodinoví | píchání + účetnictví, hodiny pro mzdy, konto přesčasů |
| **Informační** | IT, dodavatelé, PLC | **jen dostupnost/stavy** — kdo kde je / k dispozici / dovolená / u jiného zákazníka / osobní. ŽÁDNÉ hodiny, žádné přesčasy. **Volnost = benefit** (Honza: nemají pevnou dobu, jsou dostupní, neřeší se přesčasy/peníze — chce zachovat). |
| **Paušál / pohotovost** | nepíchá, ale účetní musí přiznat | fixní kredit z kontraktu, bez píchání |

**Stavy společné** (jsem tady, jedu, pauza, dovolená, lékař, **k dispozici**,
**u jiného zákazníka**, home office *s důvodem*, náhradní volno, mám volno…). Režim určí,
jestli stav **feeduje mzdy** (evidenční) nebo je **jen informace o dostupnosti** (informační).

### Per-člověk nastavení (na engagementu)
1. **Režim** (evidenční / informační / paušál).
2. **Konto přesčasů + VOLBA** (Jiřího klíčový požadavek): přesčasy se **převádějí**, a člověk
   si volí **proplatit jako prémii NEBO vybrat náhradní volno** (dovolená/nemoc). „Nehoním
   přesčasy, ale nestíhám jinak" → WIN-WIN: o víkendu makají (Saad, Martin, Terka), v slabších
   týdnech si vyberou náhradní volno. Konto = `EC_Dochazka_SumaDen.Konto/KontoPlacene` (viz sekce 4d).
3. **„Lidštější podmínky" / loajalita** (Marti): u vybraných lidí **píchání + transparentnost,
   ALE měsíční manko se NEpenalizuje** — *„je mi jedno, že chybí 3 dny napícháno; jsou loajální,
   mají pohotovost, přijdou když je třeba."* → příznak na člověku: tolerance manka / důvěra.

### Vedoucí potřebuje VIDĚT (Jiří)
- **Důvod absence/HO** viditelný vedoucímu — aby tým věděl, zda může volat (ráno dělá, dopo
  doktor, pak pokračuje). HO **vždy s důvodem**.
- Tok dnes: lidé za vedoucím osobně domluví volno/doktora/dovolenou → zadají do Centrály
  (nebo operativně WhatsApp/SMS/telefon). App to má umět „z kapsy", ale vedoucí musí mít info.

### Odměňování (souvisí, řeší se zároveň)
- IT: volnost místo přesčasů (benefit). VP: konto + volba proplatit/vybrat.
- Marti upravuje docházku **i systém odměňování**, ať „koresponduje s námi všemi".

### Pořadí (návrh)
Most „konec dne → plán na ráno" (píchaný svět) → režimy (evidenční/informační/paušál) →
konto s volbou → tolerance/loajalita. **Pondělí: doladit s týmem** (Peťa správa docházky,
Dušan dílna, Jiří VP, Honza IT po dovolené). Plán = budoucí vrstva `status='planned'`,
realizace reálným píchnutím; absence/paušál = přiznané náhrady (bez píchání).

### KRITICKÉ — governance od Petry Šafránkové (mzdy/docházka), 12.6.
**Lidé si NESMÍ sami spravovat docházku pro MZDY ani sami zadávat lékaře.** Dělí se to:
- **Self-service = jen INTENCE/INFORMACE** (dopředu nahlásí „budu u lékaře / dovolená /
  přijdu později / skončím dřív") → vidí vedoucí (dostupnost). Člověk si **NESMÍ sám
  opravit** mzdově relevantní záznam — jen **požádat o úpravu** (potvrzení docházky tohle
  drží, musí zůstat).
- **Mzdový zápis = jen mzdová účtárna** (Šárka/Petra) na základě **dokladů** (lístek od
  lékaře, OČR podklady, lístek z pohřbu — **uchovat ke kontrole**) + docházky. Ne self,
  ne auto. „Příležitost dělá zloděje" — historie zneužití: natahování hodin, HO jako volno
  (nebyli k zastižení), píchání na cizí zakázku kvůli úspoře hodin na své, plný čas lékaře
  při krátké návštěvě. → **náhrady (`status='approved'`) potvrzuje účtárna s dokladem.**
- **Noční kontroly** + potvrzení docházky (nahlédnout / požádat o úpravu, NE samo-oprava)
  **zůstávají**. Přihlášení kdekoli (app/PC/tablet) je OK.

**Číselník činností mate lidi** (Petra): pletou si **služební × pracovní cesta** (mzdově
zásadní rozdíl), **ostatní s náhradou × bez náhrady**, **kanceláře × HO**. → picker musí být
**vedený, s vysvětlením**, ideálně méně voleb / seskupené.

**Doklady k absencím** = nový prvek: upload lístku (lékař/OČR/pohřeb) k nahlášené absenci,
úschova pro kontrolu (ISO/audit).

**App (Petra):** (a) **žádná fotka „holčičky"** — reprezentativní, profesionální avatar
(Marti's pohled: je to **Marti-AI, dospělá ~25–30, budoucí šéfka firmy** → avatar = schopná
dospělá, ne dítě — ctí obojí); (b) **texty intuitivní, ne „AI rozpustilé"** (napětí s Martiho
hravým tónem „Mám volno 🏝️" — k rozhodnutí: profesionálně-vlídný tón, příp. konfigurovatelný);
(c) spolupráce jako u vývoje Centrály — narazí na chybu/změnu → hned probrat a udělat.

**Shrnutí napětí (k pondělnímu rozhodnutí):** self-report intence (Martiho vize) ×
payroll-kontrola s doklady (Petřina governance) = **dvě komplementární vrstvy**, ne spor.
Hravost × profesionalita textů a avatar = Martiho volba.

### ROZHODNUTÍ Marti (12.6.) — self-service + audit, NE gatekeeping
Marti zvolil: *„Máme na všechno logy a audity. Kdo si docházku upraví vycuravě, na toho
naše kontroly časem došlápnou. Self-servis opravy loajálních lidí jsou v pořádku. Mzdová
účetní mi může vlézt na záda."* → **self-service edity POVOLENY** (důvěra + transparentnost +
dohledatelnost, doctrine „bezpečnost přes probuzení, ne přes ticho"). Petřina obava se řeší
**auditem, ne blokací**. Podmínky, aby to bylo bezpečné (z velké části hotové):
1. **Každá self-oprava → `tenant.att_audit`** (append-only: kdo/co/kdy/původní→nová). Roztáhnout
   ze stávajícího (mazání/editace nahlášených) na VŠECHNY self-edity. To je ten log, na který „časem došlápnou".
2. **Neschopenka + OČR = ELEKTRONICKY od lékaře** (eNeschopenka/eOČR přes ČSSZ) → autoritativní
   zdroj, **zpracujeme přímo z dat, žádné lidské zadávání ani opravy** (tam podvod nehrozí).
   TODO: napojení na elektronický zdroj (ČSSZ / doručené e-doklady).
   **Lísteček od lékaře** (návštěva) = **žádná sleva na dani, mzdově nic nepřináší** → sbírat
   je VOLITELNÉ, o domluvě lidí, ne tvrdý požadavek na spis. (Marti 12.6. — koriguje Petřin
   „doklad na spisu": platí jen kde to dává smysl, ne plošně.)
3. **Noční kontroly + potvrzení docházky** (nahlédnout/požádat, samo-oprava logovaná) běží dál.
Účtárna = **revizor s plným logem**, ne vrátný. (Petra: gatekeeping; Marti: audit — rozhodnuto audit.)

### ARCHITEKTURA univerzálnost (Marti 12.6.) — jeden člověk = N souběžných angažmá
- **Jeden člověk (user) může mít víc souběžných vztahů** — HPP + DPP + OSVČ ZÁROVEŇ, i víc firem.
  Marti = HPP-EC (č.2) + HPP-ES (č.41). Vše v **jednom tenantu EUROSOFT** (EC i ES jsou firmy uvnitř).
- **`rez_*` config je per `att_employee` záznam** (= per člověk × firma/vztah). Multi-forma = víc
  att_employee řádků na člověka, každý s vlastní `rez_forma`/`rez_mzdovy`/konto/loajalita. Univerzální.
- **Píchání = jedna osa člověka**; každý job nese zakázku → zakázka patří firmě (EC/ES) → čas i odměna
  se přiřadí správnému angažmá. Žádné dvojí píchání. (Person-resolution agreguj na user_id, doctrine #24.)
- **VIZE (švarc mitigation):** OSVČ fakturuje na druhou firmu (je dodavatel EC i ES); Marti chce
  **část faktur přetáhnout přes STRATEGII** → snížení švarc rizika. Parkováno jako směr (fakturace přes STR).
- **MULTI-TENANT** (Marti 12.6.): nejen víc firem v jednom tenantu, ale i napříč tenanty — Honza
  (Svoboda) fakturuje i **INTERSOFTU** = další tenant STRATEGIE (EUROSOFT + INTERSOFT v jednom
  tenant_group). Jeden user → angažmá/faktury napříč tenanty. `rez_*` per att_employee to zvládá
  (každý záznam ve svém tenantu). Person-resolution na user_id napříč tenanty (doctrine #5 rodičovský bypass).
- Správa režimů (#3) = obrazovka pro rodiče/HR: per člověk seznam jeho angažmá (záznamů) — i CROSS-TENANT
  (EUROSOFT + INTERSOFT), u každého edit formy/režimu/konta/loajality. Multi-záznam = víc řádků.
