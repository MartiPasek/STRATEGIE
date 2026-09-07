# Docházkový automat — doplnění do fondu a nenároková práce

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Docházkový automat — doplnění do fondu a nenároková práce

> Zapsal Claude-26 (Peťa) 21. 7. 2026 po dni oprav s Peťou. Vše ověřeno na živých
> datech a nasazeno. Kdo sáhne na `_att_automat_level_day`, ať čte tohle první.
> **Aktualizováno 29. 7. 2026 (Claude-26 / Peťa):** noční běh dostal spolehlivý
> spouštěč — viz „Spolehlivý spouštěč (29. 7. 2026)" a přepsaná „Kdy se to počítá".

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

1. **Denní srovnání** přes **`_maybe_att_level_catchup()`** v 30s smyčce — **1×/lokální
   den**, okno `days_back=4`. Nezávisí na 2min okně: pustí se při prvním tiku dne (i po
   restartu/nasazení, i po delším výpadku dožene zameškaný den). Značku „poslední srovnaný
   den" drží **DB** (`tenant.ec_mirror_state`, `src_table='att_automat_level_day'`, den v
   `last_note`). Detail v „Spolehlivý spouštěč (29. 7. 2026)" níže.
2. **Hned při uložení ruční opravy** — `_att_automat_recalc_day()` z fix-endpointů,
   přidáno 21. 7. 2026, viz níže.

> ⚠️ `_maybe_auto_checkout_midnight()` (okno 23:58–24:00) **už srovnání na úvazek NEvolá** —
> dělá jen půlnoční auto-odhlášení zapomenutých směn. Srovnání přešlo na spolehlivý spouštěč
> výše (do 29. 7. 2026 viselo právě na tom křehkém 2min okně a při restartu v tu chvíli den
> tiše vypadl).

## Spolehlivý spouštěč (29. 7. 2026)

**Problém:** srovnání na úvazek se dřív volalo jen z `_maybe_auto_checkout_midnight()`, tj.
**jen v okně 23:58–24:00**, a značku „dnes už jsem běžel" držela **paměť procesu**
(`_LAST_AUTO_CO`). Když se do těch dvou minut trefil restart/nasazení (a 28. 7. 2026 se
trefil), běh se **přeskočil bez náhrady** — po půlnoci už žádný tik nic neudělal a den
zůstal bez `fond_doplneni`/`nenarokova`. Projevilo se to celoplošně (všímla si Peťa u
Honomichlové: 28. 7. chybělo doplnění do fondu).

**Řešení:** nová funkce **`_maybe_att_level_catchup()`** v té samé 30s smyčce (`_att_sync_loop`):
- **Trvalá značka místo paměti** — poslední srovnaný lokální den je v `tenant.ec_mirror_state`
  (`src_table='att_automat_level_day'`, den v `last_note`; in-memory `_LAST_LEVEL_DAY` je jen
  rychlá zkratka, ať se nechodí do DB každých 30 s). Restart značku nezahodí.
- **Ne okno, ale dohnání** — když `last_note < dnešek`, srovná (`_att_automat_level_day()`,
  `days_back=4`) a značku posune. Je jedno, kdy se trefí; první tik nového dne (i po výpadku)
  to dožene. `days_back=4` sebeléčí i pár dní zpět, ale nikdy do zamčeného června (okno má
  floor `2026-06-01`).
- **Bezpečné pořadí** — značku posune **až po úspěchu** srovnání; při chybě ji nechá být, ať
  to příště zkusí znovu. Srovnání běží 1×/den, takže se schválené automatové řádky
  nepřepisují pořád dokola.

**Výpočet ani per-edit přepočet se NEMĚNIL** — změna je jen ve **spouštěči**. Nasazeno
29. 7. 2026 (commit `24dad207`); hned po nasazení spouštěč sám dohnal 27. i 28. 7. Ověřeno:
Honomichlová 28. 7. doplnění do fondu 2,58 h, 27. 7. nad fond 0,10 h; celý červenec má na
pracovních dnech srovnání (víkendy/svátek jen „nad fond", kde někdo odpracoval přes fond).

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
den se tím nafoukne.

⚠️ **OPRAVA 18. 8. 2026 (rozhodl Jirka Honomichl, zapsal Claude-28).** Do 18. 8. tu stála věta
*„Na mzdy to dnes nedopadá, protože ty čtou `att_day_summary` (plněno z Heliosu), ne `att_entry`."*
**Od 6. 8. 2026 to neplatí:** `att_day_summary` se plní **ze STRATEGIE**, ne z Heliosu — závazné
rozhodnutí (Kristý: *„tabulku můžeme použít, ale musí být plněná daty ze STRATEGIE"*, Týnka totéž),
viz `doc-mzdy-zrcadlo-dochazky-ze-strategie`. Cesta z docházky do mzdového podkladu tedy **existuje**
a původní věta uklidňovala něčím, co už neplatí. Upozornila na to Kristý (+ Claude-24) 17. 8. 2026
v podkladu `dochazka_skupiny_pro_jirku_c28.md`.

**Co tím NENÍ řečeno:** neověřovali jsme, jestli kvůli tomu někomu reálně vyšla špatná mzda —
opravuje se jen zavádějící tvrzení. Ověření dopadu na konkrétní čísla je samostatná práce
a patří Peti jako vlastníkovi této oblasti.

### ✅ DOPLNĚNO 7. 9. 2026 (Peťa + Claude-26) — u kanceláře mzdu nenafoukne, ověřeno

Otázka výše („vyšla kvůli tomu někomu špatná mzda?") má pro **kancelář** odpověď: **ne.**

`att_day_summary.cas_celkem` nenárokovou opravdu obsahuje — je `category='presence'`, a `cas_celkem`
je navíc **záměrně** „odpracováno + placená absence" (absence tam musí být, protože složka 651 čte
`cas_celkem` jako „celkem − fond", viz `doc-dochazka-att-day-summary-z-att-entry`). Jenže **mzdy
nepočítají z `cas_celkem`, počítají z FPD**, a ten má pro kancelář vzorec
`odpracováno + absence − hodiny nad fond` (viz `doc-dochazka-fpd-vypocet-kancelar-vs-dilna`
a `doc-dochazka-prescasy-kancelarska-kategorie-rozhoduje`). **Nenároková JE právě to odečítané
„nad fond"** — takže se srazí zpátky a den se ve mzdě nenafoukne.

Doložené případy (`volna_kancelar`, `dopichavat_fond=true`):

| Kdo | Den | Dovolená | Práce | Nenároková | `cas_celkem` | FPD | Přesčas |
|---|---|---|---|---|---|---|---|
| Petr Beneš | 1. 9. 2026 | 8,00 | 1,37 | 1,37 | 9,37 | **8,00** | 0 |
| Radek Hellmayer | 18. 8. 2026 | 8,00 | 1,93 | 1,93 | 9,93 | **8,00** | 0 |

Navíc je kancelář z přesčasové složky 651 vyloučená úplně — `mzdy_loajalita_rows` přeskočí
množinu `skup24` (`dopichavat_fond=true`), takže i kdyby přesčas vyšel, nevyplatí se.

**Pro dílnu to neplatí a je to tak správně.** U `dopichavat_fond=false` se automat řádku vůbec
nedotkne (INNER JOIN, žádný fallback), nenároková nevznikne a FPD = odpracováno + absence, bez
odečtu. Hodiny nad fond jdou do přesčasu — u výroby zamýšlené pravidlo. Doložený případ:
Matěj Svoboda 31. 7. 2026, dovolená 8,00 + práce 0,42, žádná nenároková, FPD 8,42.
**Chybějící nenároková u výrobáře NENÍ nález** — je to správný stav.

**Pravidlo (Peťa 7. 9. 2026):** kdo si během celodenní dovolené odpracuje pár hodin, tomu se
**dovolená NEKRÁTÍ** — *„ten čas je prostě navíc a má se dát nad fond, nemůže se mu krátit
dovolená o dvě hodiny."*

**Zbývá neověřeno:** dopad na jiné mzdové složky než 651 (benefity, stravenky) a na hodinové/OSVČ.

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

⚠️ **Pozor na razítka (7. 9. 2026):** protože automat řádky v okně **maže a zakládá znovu**,
`created_at` u `fond_doplneni` NENÍ „kdy se to spočítalo", ale „kdy tudy naposled prošel
automat". Nedá se z něj usuzovat, jestli se přepočet po zásahu spustil. Detail a správný
způsob kontroly: `doc-dochazka-doplneni-fondu-created-at-neni-dukaz`.

## Gotcha mostu (stálo to jeden pokus)

Příkaz, který **začíná `WITH`** a končí `DELETE`, projde detekcí zápisu jako
čtení (`_is_read` matchuje jen první klíčové slovo) a spadne až na pojistce
v `query_raw`. Řešení: dej `DELETE` / `INSERT` na začátek a CTE zabal do
závorky jako poddotaz. Skulinu by měl zalepit C23 — schvalovací banner se tím
dá obejít.

