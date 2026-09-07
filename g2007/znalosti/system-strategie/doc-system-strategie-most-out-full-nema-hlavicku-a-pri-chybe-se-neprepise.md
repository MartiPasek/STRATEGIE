# Plný výstup mostu nemá hlavičku s časem a při chybě se vůbec nepřepíše — jde přečíst cizí odpověď

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Plný výstup mostu nemá hlavičku s časem a při chybě se vůbec nepřepíše — jde přečíst cizí odpověď

Zapsal Claude-28 (Jirka Honomichl) **7. 9. 2026**, schválila Marti-AI (msg 14856).
Root cause dohledaný v `scripts/claude_sql/claude_sql_runner.py`, ne odhadnutý z chování.
Dvakrát za jedno dopoledne mě to svedlo přečíst starou odpověď jako platnou.

## Tři věci, které to způsobují

**1. Při chybě se plný výstup vůbec nepřepíše.**
`_write_full()` se volá **jen na úspěšné větvi** (řádek 699). Všechny chybové větve —
`401`, vypršení času, chyba v SQL — volají pouze `_write_out()`. Po chybě tedy zůstane
v `CLAUDE<N>_OUT_FULL.txt` **předchozí úspěšná odpověď** a vypadá naprosto platně.
Kdo si po chybě otevře plný výstup, čte odpověď na svůj **minulý** dotaz.

**2. Plný výstup nemá hlavičku s časem.**
`_write_full()` (řádky 427–444) zapisuje **holý TSV** — první řádek jsou názvy sloupců,
dál data. Žádné `# STATUS`, žádné datum. Kdežto `_write_out()` hlavičku s časem má.
**U plného výstupu proto NEJDE poznat, jestli je odpověď čerstvá.** Přitom právě čas
v hlavičce je jediný důkaz, že odpověď je tvoje a ne zbytek po minulém dotazu.

**3. Patička odkazuje vždy na první linku.**
Text *„↳ plný výstup bez ořezu: `scripts/claude_sql/CLAUDE_OUT_FULL.txt`"* je na řádku 704
**natvrdo, bez ohledu na linku**. Pracuješ-li na lince 2 nebo 3, patička tě posílá
do souboru **linky 1**, kde leží výsledek úplně jiného okna.

## Jak s tím pracovat, dokud to nikdo neopraví

- **Vždy si nejdřív přečti `CLAUDE<N>_OUT.txt` a zkontroluj čas v hlavičce.**
  Teprve když je čerstvý, sáhni na plný výstup. Obráceně to nejde ověřit nijak.
- **Skončil dotaz chybou? Plný výstup je NEPLATNÝ**, ať v něm stojí cokoli. Nečti ho.
- **Patičku ignoruj a otevři si soubor své linky** (`CLAUDE2_OUT_FULL.txt`,
  `CLAUDE3_OUT_FULL.txt`). Na první lince patička sedí, jinde ne.
- Čteš-li plný výstup skriptem hned po spuštění, počítej i s **obyčejným závodem o čas** —
  most obsluhuje linky popořadě a odpověď nemusí být ještě zapsaná.

## Návrh opravy (pro toho, kdo se do toho jednou pustí)

Tři úpravy v `claude_sql_runner.py`, každá malá a nezávislá:

1. **Hlavička s časem i do plného výstupu** — `_write_full()` ať jako první řádek zapíše
   totéž `# STATUS … / # <čas>` jako `_write_out()`. Tím zmizí hlavní příčina: nedá se
   poznat stáří. (Pozor: kdo plný výstup čte strojově, čeká na prvním řádku názvy sloupců —
   hlavičku je proto lepší uvodit `#`, ať jde snadno přeskočit.)
2. **Přepsat plný výstup i na chybových větvích** — stačí zavolat `_write_full([], [])`
   (nebo zapsat jednořádkové `# CHYBA — plný výstup neexistuje`), ať tam nezůstane
   stará odpověď.
3. **Patičku sestavit podle aktuální linky** — místo natvrdo psaného názvu použít
   `OUT_FULL_FILE.name`, který už `_run_lane()` na správnou linku přesměrovává.

Kód mostu jsem **záměrně neměnil** — nebylo to zadané a měnit most na konci session
je zbytečné riziko. Až se to bude opravovat, po každé změně runneru je nutný **restart
služby** `STRATEGIE-CLAUDE-SQL`, jinak běží dál starý kód z paměti.

Souvisí: [[doc-system-strategie-bridge-most-lanes-ops]] ·
[[doc-system-strategie-most-timeout-zapisu-nerika-nic]] ·
[[doc-system-strategie-most-401-failover-na-sekundar-bez-tokenu]]

