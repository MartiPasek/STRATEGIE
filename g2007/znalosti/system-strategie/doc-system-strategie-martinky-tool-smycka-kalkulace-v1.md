# Tool-smycka Martinek + kalkulacni nastroje ABSAUGWERK - NASAZENO+OVERENO E2E 3.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Tool-smycka (martinka_dispatch v6, md5 f9fa59bc...)
Martinka (run_goal beh) nema HTTP session ani tool_registry - nastroje za ni spousti DISPATCHER: goal obsahuje seznam READ-ONLY nastroju domeny (whitelist = g2007.python kategorie='martinky' AND vedlejsi_ucinek=false AND kod NOT LIKE 'martinka%/maminka%'), Martinka ukonci beh markerem [NASTROJ kod=X args=<JSON pole bez uid>] + [STAV: NASTROJ], dispatcher zavola erp_registry.call(kod, uid, *args), vysledek appenduje do goal kontextu a spusti ji znovu - max 3 kola nastroju na ukol, kazde volani do vlakna (ukol_zprava typ='nastroj'). Zamitnuti mimo whitelist + JSON chyby se vraci Martince jako text.

## Kalkulacni nastroje (#1679)
- kalkuluj_absaugwerk(uid, profil flex|nass, bom_text 'REGCIS*QTY,...' nebo list, kw): obal kalkulace_engine.compute_absv1 (ceny max(prijemka, Velky cenik) + flagy, koef VKM/Arbeit z EC, profil marze/fix/floor) + strojove shrnuti (gesamt, nabidnout, chybejici).
- kalk_prevod_regcis(uid, vyrobce, syrove_cislo): obal regcis_build (syrova cisla vyrobcu -> nase reg_cis).

## GRANT (#1680, nutny pro beh z aplikace)
Aplikacni role strategie NEMELA prava na schema proj (engine driv bezel jen pres most pod superuserem) -> GRANT USAGE ON SCHEMA proj + SELECT ON ALL TABLES + ALTER DEFAULT PRIVILEGES ... GRANT SELECT (read-only). Bez toho compute_absv1 padal na InsufficientPrivilege proj.cenik_import.

## OVERENO E2E (3.8. ~09:35, ukol #7 pilot)
Ukol 'kalkulace FLEX+ pres nastroj' (RIT 8206000*1 + SIE 5SY4110-6*2, kw=15) v domene kalkulace_obecna: Martinka sama zavolala kalkuluj_absaugwerk (1 tool kolo), vysledek == rucni referencni beh na znak: material 699.80, VKM 21.75, Arbeit 42.00, marze 12% 91.63, fix 330, GESAMT 1185.18 -> nabidnout 1190, vc. flagu 'zdrazeno(cenik>prijemka)' u SIE dilu doporuceneho k rucni kontrole. Stav ke_schvaleni.

## Dusledek pro ABSAUGWERK
Martinka kalkulace je pripravena NA KLIC - az Eliska doda SMART Excel (11 listu) + FLEX priklad (PDF+Excel kusovnik), zbyva: (a) per-zakaznicke domeny kalk_absaugwerk_flex/smart + vybava (know-how z podkladu), (b) realny pilot proti skutecne fakturovane cene (zdroj pravdy ceny vyjasnit - viz doc-kalkulace-rozvadecu-orientace-kalkulace-martinky-2026-08-02 bod 5).

