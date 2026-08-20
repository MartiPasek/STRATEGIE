# Přefakturace ES → EC: změna pravidla pro IT — návrh k odsouhlasení

**Připravil:** Claude‑24 (Kristý) · **Datum:** 20. 8. 2026
**Zadala:** Kristý · **K aktivaci potřebuje:** společné review s Martim (mzdy + reálné peníze)
**Stav:** NÁVRH — nic z toho zatím není nasazeno, v Centrále ani v kódu.
**Varianta:** osobní čísla **napevno** (Kristý 20. 8.: varianta s novou skupinou v Centrále zamítnuta).

---

## 1. Pravidlo

**Dnes:** každý člověk ve skupině **IT** (`EC_Skupiny.ID = 5`) se přefakturuje **polovinou** nákladu, druhou platí IAP. Zavedla Kristý 18. 3. 2026.

**Nově, platné od období 7/2026:**

| Kdo | Přefakturuje se |
|---|---|
| Kristý — osobní čísla **21** a **27** | **100 %** |
| Jiří Honomichl — osobní číslo **9030** | **100 %** |
| kdokoli další ve skupině IT (349 Šik, 9000 Klik, 9017 Svoboda, 9103 Pillár, 11003 „IT IT") | **0 %** — nefakturuje se vůbec |
| všichni mimo skupinu IT | beze změny (100 %) |

Marže 6 % (nájem bez marže) se nemění.

> ⚠️ **Vědomý důsledek, který si Kristý odsouhlasila 20. 8.:** 9017 Svoboda Jan je formálně v IT, ale jeho náklad se na faktuře účtuje jako **„Správní výdaje – vedení"**. Pravidlem „0 %" vypadne **celý**, včetně té vedoucí části. Za 7/2026 to nic nedělá (nemá ES mzdu ani fakturu), ale v jiném měsíci ano. Je to tiché, ne neškodné.

---

## 2. Dopad na fakturu za 7/2026 (spočítáno z ostrých dat)

Celé IT je v červencové faktuře jen ve dvou položkách:

| | dnes (½) | nově (celé) |
|---|---|---|
| 21 Marešová Kristýna — mzdový list | 34 494 | 68 988 |
| 9030 Honomichl Jiří — přijatá faktura | 87 580 | 175 160 |
| **IT základ** | **122 074** | **244 148** |
| IT s marží 6 % | 129 398,44 | 258 796,88 |

| Faktura celkem | základ s marží | DPH 21 % | celkem |
|---|---|---|---|
| dnes | 2 699 097,61 | 566 810,50 | **3 265 908,11 Kč** |
| po změně | 2 828 496,05 | 593 984,17 | **3 422 480,22 Kč** |
| rozdíl | +129 398,44 | +27 173,67 | **+156 572,11 Kč** |

Ověření vstupů: Excel rozpad při marži 6 % dá základ 2 699 097,61; rozpad v appce při marži 5 % dal 2 676 134,43. Přepočet mezi nimi (vše kromě nájmu ×1,05 → ×1,06) sedí na haléř, takže obě čísla jsou konzistentní.

---

## 3. Nosič pravidla: tři osobní čísla napevno

Seznam **`(21, 27, 9030)`** se zapíše přímo do procedury a do Pythonu. Žádná nová skupina, žádná změna číselníků v Centrále.

**Co tím odpadá:** nemusí se sahat na sedm vylučovacích seznamů skupin v proceduře ani na dva v Pythonu — nevzniká nová skupina, která by mohla prosáknout do textu „Skupina" a změnit popisy řádků faktury. Změna je tím pádem menší a míň riskantní než varianta se skupinou.

**Co tím vzniká:** ta tři čísla budou žít **na dvou místech** (procedura v Centrále + náš Python) a mohou se rozejít. Proto:

- v obou místech **stejný komentář** s datem a autorem změny, ať je při příštím čtení jasné, že jsou to spojité nádoby;
- **každá budoucí změna složení** (přibude/ubude člověk) = zásah do procedury i do kódu, přes schvalování — není to klik v Centrále;
- do ověřovacího seznamu (kap. 7) patří kontrola, že obě místa mají stejnou trojici.

---

## 4. Změny v proceduře `EC_GenVFESzFaaDeniku_Priprava` (DB_EC)

Procedura má 30 315 znaků a odkaz na `IDSkupiny = 5` v ní je **10×** (z toho 2× v zakomentovaných řádcích). Aktivních větví, kterých se změna týká, jsou **čtyři** — dvakrát tentýž pár (blok pro měsíc a blok pro kvartál):

| Řádek | Větev | Dnes | Nově |
|---|---|---|---|
| 71, 201 | deník, **ne‑IT** | `CisloZam not in (… IDSkupiny = 5)` | **beze změny** |
| 94, 226 | přijaté faktury, **ne‑IT** | `Cislo not in (… IDSkupiny = 5)` | **beze změny** |
| 112, 244 | deník, **IT** | `CisloZam in (… IDSkupiny = 5)`, částka `/2` | `CisloZam in (21, 27, 9030)`, **bez `/2`** |
| 135, 267 | přijaté faktury, **IT** | `Cislo in (… IDSkupiny = 5)`, částka `/2` | `Cislo in (21, 27, 9030)`, **bez `/2`** |

Ne‑IT větve zůstávají na `IDSkupiny = 5` schválně: kdo je ve skupině IT a není v trojici, **nespadne ani do jedné větve** → z faktury vypadne úplně. Přesně to je požadované chování.

Konkrétně u obou IT větví zmizí dělení dvěma i v části s marží:

```sql
-- DNES (deníková IT větev)
((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2)
  + isnull(@NajemneOsMes,0)
  + (((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2)/100)*isnull(@ProcentMarze,0)))
…
and D.CisloZam in (SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)

-- NOVĚ
(sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)
  + isnull(@NajemneOsMes,0)
  + ((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/100)*isnull(@ProcentMarze,0)))
…
-- Kristýna 20.8.2026: IT se už nefakturuje půlkou; fakturuje se CELÁ Kristýna (21, 27)
-- a CELÝ Honomichl (9030), zbytek IT vůbec. Stejná trojice je i v Pythonu
-- (_pref_mzdy_praha_lines) — při změně opravit OBĚ místa.
and D.CisloZam in (21, 27, 9030)
```

```sql
-- DNES (fakturová IT větev)
(TabDokladyZbozi.SumaKcBezDPH/2) + … + (((…/2)/100)*@ProcentMarze)
… and Z.Cislo in (SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)

-- NOVĚ
TabDokladyZbozi.SumaKcBezDPH + … + ((…/100)*@ProcentMarze)
… and Z.Cislo in (21, 27, 9030)
```

Komentáře „nepočítat IT, fakturuje se polovinou částky" je potřeba přepsat, ať nelžou.

**Kontrola okolí:** `IDSkupiny = 5` je i v procedurách `EC_Skupiny_OdebratZamZSkupiny`, `EC_Notifikace_odesli`, `EC_KontrolaSkupinovychUkolu`, `EC_KontrolaDochSkupIT` — ty s přefakturací nesouvisejí (notifikace, úkoly, kontrola docházky) a **nesaháme na ně**.

---

## 5. Změny v našem kódu (mzdová část z Prahy)

### `_pref_mzdy_praha_lines()` — mzdy do faktury

```python
# Kristýna 20.8.2026: IT se nefakturuje půlkou. Fakturuje se celá Kristýna (21, 27)
# a celý Honomichl (9030); ostatní z IT (IDSkupiny=5) do přefakturace nejdou vůbec.
# TÁŽ trojice je natvrdo i v proceduře EC_GenVFESzFaaDeniku_Priprava — měnit OBĚ místa.
_PREF_IT_CELE = (21, 27, 9030)
```

```sql
-- DNES
CASE WHEN EXISTS(SELECT 1 FROM EC_SkupinyVazby WHERE CisloZam=q.zam AND IDSkupiny=5) THEN 1 ELSE 0 END AS isIT
…
ln AS (SELECT <popis> AS popis, (CASE WHEN isIT=1 THEN nak/2.0 ELSE nak END) * <marže> AS castka FROM emp)

-- NOVĚ: žádné dělení, jen vyřazení lidí z IT mimo trojici
ln AS (SELECT <popis> AS popis, nak * <marže> AS castka FROM emp
       WHERE isIT = 0 OR zam IN (21, 27, 9030))
```

Sloupec `isIT` zůstává (jen se přejmenuje komentář) — pořád je potřeba k rozhodnutí, koho vyřadit.

### `_pref_skup_popis()` + list „Detail po zaměstnancích" v Excelu

- `base = nak / 2.0 if isit else nak` → `base = nak`
- řádky lidí z IT mimo trojici do detailu vůbec nedávat (jinak Excel ≠ faktura)
- štítky `"Mzdový list – IT ½"` a `"Přijatá faktura – IT ½"` → bez „– IT ½"

`prefakturace_rozpad` i `prefakturace_vystavit` volají `_pref_mzdy_praha_lines`, takže se srovnají samy — **rozpad, Excel i vystavená faktura zůstanou konzistentní**.

---

## 6. Postup nasazení

| # | Krok | Kdo | Poznámka |
|---|---|---|---|
| 1 | Uložit stávající definici procedury do souboru (rollback) | C24 | `OBJECT_DEFINITION` přes most |
| 2 | Migrovat `_pref_*` helpery do **`g2007.python`** jako `stav_zivota='navrzeno'` | C24 | pravidlo „kód jako data" z 1.–2. 8. |
| 3 | `ALTER PROCEDURE EC_GenVFESzFaaDeniku_Priprava` | C24 přes most (schvalovací banner) | jeden skript, celá definice |
| 4 | **Aktivace `g2007.python` na `active`** | **Kristý + Marti společně** | mzdy → jedna instance sama nesmí |
| 5 | Ověření (níže) | C24 + Kristý | |
| 6 | Vystavit fakturu za 7/2026 | Kristý | banner pošlu přes most, ať chodí Tobě |

---

## 7. Ověření — co musí sedět, než se vystaví

1. **Rozpad za 7/2026, marže 6 %** → základ s marží **2 828 496,05**, s DPH **3 422 480,22**; řádek IT **244 148 / 258 796,88**.
2. **Regresní kontrola na uzavřeném měsíci:** rozpad za **6/2026** porovnat s už vystavenou fakturou **726008**. Jediný povolený rozdíl je IT část — když se pohne cokoli jiného, změna má vedlejší účinek a jde zpět.
3. Excel „Detail po zaměstnancích" nesmí obsahovat nikoho ze skupiny 5 mimo 21, 27, 9030 a nikde už nesmí být štítek „IT ½".
4. **Trojice `(21, 27, 9030)` je shodná v proceduře i v Pythonu** — přečíst obě místa a porovnat.
5. Popisy řádků faktury se nezměnily.

**Rollback:** vrátit uloženou definici procedury (krok 1) + vrátit původní verzi funkcí. Data se nemění, jde jen o výpočet — nic se nedopočítává zpětně.

---

## 8. Otevřené body pro Martiho

1. **Souhlas s aktivací** kroku 4 (mzdová logika v `g2007.python` na produkci).
2. **Je „0 % pro zbytek IT" opravdu záměr i do budoucna?** Za 7/2026 to nic nedělá, ale jakmile bude mít Svoboda (nebo kdokoli další z IT) ES mzdu či fakturu, jeho náklad z faktury tiše zmizí — u Svobody včetně části „vedení".
3. **Dva IT řádky na faktuře.** Mzdová část má popis „Správa a údržba **IS** a IT podpora uživatelů", dokladová „Správa a údržba **informačního systému** a IT podpora uživatelů" → na faktuře jsou dva řádky místo jednoho (v Excelu se slijí, protože ten si popis počítá po svém). Sjednotit texty, když už v tom kódu budeme?
4. **Sazba IAP.** Změnou přestává EUROSOFT-Control platit půlku IT — má se to někde promítnout na druhé straně (smlouva/objednávka s IAP)?

---

### Podklady

- Rozpad a čísla: `Rozpad_prefakturace_ES_7-2026 (1).xlsx` (list „Detail po zaměstnancích")
- Členové skupiny IT k 20. 8. 2026: 21 Marešová Kristýna, 27 Marešová 2 Kristýna, 349 Šik Michal, 9000 Klik Michal, 9017 Svoboda Jan, 9030 Honomichl Jiří, 9103 Pillár Ondřej, 11003 „IT IT"
- Původní pravidlo: komentář v proceduře „Kristýna 18.3.2026 – IT udělat zvlášť, přefakturujeme jen polovinu nákladů, druhou polovinu platí IAP"
