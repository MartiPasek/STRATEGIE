# Docházka na neaktivní kartě: zábrana v databázi + osobní číslo do rozpadu z docházkového záznamu

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Docházka na neaktivní kartě — zábrana + osobní číslo do rozpadu (8. 9. 2026)

Zadala **Kristý 7.–8. 9. 2026**: *„kdo je píchnutý, tomu tečou hodiny, ne na jeho druhou kartu."*

## Co se stalo
Kristýna Marešová (user 11) má dvě docházkové karty — **41 (č. 21, aktivní)** a
**188 (č. 27, neaktivní)**. Za 2. a 3. 9. jí docházka ležela **na obou zároveň**:

| den | karta 21 | karta 27 |
|---|---|---|
| 2. 9. | práce 07:55–11:00 | oběd 11:00–12:00 + práce 12:00–17:17 |
| 3. 9. | sickday 3 h | práce 13:15–14:00, 15:00–20:00 |

Mzdový podklad z toho udělal **dva řádky na den**, a v noci na 7. 9. jim automat dopsal
**fond na obě karty zvlášť** (2. 9.: +4,92 h na 21 **a** +2,72 h na 27). Za 2. 9. tak
v podkladu stálo **8 + 8 = 16 h**.

## ⛔ Kde chyba NEBYLA (ověřeno čtením 7. 9. 2026)
Nepátrej tam znovu:
- **`att_day_summary_recompute` je správně** — bere kartu z docházkového záznamu
  (`GROUP BY a.employee_id`, pak `JOIN att_employee em ON em.id=b.eid`). Dva řádky byly
  věrným obrazem toho, že ta docházka opravdu ležela na dvou kartách.
- **`_att_employee` je správně** — Peťa ho 3. 9. opravila na deterministické řazení.
  Projeto **všech 19 živých skriptů** v `g2007.python`, které tu funkci nesou: všechny
  mají opravenou verzi. Stará zbyla jen v `__zaloha_*` a v `*_demo` (ukázkový tenant).
- **`att_fix_add`** (ruční doplnění v Opravách) — deterministický taky.

**Ty záznamy nepřišly z appky.** Všech 8 vzniklo **4. 9. 2026 v 07:03:22 — v jedné sekundě**,
s poznámkami „(oprava dochazky)" a „(zadano rucne)". Hromadný skript mimo appku.

## Zábrana (trigger, nasazeno 7. 9. 2026)
Protože Python guard hromadný zápis nechytí, sedí zábrana **na tabulce**:
`trg_att_entry_karta_guard` → funkce `tenant.att_entry_karta_guard()`,
`BEFORE INSERT OR UPDATE OF employee_id ON tenant.att_entry`.

| situace | co udělá |
|---|---|
| cílová karta je **aktivní** | nic, projde |
| **neaktivní** + člověk má **jednu aktivní** | **přesměruje** + do `note` dopíše `[karta: presmerovano z neaktivni c. NN]` |
| **neaktivní** + člověk má **víc aktivních** | **RAISE EXCEPTION** |
| neaktivní je jeho **jediná** | projde — ať se píchnutí nemá kam ztratit |

⚠️ Ten třetí řádek je schválně. Marti má karty **2 (EC) a 41 (ES) zároveň** (doktrína #24,
dvě firmy). Hádat mezi nimi by znamenalo **tiše přesunout hodiny mezi firmami** — to je
horší než hlasitá chyba.

**Ověřeno naostro 8. 9.:** superseded řádek s 0,00 h poslán na kartu 188 → vrátil se na 41
s razítkem v poznámce.

**Rozsah před nasazením:** 0 existujících řádků na neaktivní kartě; aktivní+neaktivní kartu
mají v celé firmě **dva lidé** (Kristý 21/27, Marti 2+41/15). Zábrana tedy nic legitimního
neblokla.

## Osobní číslo do rozpadu (opraveno 8. 9. 2026)
Nedeterministická věta byla **v rozpadu, ne ve mzdách** — a na **dvou** místech:

```sql
(SELECT cislo_zam FROM tenant.att_employee e
  WHERE e.user_id=:u AND e.tenant_id=:t AND e.cislo_zam IS NOT NULL LIMIT 1)
```

Bez řazení, bez filtru na aktivní. Proto měla Marešová **4. 9. rozpad na č. 27**, přestože
docházku měla ten den jen na 21.

| skript | verze | odkud bere číslo nově |
|---|---|---|
| `att_sync_vyroba_work` | **9** | z `att_entry` přes `att_entry_id` (ten INSERT ho už nesl) |
| `att_wa_open` | **4** | z **otevřeného** docházkového záznamu téhož člověka a dne |

U obou zůstal fallback, ale deterministický (aktivní karta, pak nejnižší id).

## 🔧 Gotcha: jak vůbec zapsat kód s dvojtečkou přes most
Most posílá SQL přes SQLAlchemy `text()`, takže **`:slovo` kdekoli v příkazu = bind param
→ pád**. A opravovaný kód je plný `:t`, `:u`, `:a`.

**Řešení:** dvoufázový replace, kde **kotva je bez dvojtečky** a nové dvojtečky se skládají
přes `chr(58)`:
1. kotva `'(SELECT cislo_zam FROM tenant.att_employee e WHERE e.user_id='`
   → nový text `... WHERE ae9.id=' || chr(58) || 'a),(SELECT ...'`
2. kotva `'e.cislo_zam IS NOT NULL LIMIT 1)'` → `'... ORDER BY ... LIMIT 1))'` (bez dvojteček)

**Před zápisem spočítej výskyty kotev** (musí být přesně 1) a **po zápisu ověř čtením** —
návratovka `G2007 KONSTRUKTIVNI` je neutrální. U živého kódu píchání navíc **protestuj
výsledný SQL** samostatným SELECTem s dosazenými hodnotami; syntaktická chyba by položila
každé píchnutí ve firmě.

## Co zůstalo otevřené
- **Nesouvisí s tím `mzdy_karta_hlidac`** (Peťa 7. 9.) — ten řeší **mzdovou** kartu
  v Heliosu (`TabZamMzd`) proti Podmínkám, ne docházkovou kartu. Nezaměňovat.
- Kristý 7. 9. odložila příznak na kartě „na tuhle kartu docházku nepíchat" — zábrana výše
  ho zatím nahrazuje.

