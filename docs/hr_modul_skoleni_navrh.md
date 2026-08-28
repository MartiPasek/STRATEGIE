# Návrh modulu „Školení zaměstnanců" (HR)

> Podklad k odsouhlasení, **než sáhneme do DB**. Zpracoval Claude‑25 (Šárka), 24. 7. 2026.
> Zdroje: `apps/api/static/karta_zamestnance.html` (dlaždice 🎓), `modules/erp/api/bozp_cockpit.py`
> (periodické povinnosti + doklady BOZP/PO), `hr.md`, `HR_sablony/`. Nic v produkci se tímto nemění.

---

## 1. Proč to řešíme a co dnes chybí

Na kartě zaměstnance je „Školení" naplánovaná sekce, ale **není postavená**
(dlaždice 🎓 „Absolvovaná + plánovaná (BOZP/PO)", `on:false`). V HR menu i na pultu
čeká notifikace **„propadající školení"** ve stavu *soon*. Zároveň už existuje
firemní vrstva: `bozp_cockpit.py` řídí **periodické povinnosti** (revize/kontroly/
školení/prohlídky s termíny a upomínkami) na úrovni firmy a v RO zóně žijí doklady
a šablony (Školení BOZP v4, Doklad o školení administrativa/projekce v4, Doklad
o školení elektromontér/zámečník v4, testy znalostí).

**Co chybí:** *per‑zaměstnanec* evidence — kdo má které školení absolvované, do kdy
platí, co je naplánované a co propadá. Dnes to nikde v systému strukturovaně není;
propadání školení se tím pádem nedá hlídat ani notifikovat.

Cíl modulu: u každého člověka vidět jeho školení (absolvovaná + plánovaná), automaticky
počítat platnost podle periodicity, barevně hlásit „brzy propadá / propadlé" a živit
tím notifikace. Firemní pohled = matice „kdo má co" pro audit (ISO/TISAX, kontroly).

---

## 2. Typy školení, které chceme pokrýt (návrh číselníku)

Rozdělení podle kategorie — každá má jinou periodicitu a jiný doklad. Periodicita je
orientační dle běžné praxe; **finální hodnoty potvrdí Míša/Marti** (viz otevřené otázky).

| Kategorie | Příklad | Periodicita (typicky) | Doklad |
|---|---|---|---|
| **BOZP** | Školení BOZP — administrativa/projekce; elektromontér/zámečník | vstupní + periodické (často 2 roky, dle profese/rizika) | Doklad o školení + test znalostí (šablony v RO) |
| **PO** (požární ochrana) | Školení PO, preventivní požární hlídka | dle začlenění, často 1–2 roky | Doklad o školení PO |
| **Odborná způsobilost elektro** | §6/§7/§8 (dříव „vyhláška 50") | periodicky (běžně 3 roky) | Osvědčení / protokol |
| **Řidiči (referentská)** | Školení řidičů referentů | často 1–2 roky | Doklad o školení |
| **Interní / seznámení** | Seznámení se směrnicemi, BOZP na pracovišti | dle změny předpisu / jednorázově | Podpisový arch |
| **E‑learning / kurzy** | online kurzy, skóre | dle kurzu | výstup z e‑learningu (skóre) |
| **Odborné / kvalifikace** | svářečský průkaz, VZV, jeřáb, lešení… | dle průkazu | průkaz / certifikát |

Pozn.: **Lékařské prohlídky** už mají na kartě vlastní sekci (🩺 „Lékařské prohlídky") —
do školení je netaháme, jen se na ně vizuálně navážeme (stejná logika platnosti/propadání).

---

## 3. Datový model (návrh — konvence `tenant.*`, multi‑tenant)

Dvě tabulky: **číselník typů** + **záznamy osob**. Drží se stylu `bozp_*` a HR tabulek
(tenant 2 = EUROSOFT, 14 = INTERSOFT; vazba na osobu přes `att_employee`/`hr_person`).

### 3.1 `tenant.hr_skoleni_typ` — číselník typů školení

| Sloupec | Typ | Význam |
|---|---|---|
| `id` | PK (GENERATED ALWAYS) | — |
| `tenant_id` | int | firma/tenant |
| `kod` | varchar | strojový kód (`bozp_admin`, `bozp_elektro`, `po`, `elektro_par6`, `ridici_ref`…) |
| `nazev` | varchar | název pro člověka |
| `kategorie` | varchar | `bozp` / `po` / `odborna_zpusobilost` / `ridici` / `interni` / `elearning` / `kvalifikace` |
| `periodicita_mesice` | int NULL | interval opakování; NULL = jednorázové/bez expirace |
| `povinne` | bool | povinné vs. volitelné |
| `pro_skupiny` | jsonb/ref NULL | pro které profese/skupiny platí (napojení na „Skupiny a kvalifikace") |
| `doklad_sablona` | varchar NULL | odkaz na šablonu dokladu v `HR_sablony`/RO |
| `bozp_povinnost_id` | int NULL | volitelná vazba na firemní `bozp_povinnost` (BOZP/PO) |
| `aktivni` | bool | — |

### 3.2 `tenant.hr_skoleni` — záznam školení osoby

| Sloupec | Typ | Význam |
|---|---|---|
| `id` | PK (GENERATED ALWAYS) | — |
| `tenant_id` | int | firma/tenant |
| `att_employee_id` | int | angažmá osoby (per člověk × firma — kvůli multi‑angažmá dle hr.md §11) |
| `typ_id` | int → `hr_skoleni_typ` | druh školení |
| `stav` | varchar | `planned` / `completed` / `expired` / `waived` (odpuštěno) |
| `datum_absolvovani` | date NULL | kdy absolvováno (u `completed`) |
| `platnost_do` | date NULL | konec platnosti = `datum_absolvovani + periodicita` (dopočítané, editovatelné) |
| `planovano_na` | date NULL | plánovaný termín (u `planned`) |
| `skolitel` | varchar NULL | kdo školil / dodavatel |
| `doklad_file` | varchar NULL | odkaz na sken dokladu ve spisu (RO zóna) |
| `poznamka` | text NULL | — |
| `created_by` / `created_at` | — | audit vzniku |
| `updated_by` / `updated_at` | — | audit změny |

**Odvozený stav pro UI** (nepočítá se do tabulky, počítá endpoint):
`platné` (platnost_do v budoucnu, > práh), `brzy propadá` (do X dní — návrh 30/60 dní
podle kategorie), `propadlé` (platnost_do < dnes), `naplánováno`, `chybí` (povinné, ale
žádný záznam).

**Audit:** každá editace do `tenant.att_audit` (append‑only), stejně jako u docházky
(doctrine „bezpečnost přes audit, ne přes blokaci", hr.md §11 rozhodnutí Marti 12.6.).

---

## 4. Obrazovka na kartě zaměstnance (sekce 🎓 „Školení")

Zapadá do stávajícího rozvržení karty (`SEKCE[]` v `karta_zamestnance.html`), přepneme
dlaždici na `on:true` s `key:'skoleni'`.

**Layout sekce:**
- **Přehledový řádek nahoře:** počty — platné / brzy propadá / propadlé / chybí povinné.
  Barevné čipy (zelená/oranžová/červená/šedá).
- **Seznam školení osoby:** řádek = typ • datum absolvování • platí do • stav (barevný čip)
  • doklad (ikona, pokud je). Řazení: propadlé/brzy propadá nahoru.
- **Akce:** „➕ Přidat školení" (typ z číselníku → datum → platnost dopočítá) •
  „📅 Naplánovat" (termín do budoucna) • u řádku „doložit doklad" (upload do spisu).
- **Povinná, ale chybějící** školení (dle profese/skupiny) se ukážou jako „chybí" —
  aby bylo vidět, co člověku ještě schází.

**Firemní pohled (HR menu):** matice „Školení — přehled" = lidé × typy, barevně platné/
propadlé; filtr profese/tým. To je audit‑ready výstup (ISO/TISAX). Napojení: stejná data,
jen agregace přes lidi.

---

## 5. Napojení na zbytek systému

- **Notifikace „propadající školení"** (dnes *soon*) → živí se z `platnost_do`
  (práh dle kategorie). Odemkne hlášku na HR pultu i v „Notifikacích".
- **BOZP/PO firemní povinnosti** (`bozp_povinnost`) → volitelná vazba `bozp_povinnost_id`
  v číselníku, ať firemní termín a osobní školení sedí (jedna pravda o periodicitě).
- **Doklady/šablony** (`HR_sablony`, RO zóna) → z typu školení se dá vygenerovat
  prezenční listina / doklad o školení (administrativa vs. elektromontér mají svou v4)
  a certifikát. Sken se zaváže na `doklad_file`.
- **Skupiny a kvalifikace** (sekce 👥 na kartě) → `pro_skupiny` určí, komu je školení
  povinné, takže „chybí povinné" se počítá automaticky podle zařazení člověka.
- **Multi‑angažmá** (hr.md §11) → záznam je per `att_employee`, takže OSVČ/HPP a víc firem
  má školení správně přiřazené.

---

## 6. ACL a zápisy

- **Číst / editovat:** `_hr_can_manage` = rodič **nebo** člen staff_group „HR"
  (stejně jako Režimy docházky a Uzávěrka konta).
- **Zápisy do produkce** přes schvalovací banner (nová tabulka = banner, jako `bozp_*`
  přes #891). Konstrukce tabulek a číselníku = jeden banner; běžné zápisy záznamů školení
  pak jedou přes HR obrazovku pod ACL.

---

## 7. Otevřené otázky (než začnu stavět)

1. **Periodicity a povinné typy** — které typy školení nasadit do číselníku a s jakou
   periodicitou? BOZP/PO a elektro §6–8 potvrdí **Míša** (vlastní BOZP/PO agendu). Návrh
   v tabulce §2 je orientační.
2. **Zdroj počátečních dat** — máme existující papírovou/EC evidenci absolvovaných školení
   k naimportování, nebo začínáme „od teď" a historii doplní HR ručně?
3. **Práh „brzy propadá"** — jednotný (např. 30 dní) nebo per kategorie (BOZP 60, elektro 90…)?
4. **Kdo zapisuje** — HR (Šárka/Petra) na základě dokladu, nebo i vedoucí u svého týmu?
5. **E‑learning** — je teď reálný zdroj (kurzy + skóre), nebo to necháme jako připravené pole
   na později (dlaždice 🖥️ „E‑learning" je taky `on:false`)?
6. **Rozsah teď** — postavit celé (karta + matice + notifikace), nebo fázovat:
   (a) datový model + karta → (b) matice/audit → (c) notifikace + generování dokladů?

---

## 8. Doporučené pořadí realizace (návrh)

1. **Banner:** `hr_skoleni_typ` + `hr_skoleni` + seed pár základních typů (BOZP admin,
   BOZP elektro, PO, elektro §6–8, řidiči).
2. **Endpointy** `GET/POST /app/hr/skoleni…` (per osoba) pod `_hr_can_manage`, výpočet stavů.
3. **Karta:** zapnout dlaczku 🎓, sekce se seznamem + akcemi.
4. **Matice** v HR menu (audit pohled).
5. **Notifikace** propadajících školení (odemknout *soon*).
6. **Doklady** — generování prezenček/dokladů ze šablon + úschova skenu do spisu.
7. **G2007** — zapsat znalost o modulu (oblast `bozp-po`/`osoba`) na konci.

---

*Až tohle odsouhlasíš (nebo upravíš otevřené otázky v §7), přepnu z návrhu na stavbu:
banner na tabulky → endpointy → obrazovka. Nic z výše uvedeného zatím není v produkci.*
