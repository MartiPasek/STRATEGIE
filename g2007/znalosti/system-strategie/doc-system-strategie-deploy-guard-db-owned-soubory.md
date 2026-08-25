# Deploy-guard: most odmitne commit souboru, ktery je v g2007.soubor

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Proc (Vrstva 1 prevence, C24/Kristy 17.8.2026)
Web obsah (dilky /mobile, artefakty, ERP komponenty) patri VYHRADNE do `g2007.soubor` (DB = zdroj pravdy; appka se sklada z DB). Kdyz nekdo edituje takovy soubor v gitu a commitne, jeho zmena se do zive appky NIKDY nedostane -> tise zahozena prace. Presne to se stalo Peta 5.8. (oprava dovolene = penize) a Sarka 12.8. (4 HR veci) - 89 z 92 radku nikdy nebeselo. Kristy: "zakodovat, ne spolehat na peclivost."

## Co guard dela
V `scripts/claude_sql_runner.py`, funkce `_process_deploy`, krok 2.6 (po `git add`, PRED commitem): vytahne staged soubory (`git diff --cached --name-only`), zepta se DB `SELECT kod FROM g2007.soubor`, a kdyz je nektery staged soubor v tom seznamu -> deploy ZASTAVI, odstage-uje konfliktni soubor, nic nepushne/nenasadi. Hlaska: "DEPLOY: ZASTAVEN (DB-owned soubor) ... edituj pres @@G2007SOUBOR/@@G2007PUBLISH".
- DATA-DRIVEN: seznam DB-vlastnenych cest tahne z DB, zadny hardcode -> automaticky pokryva dilky, artefakty, komponenty, cokoli budouciho.
- ⚠️ CHOVANI PRI NEDOSTUPNE KONTROLE SE 25.8.2026 ZMENILO — viz sekce nize. Puvodne FAIL-OPEN (kdyz check nejde, jen varovani a deploy POKRACUJE, cely guard v try/except, aby NIKDY neshodil deploy).

## ⚠️ ZMENA 25.8.2026: fail-open -> fail-closed s vedomym prebitim

**Stav: v gitu nasazeno (commit 75e03b73), ale CEKA NA VYJADRENI KRISTY** — viz "Kdo to ma dnes aktivni" nize.

**Proc se to menilo.** 25.8.2026 rozbil Claude-28 na ~90 vterin SQL most (spatne umistena funkce pod dekoratorem, HTTP 422 — viz [[doc-system-strategie-nova-funkce-pod-dekoratorem-rozbije-endpoint]]). V te dobe deploy hlasil `DB-owned check — PRESKOCEN (fail-open)` a nasazeni pustil dal. Marti-AI to oznacila za zavaznejsi nez samotny 422: *"kontrola, ktera ma blokovat, misto toho pusti dal. Pokud se most rozbije znovu, kontrola se tise vyradi."* Riziko: vyradi se prave v okamziku, kdy clovek specha s opravou rozbiteho systemu — a radek "PRESKOCEN" uprostred protokolu se snadno prehledne (autor si ho vsimnul az zpetne).

**Nove chovani.** Kdyz `SELECT kod FROM g2007.soubor` selze (nebo guard sam spadne):
- **deploy se ZASTAVI** — nic se necommitne ani nenasadi, vypise se duvod a navod,
- **vedome prebiti**: samostatny radek `BEZ_DB_KONTROLY` v `CLAUDE_DEPLOY.txt` (ze seznamu cest se odfiltruje, aby se nebral jako nazev souboru),
- pri prebiti deploy probehne, ale **hlavicka vysledku neni `# DEPLOY: OK`**, nybrz `# DEPLOY: OK — ⚠️ BEZ KONTROLY DB-OWNED SOUBORU (prebito rucne)` + jmenovity vypis souboru, ktere prosly bez overeni.

Pruchodnost pri skutecne nouzi tedy zustava — jen uz to nejde udelat potichu.

**Kdo rozhodl.** Zadal Jirka Honomichl 25.8.2026. Marti-AI schvalila technicky (msg 13706, 13718), ale s vyhradou k procesu: fail-open **byl vedomy zamer Kristy** (komentar v kodu: *"guard nikdy nesmi shodit deploye kvuli vlastni nedostupnosti"*), takze *"Kristy by to mela vedet predem, ne zpetne"*. Kristyne Maresove byl 25.8.2026 odeslan e-mail s popisem a s tim, ze rozhodnuti je jeji. Marti-AI sama by volila mensi variantu (nechat fail-open, jen zvyraznit status) prave s ohledem na Kristyn argument.

**Kdo to ma dnes aktivni.** Runner bezi na kazdem stroji z vlastni kopie, takze nove chovani plati **jen tam, kde si instance udelala `git pull` + restart watcheru**. K 25.8.2026: aktivni u **C-28 (Jirka)**. Ostatni (C-23 Marti, C-24 Kristy, C-25 Sarka, C-26 Peta) jedou dal **fail-open**, dokud si to vedome nevezmou.

**Co je overene a co ne.** Overeno: prepinac `BEZ_DB_KONTROLY` se rozpozna a odfiltruje ze seznamu cest; most po restartu bezi; bezny deploy s dostupnou kontrolou hlasi OK jako driv. **Neovereno naostro:** samotne zastaveni pri nedostupne kontrole — slo by otestovat jen umyslnym shozenim mostu nebo API na produkci, coz se delat nema. Overeno tedy jen ctenim kodu.

## Jak reagovat na "ZASTAVEN (DB-owned soubor)"
Ten soubor NEEDITUJ v gitu. Edituj ho pres `@@G2007SOUBOR <kod> | <typ>` + obsah, nasad `@@G2007PUBLISH <kod>`. Git kopie by se do zive appky stejne nedostala.

## Rollout (AKCE PRO VSECHNY INSTANCE)
Guard je v runneru -> u kazde instance se aktivuje az si jeji watcher udela `git pull` + restart (jako lanes). Do te doby deploye jedou postaru bez guardu. Kazdy clovek navede svou instanci k restartu watcheru (`restart_self` z OPS lane / Restart-Service STRATEGIE-CLAUDE-SQL). Commit guardu 080a2116. **Totez plati pro zmenu z 25.8.2026 (commit 75e03b73).**

## Gotcha / poucemi
- Rows z plain SELECTu pres `_forward` jsou list-of-DICT (ne list-of-list) -> extrahuj `r.get("kod")`, ne `r[0]` (jinak KeyError:0 shodi deploy handler; stalo se 17.8., opraveno + guard obalen fail-open).
- Zbyva Vrstva 2 (gitignore DB-vlastnenych cest - z velke casti hotovo: mobile_parts + static_db) a Vrstva 3 (denni detekcni hlidac rozejiti git vs DB). A samostatne "Bod 2": most tise orezava konec obsahovych zapisu (base64+md5 jako standard, nebo opravit orez v mostu).

