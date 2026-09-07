# Mzdová karta v Heliosu (úvazek + kalendář) se do Prahy nepřenášela vůbec — Centrála psala do mrtvé větve

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo (7. 9. 2026, Peťa + Claude-26)

Andrea Bernardová (EC 475) má od 1. 8. 2026 v Podmínkách úvazek **40 h/týden**, ale
v Heliosu jí zůstalo **32 h** (kalendář 013). Základní mzda se proto počítala z fondu
134,40 h místo 168 h. Za srpen rozdíl **5 615 Kč**.

**Nebyla to její výjimka — byl to chybějící kus přenosu.** Byla jen prvním člověkem,
kterému se od přestěhování mezd změnil úvazek, takže se to na ní poprvé projevilo v penězích.

## Příčina

Mzdové údaje zaměstnance (úvazek, kalendář, druh PP, zkušební doba, datum vzniku
a ukončení PP) do Heliosu posílala **Centrála** procedurou `EC_ContrMzdyPrenesDoMezd`
(volá ji `EC_Mzdy_PrepocetMesicZam`). Ta ale zapisuje do **plzeňského** Heliosu
(`DB_EC` / `DB_IS`), zatímco mzdy se od přestěhování počítají v **pražském cloudu**
(`UCTO_EC` / `UCTO_ES`).

Důkaz: plzeňská `DB_EC.TabMzSloz` nemá za 8/2026 **ani jednu** mzdovou složku.

STRATEGIE ten přenos nikdy nepřevzala — `mzdy_generuj` posílá **pouze mzdové složky**
(předzpracování) a do `TabZamMzd` nesahá vůbec. Takže úvazek do Heliosu neposílal nikdo.

## Kde ty údaje v Heliosu žijí

| co | kde |
|---|---|
| mzdové údaje **per období** | `TabZamMzd` (řádek na každé mzdové období; to je ta obrazovka „Mzdové údaje") |
| osobní kalendář **per rok** | `TabMzKalendarZam` + `TabMzKalendarDnyZam` (365 dnů) |
| číselník kalendářů | `TabMzKalendar` |
| období | `TabMzdObd` (IdObdobi 152 = 8/2026, `Uzavreno` 3 = uzavřené) |

## ⚠ Změna karty SAMA NESTAČÍ

Když se v `TabZamMzd` změní `DruhKalendare`, ale chybí **osobní kalendář** na ten rok,
`hp_VypocitejMzdu` spadne na **`55071 | Není zadán osobní kalendář zaměstnance`**
a **tiše se odrolluje** — mzda prostě nevznikne a ve výsledku generování je jen
`uvazlo: true`. Worker tu chybu polyká v `TRY/CATCH`.

Osobní kalendář se zakládá **heliosovskou procedurou**:

```sql
DECLARE @R BIT;
EXEC UCTO_EC.dbo.hp_MzVytvorOsobniKalendar <ZamestnanecId>, N'004', 2026, @R OUT;
```

Je idempotentní (když existuje, jen se vrátí) a řeší i typ výpočtu dovolené.

**NEPSAT to vlastními INSERTy.** 7. 9. 2026 jsem to zkoušel a narazil postupně na:
počítaný sloupec `NazevDne`, unikátní `AVAReferenceID` (GUID), a `USE` + `BEGIN TRAN`
v jednom bloku přes most se tiše neprovedlo. Helios na to má proceduru — použij ji.
**Obecné pravidlo: než napíšeš vlastní SQL do Heliosu, hledej `hp_*` proceduru.**

## Jak se to řeší teď — `mzdy_karta_kontrola` (g2007.python)

Volá se jako **krok 0** z `mzdy_generuj`, ještě **před** čistou vodou. Musí to být tam:
čistička i worker si berou seznam lidí z `TabZamMzd` a Helios z té samé karty počítá fond.
Záměrně **před** rozcestím na čistou vodu — generování se pouští i bez ní (dopočet lidí,
co ještě spočítaní nejsou) a ti by jinak zůstali na staré kartě.

Režim (rozhodnutí Peťa 7. 9. 2026: *„hlásit jen nějaký rozporuplný"*):

- **jednoznačné → opraví samo** (karta + osobní kalendář)
- **sporné → jen nahlásí**, nesahá se na to
- **generování se NIKDY nezastaví** — zastavit celé mzdy kvůli jednomu člověku je horší
  než je dopočítat a nahlásit

Hlášky jdou do výsledku (`karta_opraveno`, `karta_warn`) a **zobrazují se rovnou na
výplatnici** po generování — Peťa: *„mě asi nenapadne se jít kouknout, zda není něco
ve frontě k řešení"*.

## Výjimky — kdo se neřeší a proč

1. **JEDNATELÉ.** Kdo je aktivně přiřazený na post **`JEDNATEL`** (`tenant.org_post_assign`
   + `tenant.org_post`), má v Heliosu záměrně kalendář 009 = 0 h/týden, i když v Podmínkách
   40 h má. Ověřeno 7. 9. 2026: na postu sedí přesně Marti Pašek (EC 2, ES 41) a Branislav
   Mózer (EC 47) — a přesně ti tři mají v Heliosu 0 h. Nikdo jiný.
   **NEDĚLAT z toho seznam čísel v kódu.** Dřív bylo `_JEDNATELE_CISLA = {2, 41, 47}`
   natvrdo na několika místech a 31. 7. 2026 se ty konstanty při jiné úpravě omylem smazaly
   → jednatelé zůstali bez stravného. Změní se jednatel → přehodí se přiřazení na postu.
2. **NEAKTIVNÍ lidi** (`att_employee.is_active = false`). Nesahat (Peťa 7. 9. 2026:
   *„nesahej na neaktivní"*). Marti Pašek má stará osobní čísla (15), která už neplatí.
3. **DOHODY (DPP).** V Heliosu mají záměrně kalendář 011 = 0 h. V proceduře Centrály je
   poznámka *„Kristýna 29-3-2024 — změněno na kalendář s 0h kvůli nároku na dovolenou u DPP"*.
   První běh kontroly na to hned narazil (Senft EC 374: Podmínky 5 h, Helios 0 h).
4. **Jiné číslo kalendáře při shodných hodinách NENÍ nález.** Vlková EC 361 má 15 h
   a kalendář **012**; mapování z Centrály by dalo **010**. Obě jsou 15 h / 3 h denně,
   takže je to jedno. Potvrzeno proti kartě z plzeňského Heliosu.
   **Mapování úvazek→kalendář z Centrály je vodítko, ne autorita.**

## Jak se vybírá kalendář

Kandidáti = kalendáře daného roku se shodným `UvazekTyden`. Mezi nimi:

1. ten, který už člověk někdy měl (`TabMzKalendarZam` za jiný rok) — nejsilnější signál;
   Bernardová měla 004 v letech 2021–2025
2. jinak jednoznačně nejpoužívanější (pro 40 h má **004** čtyřicet dva lidí, zatímco
   001 jednoho a 002 nikoho)
3. jinak **spor** → jen nahlásit

## Co je sporné

- pro úvazek není v Heliosu žádný kalendář daného roku
- kandidátů je víc a nedá se mezi nimi rozhodnout
- člověk má v Podmínkách **víc různých platných úvazků naráz** — Marti Pašek má dvě
  pozice (Jednatel 20 h + Vedoucí projektů 40 h), takže nevíme, který poslat

## Ještě se nepřenáší

Centrála posílala i **druh PP** (0 = doba neurčitá, 1 = určitá, 13 = DPP; odvozuje se
z toho, jestli je vyplněné datum do), **datum vzniku PP**, **datum ukončení PP**
a **zkušební dobu**. Kontrola zatím řeší jen úvazek + kalendář. Peťa 7. 9. 2026 chce
přenášet všechno, co posílala Centrála — zbytek se doplní stejným způsobem.

Zajímavý trik z Centrály k převzetí: u nového zaměstnance vloží složku **250**
(„vojenské cvičení") **schválně jako poplach**, aby si účetní nové karty všimla.

