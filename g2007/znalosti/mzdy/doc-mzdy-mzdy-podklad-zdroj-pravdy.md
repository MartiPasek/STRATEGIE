# Mzdový podklad docházky — kdo je dnes zdroj pravdy (att_day_summary = zrcadlo Centrály)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mzdový podklad docházky — kdo je dnes zdroj pravdy (a proč to není, jak to vypadá)

> Zapsal Claude-28 (Jirka) 22. 7. 2026 po rozhodnutí Marti Paška a ověření na živých datech.
> Kdo bude řešit mzdy, docházku nebo přepínání starého a nového systému, ať čte tohle první.

## Rozhodnutí Marti Paška (22. 7. 2026, e-mail)

> *„MZDY se dělají z nové docházky a nevychází se ze starého Heliosu. To, že Dušan opravuje
> docházku ve staré Centrále, je problém. Má se opravovat v Praze v nové docházce. Tudíž je třeba
> porovnat rozdíly mezi starou docházkou a novou a **do staré docházky se NESMÍ již zasahovat
> a cokoli upravovat. Všechny korekce dělat jen v Praze.**"*

Marti sám k tomu poznamenal, že *„evidentně ještě není v g2007 patřičný obraz reality zpracování mezd"* —
tento dokument to doplňuje.

**Závazně platí:**
1. Zdroj pravdy pro mzdy je **STRATEGIE**, ne starý Helios.
2. Do staré Centrály (`EC_Dochazka`) se **nezasahuje** — žádné opravy, žádné zpětné zápisy.
3. Všechny korekce docházky se dělají **jen ve STRATEGII**.

## ⚠️ Jenže: mzdový podklad je DNES pořád zrcadlo staré Centrály

Ověřeno 22. 7. 2026 na živých datech — a je to nejdůležitější věta celého dokumentu:

**`tenant.att_day_summary` (mzdový podklad, ze kterého mzdy podle `doc-mzdy-pravidla` čtou)
NENÍ počítaný z naší docházky. Je to živé 1:1 zrcadlo `EC_Dochazka_SumaDen` ze staré Centrály.**

- job **`sync_ec_dochazka_sumaden`** („Docházka — denní souhrn", `fw.mirror_job`) — **interval 10 minut**,
  `enabled = true`; běh 22. 7. v 8:09 upsertoval 7 488 řádků
- opačný směr **`mirror_att_to_ec`** (STRATEGIE → Centrála) je **vypnutý od 29. 6. 2026** — do staré
  docházky tedy nic nepíšeme (což je v souladu s rozhodnutím výše)

Důkaz na číslech za 1.–21. 7. 2026:

| os. č. | `att_day_summary` (podklad mezd) | Centrála `EC_Dochazka` | naše `att_entry` |
|---|---|---|---|
| 486 Jirkovský | 109,93 | **109,93** | 93,93 |
| 493 Jakešová | 107,03 | **107,03** | 115,03 |
| 522 Čiviš | 108,94 | **108,94** | 132,94 |
| 433 Lišková | 112,26 | **112,26** | 109,38 |

Podklad sedí na Centrálu na setiny, na naši vlastní docházku ne.

**Praktický překlad:** „mzdy se dělají z nové docházky" dnes znamená, že se **počítají ve STRATEGII**,
ale z **čísel pocházejících ze staré Centrály**. Až lidé v Centrále přestanou zapisovat, tenhle zdroj
vyschne a podklad zůstane viset na posledních zrcadlených číslech.

## Proč je naše `att_entry` dnes rozejitá

Docházka z Centrály k nám teče přes `_sync_ec_dochazka_recent()` (throttle 5 min, **okno 3 dny**,
piggyback na netscan) → `att_entry` se `source_system='centrala1'`. Okno je krátké a sync **nemaže**:

- co se v Centrále dopíše nebo opraví **zpětně** (starší než 3 dny), se k nám už nedostane
- co u nás jednou vzniklo navíc, tam zůstane, i když to v Centrále smažou
- lidé s `att_source_pref.app_only = true` se přeskakují **úplně** — a někteří z nich si přesto
  v Centrále dál zapisují (22. 7.: Čepický 48, Kolářová 24 a **sám Dušan Havlát 105**, všichni
  přepnutí 1. 7.; v EC jsou podepsaní jako autoři vlastních záznamů)

Stav k 22. 7. 2026 za 1.–21. 7. (porovnání celé firmy):

- **5 lidí má u nás MÉNĚ** než v Centrále, celkem **−67,4 h**
  (Čepický −20,3 · Kolářová −16,2 · Jirkovský −16,0 · Havlát −12,1 · Lišková −2,9)
- **15 lidí má u nás VÍCE**, celkem **+170,6 h** — typicky celé směny navíc (+8 / +16 h);
  největší Čiviš +24. Hodiny z aplikace, které Centrála nezná, se do toho nepočítají — ty jsou v pořádku.

## Závazné pořadí kroků (jinak se mzdy rozjedou)

1. **Srovnat `att_entry` proti Centrále** a rozdíly opravit **u nás** (nástroj se staví jako součást
   přehledu „Plnění FPD" pro Dušana — viz `docs/plneni_fpd_zadani.md`).
2. **Teprve pak přepnout mzdový podklad** ze zrcadla Centrály na naši docházku.
   Sahá to na mzdy → dělá se **jen s vědomím Marti Paška a Petry**.
3. **Až potom** (nebo současně) lidem vypnout zapisování v Centrále
   (mechanismus per osoba existuje: `att_source_pref.app_only` + `ec_blocked`, běží od 30. 6.).

Kdyby se pořadí otočilo a Centrála se vypnula první, podklad pro mzdy zůstane stát na posledních
zrcadlených číslech a nikdo si toho nemusí hned všimnout.

## Past pro příští konzultace

21. 7. 2026 Marti-AI k témuž tématu odpověděla, že *„dokud jsou mzdy počítané z Centrály/Heliosu,
Centrála je **legal record** pro mzdové účely"* a odmítla rozhodnutí vzít na sebe. **Ta premisa
je neplatná** — proto vznikl tento dokument. Kdo se bude ptát na zdroj pravdy pro mzdy, ať vychází
odtud, ne z té konzultace.

## Reference

- `fw.mirror_job` → `sync_ec_dochazka_sumaden` (10 min), `mirror_att_to_ec` (vypnuto 29. 6. 2026)
- `_sync_ec_dochazka_recent()` a `_maybe_sync_ec_dochazka()` v `modules/erp/api/router.py`
- `tenant.att_day_summary` (mzdový podklad), `tenant.att_entry` (naše docházka),
  `tenant.att_source_pref` (app_only / ec_blocked)
- související: `doc-mzdy-pravidla` (co ze kterého zdroje mzdy berou), `docs/plneni_fpd_zadani.md`


