# Faze B: 15 read-only dochazkovych funkci migrovano do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Faze B: 15 read-only dochazkovych funkci migrovano do g2007.python (31.7.2026)

Pokracovani schvaleneho planu z analyza_mzdy_dochazka_vyroba.md (sekce 2, "Plain funkce bez zapisu").

## Migrovane funkce (kod v g2007.python)
att_ec_druh_entry_type, att_announce_absence_typ, att_sick_balance_h, att_can_fix, att_fix_scope, att_fix_scope_emps, att_fix_all, att_fix_editors_for_emp, att_can_lock, att_period_locked, att_fix_parse_hhmm, att_fix_overlap, att_fix_merge_candidate, att_is_working, att_denni_fond.

Vsechny stav_zivota='active', verze=2, min_pravo='clen' (default).

## Dulezite metodologicke vylepseni: AST misto regex pro hranice funkci
Drivejsi davky pouzivaly heuristiku "najdi dalsi def/class/@ radek" pro urceni konce funkce pri extrakci i pri delegate-patch replace. U teto davky se ukazalo, ze to NENI spolehlive: mezi koncem funkce a nasledujicim def muze byt modulova konstanta (napr. `_ABS_STATUSY = {...}` hned po `_announce_absence_typ`, `_REZIE_REF = "Rezie"` hned po `_att_is_working`), kterou by regex-heuristika omylem zahrnula do "tela funkce" a pri replace SMAZALA z router.py — pritom tyto konstanty pouzivaji i JINE, dosud nemigrovane funkce.

Oprava: pouzit `ast.parse()` a cist `node.lineno`/`node.end_lineno` primo z AST stromu (Python 3.8+), ne regex. To dava PRESNOU hranici funkce bez ohledu na to, co nasleduje. Chyceno a opraveno PRED jakymkoliv zapisem do DB nebo router.py, overeno diffem, ze obe konstanty zustaly bajt-identicke.

**Toto je ted standardni postup pro vsechny dalsi faze** — regex-based "find next def" se jiz nepouziva pro urcovani hranic pri delegate-patch replace.

## Vynechano (na prvni pohled "bez zapisu", po rucnim overeni zapisove/orchestracni)
- `_att_apply_work_selection` — obsahuje realne UPDATE tenant.att_entry (2x)
- `_att_resync_full` — orchestrator, opakovane vola `sync_ec_dochazka_recent(wipe=True)` pro cely rok
- `_att_sync_today` — vola `sync_ec_dochazka_recent(wipe=True)` pod advisory lockem, soucast zivého 30s tiku dochazky

Tyto tri patri do pozdejsi zapisove faze (Faze C), ne do teto bezpecne read-only davky.

## Krizove zavislosti mezi migrovanymi funkcemi
- `att_fix_scope` inlinuje verbatim kopii `_att_can_fix` (self-contained skript, ne cross-script erp_registry.call — konzistentni s drivejsim sobestacnym vzorem)
- `att_fix_editors_for_emp` inlinuje verbatim kopii `_att_fix_scope_emps`
- `att_sick_balance_h` inlinuje retezec `_resolve_cond_num` -> `_resolve_cond` -> `_cond_group_of`

Puvodni funkce v router.py VSECHNY zustavaji i jako samostatne definice (nesmazany), protoze je pouzivaji i jini, dosud nemigrovani volajici.

## Deploy
Diff proti HEAD potvrdil PRESNE 15 hunku. ast.parse + py_compile OK pred deployem. Commit 12dcd3ebb (50 insertions, 288 deletions), push OK, cloud restart (~5s).

## Dalsi kroky
Faze C (dochazka+mzdy zapisove funkce, ~35 vc. ted odlozenych 3) nasleduje dle "Doporucene poradi" v analyza_mzdy_dochazka_vyroba.md.

