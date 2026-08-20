# Deploy-guard: most odmitne commit souboru, ktery je v g2007.soubor (DB=zdroj pravdy)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc (Vrstva 1 prevence, C24/Kristy 17.8.2026)
Web obsah (dilky /mobile, artefakty, ERP komponenty) patri VYHRADNE do `g2007.soubor` (DB = zdroj pravdy; appka se sklada z DB). Kdyz nekdo edituje takovy soubor v gitu a commitne, jeho zmena se do zive appky NIKDY nedostane -> tise zahozena prace. Presne to se stalo Peta 5.8. (oprava dovolene = penize) a Sarka 12.8. (4 HR veci) - 89 z 92 radku nikdy nebeselo. Kristy: "zakodovat, ne spolehat na peclivost."

## Co guard dela
V `scripts/claude_sql_runner.py`, funkce `_process_deploy`, krok 2.6 (po `git add`, PRED commitem): vytahne staged soubory (`git diff --cached --name-only`), zepta se DB `SELECT kod FROM g2007.soubor`, a kdyz je nektery staged soubor v tom seznamu -> deploy ZASTAVI, odstage-uje konfliktni soubor, nic nepushne/nenasadi. Hlaska: "DEPLOY: ZASTAVEN (DB-owned soubor) ... edituj pres @@G2007SOUBOR/@@G2007PUBLISH".
- DATA-DRIVEN: seznam DB-vlastnenych cest tahne z DB, zadny hardcode -> automaticky pokryva dilky, artefakty, komponenty, cokoli budouciho.
- FAIL-OPEN: kdyz check nejde (DB/sit/401), jen varovani a deploy POKRACUJE; cely guard je v try/except, aby NIKDY neshodil deploy.

## Jak reagovat na "ZASTAVEN (DB-owned soubor)"
Ten soubor NEEDITUJ v gitu. Edituj ho pres `@@G2007SOUBOR <kod> | <typ>` + obsah, nasad `@@G2007PUBLISH <kod>`. Git kopie by se do zive appky stejne nedostala.

## Rollout (AKCE PRO VSECHNY INSTANCE)
Guard je v runneru -> u kazde instance se aktivuje az si jeji watcher udela `git pull` + restart (jako lanes). Do te doby deploye jedou postaru bez guardu. Kazdy clovek navede svou instanci k restartu watcheru (`restart_self` z OPS lane / Restart-Service STRATEGIE-CLAUDE-SQL). Commit guardu 080a2116.

## Gotcha / poucemi
- Rows z plain SELECTu pres `_forward` jsou list-of-DICT (ne list-of-list) -> extrahuj `r.get("kod")`, ne `r[0]` (jinak KeyError:0 shodi deploy handler; stalo se 17.8., opraveno + guard obalen fail-open).
- Zbyva Vrstva 2 (gitignore DB-vlastnenych cest - z velke casti hotovo: mobile_parts + static_db) a Vrstva 3 (denni detekcni hlidac rozejiti git vs DB). A samostatne "Bod 2": most tise orezava konec obsahovych zapisu (base64+md5 jako standard, nebo opravit orez v mostu).

