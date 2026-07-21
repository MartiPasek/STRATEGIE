# Docházkový automat — doplnění do fondu a nenároková práce

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Docházkový automat — doplnění do fondu a nenároková práce

> Zapsal Claude-26 (Peťa) 21. 7. 2026 po dni oprav s Peťou. Vše ověřeno na živých
> datech a nasazeno. Kdo sáhne na `_att_automat_level_day`, ať čte tohle první.

## K čemu automat je

U kancelářských kategorií (`tenant.att_kategorie.dopichavat_fond=true`) srovnává
dokončený den na **osobní denní fond**:

- odpracováno **pod** fond → přidá řádek **`fond_doplneni`** (chybějící kus do fondu)
- odpracováno **nad** fond → přidá řádek **`nenarokova`** (přebytek nad fond)

Fond na osobu = `engagement.uvazek_tyden_h / work_mode.dny_v_tydnu`, záložně
`att_kategorie.fond_h_den`. Vše dělá jediná živá funkce
**`_att_automat_level_day()`** v `modules/erp/api/router.py`.

⚠️ `_att_automat_fond_fill()` a `_att_automat_fond_odpich()` jsou **mrtvý kód** —
nula volání. Needituj je, nic nedělají.

## Kdy se to počítá

1. **Noční běh** 23:58–24:00, okno `days_back=4` (přes `_maybe_auto_checkout_midnight`).
2. **Hned při uložení ruční opravy** — přidáno 21. 7. 2026, viz níže.

## Co se 21. 7. 2026 opravilo (čtyři chyby)

### 1. Po ruční opravě se fond nepřepočítal

Endpointy `att_fix_entry` / `att_fix_add` / `att_fix_void` / `att_fix_merge`
přepočet **nevolaly vůbec**. Doplnění do fondu zůstalo viset na hodnotě spočtené
před zásahem. Dny do 4 dnů zpět srovnal až noční běh, **starší dny nikdy**.

**Řešení:** `_att_automat_level_day` umí volitelné `employee_id` + `day` (cílený
přepočet jednoho dne) a nový obal **`_att_automat_recalc_day()`** se volá ze všech
čtyř endpointů **za `s.commit()`**, tedy ještě před odpovědí do prohlížeče.

Pojistky v obalu: nikdy nevyhodí výjimku (oprava je už zapsaná a nesmí spadnout
kvůli automatu); nepřepočítává **běžící den** (člověk má rozdělanou směnu);
zamčené měsíce řeší už samy fix-endpointy dřív.

### 2. Počítaly se STORNOVANÉ pauzy

CTE `brk` nemělo filtr `status NOT IN ('superseded')` — na rozdíl od `iv`.
Když se pauza opravila, odečetla se **stará i nová**.

### 3. Pauza se odečítala, i když leží MIMO práci

Výpočet předpokládal, že pauza je uvnitř pracovního záznamu. Když je ale práce
rozdělená a pauza je v mezeře mezi kusy (09:40–13:09 / pauza / 13:24–16:04), je
z práce **už vynechaná** a druhé odečtení ubralo hodiny dvakrát.

**Řešení:** odečítá se jen **průnik** pauzy se sloučenou pracovní dobou
(`LEAST(b.en,m.en) - GREATEST(b.s,m.s)`, ořezáno na ≥ 0). Pauza bez časů (jen
hodiny, typicky import z Centrály) se odečte celá — nevíme, kde leží.

> Reálný případ (Beneš 9. 7.): práce 3,48 + 2,67 = 6,15, pauza 0,25 v mezeře,
> navíc stornovaná pauza 2,08. Automat počítal 6,15 − 2,33 = 3,82 → doplnil
> **4,18 h**. Správně: 6,15 → doplnit **1,85 h**.

### 4. Doplňovalo se i o víkendu a o svátku

Automat kalendář vůbec nečetl a v sobotu i o svátku počítal s fondem 8 h. Kdo si
v neděli odpíchl 2 h, dostal dopsáno 6 h „do fondu".

**Řešení:** doplnění jen když `tenant.att_calendar_day` říká
`is_workday=true AND NOT is_holiday`. **Odpis nad fond (`nenarokova`) běží dál
i o víkendu** — ten nikomu hodiny nepřidává (rozhodla Peťa 21. 7.).

⚠️ **Kalendář je naplněný jen do konce roku 2026.** Od ledna 2027 by automat
potichu přestal doplňovat. Je proto doplněno varování do logu, když den nemá
záznam v kalendáři. Kalendář plní Kristý — na podzim připomenout.

## ⚠️ Nenároková práce NENÍ hodiny navíc

Nejčastější omyl (spadl do něj i tenhle Claude). `nenarokova` je **ta část
odpracovaných hodin, která přesáhla fond**, ne čas navíc:

> odpracováno 15,02 při fondu 8 → nenárokových 7,02 je **uvnitř** těch 15,02.
> Sečteno dohromady vyjde 22,04 — nesmysl.

Do součtu dne se proto **nepřičítá**, ukazuje se jen jako „z toho".
`fond_doplneni` se naopak přičítá — ten fond doplňuje.

### Nedodělek k rozhodnutí

Původní záměr (docstring mrtvé `_att_automat_fond_odpich`) byl: *„placená doba =
strop fond, celková přítomnost zůstává zachovaná"* — tedy hodiny nad fond
**ubrat z práce** a překlopit do nenárokové. Ta polovina se ale nikdy
nezrealizovala: živá funkce jen **přidá řádek**, práci nesrazí.

Důsledek: `nenarokova` má `category='presence'`, takže ji většina součtů
(`/attendance/daily`, `_konto_compute`, HR grid, mobil „Odmakáno") **přičte** —
den se tím nafoukne. Na mzdy to dnes nedopadá, protože ty čtou
`att_day_summary` (plněno z Heliosu), ne `att_entry`.

**Otevřené rozhodnutí pro Martiho:** dodělat sražení práce na fond, nebo přestat
nenárokový řádek zakládat? Peťa 21. 7.: *„rozhodně nechceme, aby se mazaly"* —
evidovat se má, jde jen o způsob.

## Zpětné dopočty (jak na ně)

Noční běh sahá 4 dny zpět, takže starší dny je nutné dopočítat dávkou přes most.
21. 7. proběhly dvě (červenec, práh změny ≥ 0,03 h): 8 řádků po opravě přepočtu,
83 řádků po opravě pauz. **Červen a starší se nesmí — jsou zamčené, mzdy proběhly.**

Past: `_att_automat_level_day` je idempotentní (smaže automatové řádky v okně
a vloží znovu), ale dávka psaná ručně v SQL musí mít **stejnou logiku pauz**,
jinak si zaneseš zpátky tu chybu, kterou jsi právě opravil.

## Gotcha mostu (stálo to jeden pokus)

Příkaz, který **začíná `WITH`** a končí `DELETE`, projde detekcí zápisu jako
čtení (`_is_read` matchuje jen první klíčové slovo) a spadne až na pojistce
v `query_raw`. Řešení: dej `DELETE` / `INSERT` na začátek a CTE zabal do
závorky jako poddotaz. Skulinu by měl zalepit C23 — schvalovací banner se tím
dá obejít.


