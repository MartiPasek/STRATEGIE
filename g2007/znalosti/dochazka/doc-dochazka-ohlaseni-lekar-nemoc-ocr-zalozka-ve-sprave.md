# Ohlášení lékaře, nemoci a OČR: dosud končila jen v mobilu vedoucího, teď mají záložku ve Správě docházky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Ohlášení lékaře, nemoci a OČR — záložka ve Správě docházky

**26. 8. 2026, Peťa + C26.** Zadala Peťa: *„aby se Dušan nebo kdokoliv mohl kouknout, že mu
to opravdu hlásil, ale jen info, nic víc."*

## Co se dělo
Když si člověk v mobilu ohlásí **lékaře, nemoc nebo OČR**, do docházky se **nic nezapíše**
(pravidlo Peti 30. 7., viz `doc-dochazka-sprava-vs-new-co-se-preklapi` — zadává se až
z dokladu). Jediné, co vznikne, je **notifikace vedoucímu do mobilu**. Ta se ale nikam
dál nepromítala, takže vedoucí neměl kde zpětně ověřit, že mu to člověk hlásil.
Sama notifikace to říká: *„Jen na vědomí, do docházky se nic nezapisuje."*

## Kde ta informace žije
`tenant.notification_log`, `zdroj='absence'`, `titulek ILIKE '%Nahlášená nepřítomnost%'`.
Sloupce: `created_at`, `target_user_id` (komu notifikace šla = vedoucí/odpovědná),
`titulek`, `zprava`, `ref_id`, `odeslano`. Ve stejném koši `zdroj='absence'` jsou i jiné
druhy (nová žádost o absenci, zapsaná/upravená/zrušená absence, neomluvená absence) —
proto ten filtr na titulek.

## Co je hotové
- **Dataset `dochazka.ohlaseni_zdravi_list`** (fw.data_set, id 221) — sloupce
  `RadekId` (`N:<id notifikace>`), `Kdy`, `JmenoPrijmeni`, `Druh`, `Ohlaseni`, `KomuPrislo`.
- **Třetí pohled v endpointu** `/app/dochazka-zak-tab/data?obdobi=ohlaseni`
  (`_DZT_DATASET["ohlaseni"]`, commit `8f1d342d`) — jediná část, která šla přes deploy.
- **Záložka „🧑‍⚕️ Ohlášení lékař / nemoc / OČR"** v `dochazka-po-zakazkach.html`
  (`COLS_OHL`), **jen ke čtení**, žádné akce.
- Ověřeno na produkci: 12 řádků, mimo jiné „Jan Peřina: Lékař 13. 8. — u lékaře do ~09:00",
  komu přišlo: Dušan Havlát.

**Práva se NEMĚNILA** (Peťa: *„nechceme nic přepisovat, chceme aby tam viděli stejní lidi"*).
Záložka dědí přístup obrazovky = `_DZT_ALLOWED` v `dochazka_zak_tab.py`, což je **pevný
seznam 11 uživatelů** (1, 11, 13, 16, 17, 18, 20, 41, 107, 108, 109) plus rodiče, a kdo je
v něm, **vidí všechny lidi** — žádné omezení „jen moji lidé" tam není. Že je seznam
natvrdo v kódu, je proti pravidlu „práva se nepíšou do kódu"; vědomě ponecháno.

## Háčky
- **Druh se pozná z TEXTU zprávy** (`ILIKE '%Lékař%' / '%OČR%' / '%Nemoc%'`), ne z uloženého
  údaje — notifikace na žádost navázaná není a `ref_id` na `att_absence_request` neukazuje.
  U těchto tří druhů to vychází spolehlivě, ale je to odvozené.
- **Zdroj „žádost z appky" v přehledu Správa docházky je natvrdo napsaný text**, ne uložený
  údaj: dataset dá každé žádosti `'app'::varchar src` a pak vypíše „žádost z appky".
  **Odkud žádost přišla, se dnes nedá zjistit** — `att_absence_request` nemá sloupec zdroje.
  A žádosti nevznikají jen z mobilu: `/app/dochazka-abs/new` (Správa docházky, „nová absence
  za jiného člověka") zakládá rovnou schválenou žádost + dny.
- **Zkušební ohlášení nejsou nijak označená.** 26. 8. se musely 4 kusy (Hrůzová 3×,
  Honomichl 1×) smazat ručně z `notification_log`. Kdo bude zkoušet, ať počítá s tím,
  že se to objeví lidem v přehledu.
- `fw.data_set` má `db_connection_id` **NOT NULL** — při zakládání nového datasetu ho
  opsat z existujícího (`SELECT db_connection_id FROM fw.data_set WHERE code=…`), jinak
  INSERT spadne na NotNullViolation.

## Otevřené
- Sloupce ve Správě docházky, které Peťa chce od 25. 8.: **autor záznamu** (dnes se do něj
  přepisuje ten, kdo schválil nebo opravil — to je špatně), **kde bylo pořízeno** (appka/ERP),
  **kdo schválil**, **kdy schválil**, **kdo změnil**, **kdy změnil** (podle poslední změny).
  Neuděláno — chce to zásah do datasetu na čtyřech místech naráz (větev dnů, větev žádostí,
  výčet sloupců v obou částech UNION, výsledný SELECT) plus hlavičku tabulky. Vzor, kde tyhle
  údaje už jsou spočítané, leží v `scripts/_dochazka_109_sloupce.sql` (nenasazený, 21. 7.).

