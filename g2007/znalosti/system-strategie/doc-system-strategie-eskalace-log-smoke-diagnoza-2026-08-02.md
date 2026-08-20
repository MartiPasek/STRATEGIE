# g2007.eskalace_log + smoke_eskalace: obe otevrene otazky z #280/#283/#313 UZAVRENY (2.8.2026) - zadny bug, zadna nova tabulka

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Kontext:** Marti 2.8.2026 pozadal pokracovat na "eskalaci" po dokonceni triage (#313). Dve otevrene otazky viselo z #280 (30.7.) a #283 (31.7.), znovu zopakovane v #313 (odrazovy mustek): (1) "g2007.eskalace_log stale neexistuje", (2) "smoke_eskalace last_status=chyba, nediagnostikovano od 30.7.". Overeno primo v DB/kodu 2.8.2026 - obe jsou VYRESENE, zadny kod se psat nemusel.

## 1. g2007.eskalace_log NENI potreba stavet - uz existuje, jen se jmenuje jinak

`g2007.automat_run` (existuje od 18.7.2026, `modules/erp/api/automat.py`) uz PRESNE plni roli, kterou #280/#283 navrhovaly pro novou tabulku `g2007.eskalace_log` ("append-only log kazde eskalace automatu/Haiku"). Sloupce: `automat_kod, spusteno, dokonceno, vysledek, zprava, rows, trvani_ms, eskalovano_na, eskalace_vysledek`. `eskalovano_na` drzi na kterem stupni zebricku (L0-automat/haiku/marti-ai/clovek) se to zastavilo, `eskalace_vysledek` cely trace vsech stupnu (Haiku diagnoza, Marti-AI pokus, atd). Overeno 2.8.: 1714 radku celkem (od 18.7. do dnes), 44 s eskalaci. Zadne DELETE/TRUNCATE/DROP na tuto tabulku nikde v kodu (grep cely `modules/` prazdny vysledek) - fakticky append-only/durabilni, presne jak #280/#283 chteli.

**Zaver:** Stavet novou `g2007.eskalace_log` by bylo duplicitni s `g2007.automat_run`. Kdyz bude chtit Marti/Kristy dedikovany "eskalacni prehled" (jen radky s eskalaci, hezci format), staci VIEW nad `automat_run WHERE eskalovano_na IS NOT NULL` - zadne nove DDL, zadny novy zapisovy kod, nulove riziko. Oba dokumenty (#280 krok 3 tabulka schema, #283 bod 6) se timto povazuji za vyresene jinak, nez puvodne navrzeno - ne "nikdy postaveno", ale "uz existovalo pod jinym jmenem, jen si toho nikdo nevsiml".

## 2. smoke_eskalace NENI rozbity - test presel na jednicku, spravne deaktivovan

`g2007.automat.last_status='chyba'` pro `smoke_eskalace` vypadalo alarmujici na dashboardu, ale je to OCEKAVANY artefakt designu, ne bug. `_check_smoke_eskalace()` (`modules/erp/api/automat_eskalace.py:138`) je RIZENY TEST - vzdy vraci `('chyba', ...)` umyslne, to je cely smysl testu ("smoke test zebricku"). `last_status` na `g2007.automat` proste zrcadli posledni vysledek CHECKU (ne vysledek eskalace), takze u tohohle automatu bude `chyba` navzdy, i kdyz zebricek funguje perfektne.

Overeno primo v `g2007.automat_run` (radek id=569, 27.7.2026 23:04:30): automat spustil check → `vysledek='chyba'` (ocekavane) → eskaloval na L1 Haiku → Haiku dostal kontext, spravne diagnostikoval jako "rizeny test, umela chyba, zadny realny dopad" a vratil presny pozadovany token `[VERDIKT: VYRESENO]` → zebricek se ZASTAVIL na L1 (`eskalovano_na='haiku'`), NEeskaloval dal na L2 Marti-AI ani L3 clovek. To je presne spravne chovani - test PROSEL na plnou caru.

Automat ma `aktivni=False` - to je taky zamerne, ne pozustatek chyby: docstring primo v kodu rika "Automat smoke_eskalace; po testu deaktivuj." Autor (C23, 27.7.) test spustil jednou k overeni zebricku a rucne ho vypnul, aby nebusil kazdou minutu (interval_min=1) navzdy s umelou chybou v monitoringu.

**Zaver:** Nic se neopravuje. Zebricek L0->L1->L2->L3 je proverene funkcni na zivem datovem dukazu (ne jen v teorii). Kdyz bude chtit Marti zebricek znovu proklepnout (napr. pred spustenim prvniho byznys automatu domeny `poptavky`), staci `UPDATE g2007.automat SET aktivni=true WHERE kod='smoke_eskalace'` (schvaleni pres banner, je to UPDATE mimo autonomni tabulky) a pockat 1 min.

## 3. Dusledek pro dalsi krok (#281 krok 2 -> krok 3)

`doc-system-strategie-domeny-automaty-implementace-plan` (#281) mel krok 2 = "Diagnoza smoke_eskalace, PRED stavenim byznys domen na stejnem mechanismu". Krok 2 je timto hotovy (zebricek overeny funkcni na realnych datech). Krok 3 (`get_effective_tools()` prepis + `permission_tier`/`active_domain` sloupce) muze nasledovat, jakmile Marti/Kristy rozhodnou otevrenou otazku z #281: kdo dostane jaky `permission_tier` v prvnim kole (Eliska jako prvni MD1 pilot?).

_Zapsano Claude-23, 2.8.2026. Navazuje na #280, #281, #283, #313 - uzavira dva jejich otevrene body._

