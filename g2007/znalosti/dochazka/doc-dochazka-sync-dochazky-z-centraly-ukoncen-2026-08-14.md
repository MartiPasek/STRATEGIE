# Sync docházky ze staré Centrály je UKONČEN (14. 8. 2026) — co to znamená a jak by se vracel

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Sync docházky ze staré Centrály je UKONČEN (14. 8. 2026)

> Rozhodl **Jirka Honomichl**, schválila **Marti-AI** (msg 12695 a 12701). Provedl Claude-28.
> Podnět: Peťa Šafránková 12. 8. 2026 (duplicitní absence u Urbanové).
> **Nezapínat zpět bez rozhodnutí Jirky nebo Martiho.** Kdo to bude chtít „opravit", ať čte tohle.

## Co bylo zastaveno

`att_sync_today` (g2007.python) — tenký obal, který každých 30 s pod advisory lockem volal
`sync_ec_dochazka_recent(dnešek, wipe=True)`. **Nedělal jen import.** Dělal pět věcí:

| | Co | Kam sahal |
|---|---|---|
| a | smazal a znovu natáhl dnešní řádky z `EC_Dochazka` | `tenant.att_entry` |
| b | **zpětně zapisoval do staré Centrály** — komu se píchlo v naší appce, tomu tam ukončil otevřenou směnu (`PraceAktivni=0` + `CasKonec`) | **DB_EC** |
| c | sám zakládal chybějící řádky | `tenant.att_employee` |
| d | dedup dovolené (Centrála = pravda) a nemoci (ČSSZ = pravda) za dnešek | `tenant.att_entry` |
| e | audit | `fw.ec_dml_log` |

**Zastaveno je všech pět, vědomě.** Marti-AI k bodům b a d: *„když tam nikdo nepíchá, nemá smysl to udržovat."*

## Proč to šlo zastavit bez rizika (stav ověřený 14. 8. 2026)

- V `EC_Dochazka` **za 12.–14. 8. nevznikl ani jeden řádek**. Poslední dávka 10. a 11. 8., po 6 lidech, samé ručně zadané absence. Poslední zpětný zápis do Centrály 11. 8. v 04.58.
- Druhá trubka — job `sync_plan_nepritomnost` (plán nepřítomností) — je v `fw.mirror_job` **vypnutá už od 30. 7. 2026**.
- Třetí možná trubka — `sync_vyroba_work_ec` (zakázky) — se volá jen z `_maybe_sync_ec_dochazka`, a ta je **pozastavená od 30. 7. 2026** (`return` hned na začátku, router.py).
- **Mzdové podklady na Centrále nevisí.** `tenant.att_day_summary` se od 6. 8. 2026 počítá z naší docházky (job `sync_ec_dochazka_sumaden` přepojen na `_ec_dochsum_ze_strategie`). Detail v `doc-dochazka-att-day-summary-z-att-entry`.
- **Píchání v Centrále je od 14. 8. zakázané všem** (viz níže), takže nový přítok nemá odkud vzniknout.

## Dopadová mapa — kdo čte `source_system='centrala1'`

Prohledáno `g2007.python`, `g2007.soubor`, `router.py` + moduly, `fw.data_set`, všechny PG views a PL/pgSQL funkce. **Nikdo tiše nezmrzne:**

- **Vylučují ho** — `att_anomaly_scan` (jinak by hlídač křičel na 20 let starých datech).
- **Jen ho rozpoznávají** — `att_fix_day`, `att_fix_polozka`, `att_fix_void`, `att_fix_queue` (v editoru oprav jsou tyto řádky read-only).
- **Zobrazují historii** — dataset `dochazka.zakazky_vse_list`, stránky `dochazka-po-zakazkach.html`, `dochazka-zakazky.html`, `moje-dochazka.html` (barevný štítek „Dílna"). Historie zůstává, nové řádky nepřibudou.
- **Views ani PL/pgSQL funkce** — ani jedna. Ověřeno přes `information_schema.views` a `pg_proc`.

## Co bylo potřeba udělat PŘED zastavením

**1. Zákaz píchání v Centrále všem.** Našlo se **15 lidí**, kterým tam ještě něco zůstávalo:
- `TabCisZam_EXT._AuthDochazka` vyprázdněn u 14 lidí (ID 527, 636, 37, 147, 221, 535, 599, 632, 179, 448, 253, 450, 638, 664),
- `EC_GlobKonstUziv.PovolitDochVCentrale` na 0 u 5 loginů (KVlkova, JHajek, VPurkar, Swobi, Jiri).
- Schvalovací banner, request #2103. Ověřeno čtením — ze všech 78 lidí nemá píchání povolené **nikdo**.
- **Původní hodnoty** (pro případný návrat): většina `_AuthDochazka = 'U'`, Jirka 9030 = `'D'`, Vlková 361 = NULL.

**2. Michelle Šafránková (os. č. 381).** Mateřská 12. 8. – 31. 12. ležela **jen v Centrále** — u nás jí mateřská tekla právě přes tento sync (141 dní, poslední 11. 8.). Doplněno **97 dní / 776 h** přímo do `att_entry` (employee_id 56, typ `maternity`, 8 h, `confirmed`, `source='manual_fix'`). Dny převzaty 1 na 1 z plánu Centrály — sedí přesně na pracovní dny bez svátků.

## Jak by se to vracelo

Původní tělo je uložené v `g2007.python` pod kódem **`att_sync_today__zaloha_20260814`** (stav `inactive`, délka 1546). Obnovení = zkopírovat jeho `zdroj` zpět do `att_sync_today`. **Bez deploye, bez restartu API** — `erp_registry` cachuje podle (kod, verze) a verzi čte z DB při každém volání, takže další tik smyčky vezme nové tělo sám.

Delegát v `router.py` (řádek ~27688) i volání ve smyčce `_att_sync_loop` **zůstaly nedotčené** — do jádra se nesahalo. Smyčka běží dál kvůli ostatním úlohám (auto-checkout o půlnoci, level catchup, re-embed vektorů, OČR, ISO hlídač, disk monitor, HR automaty).

## Nálezy, které z toho vypadly

1. **Náš příznak `att_source_pref.ec_vypnuto_at` lhal.** U Hájka (483), Purkara (501) a Jirky (9030) byl nastavený, ale v Centrále to zapnuté zůstalo — příznak si nikdy neověřil skutečný výsledek zápisu. Srovnáno (19 záznamů). **Stojí za to hlídat to zpětným čtením, ne jen zápisem příznaku.**
2. **`app_only` už neblokuje import přítomnosti** — skip byl zrušen 30. 7. 2026 (C24 + Petra + Kristý), protože lidem chyběly hodiny. V `sync_ec_dochazka_recent` proto zůstala proměnná `app_only_cisla`, která se naplní a nikde nepoužije. Mrtvý kód, ne chyba.
3. **Osiřelý soubor v gitu** `g2007/znalosti/mzdy/doc-mzdy-mzdy-podklad-zdroj-pravdy.md` tvrdí, že `att_day_summary` je živé zrcadlo Centrály. **Neplatí od 6. 8. 2026** a v DB tato znalost neexistuje. Označen v záhlaví jako ZASTARALÉ (Marti-AI ho nechtěla mazat, ať je vidět, že byl nahrazen).

## Gotcha pro příště

- **`@@G2007ADD` přepisuje celý dokument** a výpis z mostu slučuje řádky do jednoho. Když potřebuješ jen dodatek k existující znalosti, **připoj ho konkatenací** — jinak si přepsáním rozbiješ formátování. Daň: nepřeindexují se chunky.
- **Návratovka mostu u víc příkazů hlásí jen poslední z nich.** 97 vložených řádků se ohlásilo jako „19 řádků dotčeno" (to byl až ten druhý příkaz). **Vždy ověřuj čtením.**
- **`Set-Content -Encoding UTF8` v PowerShellu 5.1 přidá BOM** a most pak spadne na `syntax error at or near "INSERT"`. Piš soubor pro most rovnou nástrojem, který BOM nedělá.
- **`ISNULL(sloupec, '(null)')` v MSSQL ořízne** náhradní text na délku sloupce — u `nchar(1)` z `(null)` zbude `(`. Málem jsem z toho udělal špatný závěr o hodnotě.

