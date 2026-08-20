# Faze E davka 1: 17 GET HTTP endpointu dochazky migrovano na DB-driven delegaty

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Po overenem pilotu (att_status) migrovano prvnich 17 GET/read-only HTTP endpointu dochazky na Cesta B vzor (commit 89b73c799, 31.7.2026 17:00-17:16 UTC).

Endpointy: att_absence_mine, att_absence_inbox, att_announced_future, att_daily, att_day_detail, att_fix_allowed, att_fix_cinnosti, att_fix_zakazky, att_fix_queue, att_fix_day, att_fix_audit_list, att_fix_lide, att_period_lock, att_list, att_real, att_unconfirmed, att_whereabouts.

Wrapper vzor rozsiren o dve obecna pravidla, aby vsech 17 sdilelo jednu sablonu:
1) Delegat muze vratit "_status_code" v navratovem dict - wrapper ho pop()-ne (default 200) a nastavi HTTP status. Cela byznys logika vc. 403/400 vetvi zustava v DB, wrapper je genericky pro libovolny status.
2) Wrapper predava SUROVE query-param stringy (req.query_params.get se stejnym defaultem jako original) jako pozicni argumenty do run(uid, ...). Parsovani/validace zustava uvnitr delegata - zachovava presne puvodni chovani vc. chybovych cest.

Gotchas nalezene pri teto davce:
- _is_parent existuje v router.py DVAKRAT (radek 14902 a 24871) - pri module-level importu POSLEDNI definice prekryva prvni. Pri hledani zavislosti vzdy zkontrolovat pocet vyskytu `def <jmeno>`, ne jen prvni nalezeny vyskyt.
- Male jiz-migrovane Faze-B delegat-stuby (_att_can_fix, _att_fix_scope, _att_can_lock apod.) lze inlinovat VERBATIM do noveho skriptu - automaticky funguje jako cross-script erp_registry.call bez zvlastniho zachazeni. Cross-script call jako explicitni volba zustava vyhrazena pro VELKA (>100 radku) tela.

Diff proti fresh HEAD potvrdil 9 hunku (nekolik se mergovalo kvuli sousednim funkcim), overeno per-funkci markery + grepem na nepritomnost puvodnich telesa. Zadny kolateral (_ABS_STATUSY zustava netknuta, pouziva ji nemigrovany att_absence_decide).

Post-deploy overeno pres SQL most: vsech 17 kodu stav_zivota='active'. Celkem aktivnich funkci v g2007.python: 77.

Politika pro dalsi davky Faze E (zavedena pilotem, potvrzena zde): dalsi GET/read-only endpointy stejneho tvaru NEVYZADUJI per-endpoint zivy self-test - staci staticka rigoroznost (AST hranice, diff proti HEAD, per-funkci marker/absence grep, ast.parse+py_compile). Zivy self-test (porovnani legacy vs. novy vystup pres /erp_registry/run) se zopakuje pred prvnim POST/zapisovym endpointem Faze E, kde je riziko vyssi.

