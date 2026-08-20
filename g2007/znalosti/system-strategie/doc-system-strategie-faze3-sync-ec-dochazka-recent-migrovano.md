# Jádrový EUROSOFT docházkový sync (_sync_ec_dochazka_recent) migrován do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Stav: HOTOVO A AKTIVNÍ (31.7.2026, commit 5316dfa20, C23 + Marti, po domluvě)

Doplňuje `doc-system-strategie-faze3-dochazka-mzdy-4-funkce-migrovany` — tuhle funkci jsem tam původně vynechal (aktivně rozpracovaná Kristý), Marti potvrdil že Kristý dnes dedup-fix dokončila a chtěl ji zahrnout kvůli nadcházející dovolené (chce mít co nejvíc doodchyceno před příští týden, kdy on i Kristý odjíždí).

## Co je migrováno

`sync_ec_dochazka_recent` — inkrementální upsert `EC_Dochazka` (Centrála MSSQL) → `tenant.att_entry`, včetně dnešního (31.7.) dedup-fixu absencí (Centrála=pravda dovolená, ČSSZ=pravda nemoc) a uzavírání otevřených směn v Centrále při app check-inu. Nejsložitější migrace dosud — 7 vnořených závislostí (module konstanty `_DRUH_ABSENCE/_DRUH_HO/_DRUH_SKIP`, funkce `_ec_druh_entry_type`, `_ec_dml_log`, `_ec_close_open_shift`, `_norm_zakazka`, `_att_session`, `logger`), všechny zdvojené do DB řádku.

## Metodika (zpřísněná po předchozí dávce)

1. Všechny závislosti extrahovány **verbatim** (přímým čtením ze zdroje, ne ručním přepisem) — první pokus měl ruční přepis `_norm_zakazka` s překlepem (`"rezie","rezie"` místo `"rezie","режie"`), zachyceno regex kontrolou před insertem, opraveno verbatim extrakcí.
2. **Aktivace DB řádku PROBĚHLA PŘED deployem** delegát patche (opačné pořadí než minulá dávka — poučení z 30–45s okna, kdy volání vráceli chybu).
3. **Diff proti `git show HEAD:soubor` PŘED deployem** — potvrzeno přesně 1 hunk, žádný kolaterál.

## Důležitý kontext nalezený cestou

Sousední `_maybe_sync_ec_dochazka()` (periodický trigger, běžel by co 5 min) je od 30.7.2026 (C24) **POZASTAVENA** kvůli řízenému přeimportu července — migrace na tom nic nemění (jinou funkci jsem nesahal), auto-sync zůstává stejně pozastavený jako předtím. Reálný provoz teď jede jen přes explicitní volání (`app_hr_import_dochazka`, ruční reimport nástroje). První reálné ověření aktivace bude až při příštím explicitním použití, ne automaticky za 5 minut.

## Commit

- `5316dfa20` — delegát patch (router.py: 6 insertions, 211 deletions, ověřeno diffem = 1 cílený hunk).

Shrnutí celé dnešní Fáze 1+3 dohromady: 7 funkcí migrováno a aktivní (`mzdy_absence_rows`, `mzdy_stravenky_rows`, `att_recompute_header_from_items`, `sickday_lekar_apply`, `refresh_employee_active`, `sync_plan_to_dochazka`, `sync_ec_dochazka_recent`) + obecná infrastruktura (`erp_registry.py`, `g2007.python`/`_historie`/trigger, `/selftest` + `/run` endpointy, `min_pravo` + `python_run_audit`).

