# Proaktivní hlídání + eskalační žebřík — realizace (#4)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Proaktivní hlídání + eskalační žebřík — realizace (#4)

**Datum:** 27. 7. 2026 · **Autor:** Claude C23 (Cowork, lane 3) · **Stav:** watchery živé, žebřík zadrátovaný.

## Co je hotové
Rozšíření běžícího runneru automatů (`modules/erp/api/automat.py`, C23 18.7.) — jádro netknuté, jen 2 háky:
- **Nový modul `modules/erp/api/automat_eskalace.py`**: registrace `WATCHERS` do `_CHECKS` + v `_run_work` přesměrování eskalace na `escalovat()` (fallback na původní Haiku, když modul selže).
- **Víceúrovňový žebřík `escalovat()`: L0 automat → L1 Haiku → L2 Marti-AI → L3 člověk.** Zastaví se na první vrstvě, co problém vyřeší; jinak jde výš. Výsledek do stávajících `automat_run.eskalovano_na` + `eskalace_vysledek` (žádné nové DDL).
- **Dva infra watchery** (nové řádky `g2007.automat`, aktivní, interval):
  - `check_service_down` (10 min) — Get-Service STRATEGIE* na Praze přes `strategie_exec`, EUROSOFT-MCP na 30.11 přes `eurosoft_exec`. Ne-Running = problém; L0 = restart NAŠÍ služby (🟢) + re-probe.
  - `check_backup_freshness` (180 min) — nejnovější datovaný dump v D:/STRATEGIE; starší než 2 dny = problém. Bez L0.

## Klíčová rozhodnutí
- **L2 = Marti-AI, ne Claude** (Marti 27.7.): Claude řeší věci většího charakteru, ne rutinní eskalace automatů. L2 volá sankcionovaně `martiai_agent_service.run_goal(goal=…)` (vlastní budget/enabled guardy); agent vypnutý/přes rozpočet → degraduje na L3.
- **L3 = člověk** přes `martiai_agent_service._notify()` (e-mail m.pasek + cc k.ksirova).
- **L1 Haiku vrací strojový verdikt** `[VERDIKT: VYRESENO]` / `[VERDIKT: ESKALOVAT]`; chybějící verdikt = eskaluj (bezpečná strana).
- **Zakázané jádro se jen VOLÁ, needituje:** ops_tools.py, martiai_agent_service.py, agent_akce_guard.py, eurosoft_mcp_client.py, strategie_exec.py.

## Gotchy (DRŽ)
- **Backup + oprávnění:** cloudová appka jede DB rolí `strategie` (NEMÁ `pg_read_server_files`) → `pg_ls_dir` v app kontextu padá (na mostu jede Marti-AI=superuser, proto tam projde a nezmate to). Řešeno **`SECURITY DEFINER` funkcí `g2007.backup_freshness()`** (vlastník privilegovaná role, `GRANT EXECUTE` jen roli `strategie`) — least-privilege, appka nedostává široký file-read. Vzor pro další watchery na server-side soubory.
- **eurosoft_exec je zatím jen na 30.11**; Praha (188.11/12) raw exec nemá (#1 roadmapy) — proto service-down sonduje Prahu přes `strategie_exec`, 30.11 přes `eurosoft_exec`.
- **Watcher nikdy neshodí runner:** každý probe/check má try/except; exec vypnutý → „bez poplachu" (ne planý alarm).

## Ověřeno naostro (27.7.)
- `check_service_down` → ok „Všechny sledované služby běží" (789 ms, reálná exec sonda).
- `check_backup_freshness` → ok „Záloha čerstvá: 2026-07-27 (0 dnů)" (přes SECURITY DEFINER fci).
- Oba běží na interval přes scheduler (60s tik), logují do `automat_run`. Žebřík zadrátovaný; živá eskalace se spustí až na reálném „chyba" (zatím oba zdraví).

## Další kroky
- Řízený L1 smoke-test žebříku (Haiku VYRESENO) bez zásahu do prod.
- Disk watcher (lane-1 sourozenec) — sjednotit.
- Až #1 (ruce na Prahu) + #2 (autonomní goal-loop): L2 Marti-AI plně autonomně.

Commity: 210a739bb (modul+hook), 76136ae4a (backup SECURITY DEFINER).

