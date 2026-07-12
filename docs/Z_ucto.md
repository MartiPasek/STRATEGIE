# ÚČETNICTVÍ + SYSTÉM ZÁPISŮ — znalostní báze

> **Živý dokument.** Při jakékoli práci na účtování ho čti jako první a **průběžně aktualizuj**.
> Rozhodnutí zapisuj datovaně do changelogu dole. Odkaz v `CLAUDE.md` (rozcestník nahoře).

---

## 1. Cíl a směr (Marti, červenec 2026)
**Otočit tok dokladů a banky o 180°:** místo *realita → starý Helios (Plzeň) → zrcadlo Praha*
nově **realita → STRATEGIE → nový Helios (Praha, cloud CMIS na 188.12).**
- Důvod: Asseco ukončilo podporu staré MSSQL DB → přechod na novou; současně s digitalizací
  na bezpečný cloud v Praze (CMIS). Úspora: MSSQL **Express** místo Standard.
- **Mzdy** už jedou v Praze napřímo. **Účetní deník** je v Praze (2025 přeneseno).
- Horizont otočení: ~3 týdny (plán: `docs/prechod_helios_praha_plan_2026-07.md`).

## 2. Model účtování (ZÁVAZNÉ — Marti 6.7.2026)
Čisté a jednoduché, **žádné komplikace se sborníkem 080** (zbytečná oklika a starosti).
- **Účtovat banku a doklady rovnou do peněžního deníku** — standardně, jako doteď.
- **Peněžní deník = náš `tenant.ucetni_denik`** (cloud, Praha). Je to **věrný obraz / další stupeň kontroly.**
- **Účetní deník = ROZHRANÍ mezi dvěma světy: STRATEGIE ↔ Helios.**
- **Dva příznaky = hlavní nástroj účetní: `Zkontrolováno` a `Rozporováno`.**
  Účetní potvrzuje, co je dobře, nebo rozporuje, co se jí nezdá. **Kontrola PO zápisu, ne brána před ním.**
- **Zaúčtováno se hned promítne do dalšího stupně kontroly → věrný obraz účetnictví okamžitě, bez zpoždění.**
  (Účetní nezdržuje zápis, jen ho průběžně „prosvěcuje" dvěma příznaky.)

## 3. Příznaky v OBOU světech (klíčový postřeh Marti 6.7.)
Účetní je konzervativní a důkladná — **musí `Zkontrolováno`/`Rozporováno` vidět v Heliosu i u nás.**
Proto příznaky **žijí v obou denících a zrcadlíme je obousměrně** (deník je most).
- **STRATEGIE:** příznaky jako sloupce na `tenant.ucetni_denik` **i na dokladech**.
- **Helios:** přes **`UCTO_EC.dbo.TabDenik_EXT`** — Helios systémový mechanismus (každá tabulka může mít
  `_EXT`, custom pole s prefixem `_`; Helios upgrady ji respektují, nešaháme do 223 systémových sloupců).
  Návrh polí: `Id` (= `TabDenik.Id`), `_Zkontrolovano` (bit), `_Rozporovano` (bit),
  `_ZkontrolovalKdo`, `_ZkontrolKdy`, `_RozporDuvod`, `_ZmenilKdy`.
- **Zrcadlení příznaků obousměrně** přes most (`db=mssql188` ↔ PG). Kanály máme.

## 4. Stav pražského Heliosu (ověřeno 6.7.2026)
`UCTO_EC.dbo.TabDenik`: **2025** (IdObdobi 39) = 67 903 řádků; **2026** (IdObdobi 40) = 29 921 řádků, 21 sborníků.
- 2026 data v Praze **jsou**, ale zatím jako **zrcadlo Plzně** (přes `@@XFER` office→Praha). Uzávěrka 2026 čeká na potvrzení daňařem.
- `TabDenik` má 223 sloupců, žádnou `_EXT` (jen `IdPoznamka`) → `_EXT` vytvoříme my.
- Období: EC 2025=39, 2026=40; ES 2025=1007.

## 5. Stavební kameny (co už máme — NESTAVÍME znovu)
- **Doklady:** `oz_*` zrcadla (poptávky→faktury→výdejky) + `tenant.vp_pipeline`.
- **Banka:** RB Premium API (EC+ES živě), párovací engine `/app/bank/parovat` (92 %).
- **Engine deníku (24.6.):** `tenant.ucetni_denik` (+ `ucet_predkontace`, `bank_predpis`, `ucet_sbornik`,
  `ucet_doklad`), párování→předkontace→deník. *Deník je teď PRÁZDNÝ (reset) — znovu naplníme.*
- **Cloud Helios 188.12:** `UCTO_EC`/`UCTO_ES`, most **`db=mssql188`** (parent-only, read+DDL/DML přímo),
  `@@XFER` (office→Praha), reconciliace office×cloud po účtech.

## 6. Závazná pravidla (z 24.6., platí)
- **Způsob B zásob od 1.1.2026:** NEúčtovat příjemky ani výdejky; skladové účty vyloučit z vyhodnocení
  (editovatelný seznam vyloučených účtů). Pozn.: ~56 % řádků EC deníku byly právě tyhle = velká úspora.
- **Zakázky a střediska (útvary) se v účetnictví NErozlišují** — analytiku zakázek vedeme, ale **mimo Helios**.
- **Doklady a banka NEJSOU součástí Heliosu.** Helios = jen účetnictví + mzdy. Rozhraní = deník.
- **Uzávěrky:** do uzavřeného období se neúčtuje ani neopravuje (tvrdý blok). Oprava = **storno + přeúčtování**
  (append-only audit), ne mazání. Reconciliace **per období**.
- **Atribuce aktéra** na každém zápisu: `automat:<engine>` / `ai:marti-ai` / `human:<user>`.
- **Příznak `jistota` (0–100 %)** na zápisu — automat dle síly pravidla, AI dle inference; účetní review
  řazená vzestupně dle jistoty (pozornost na nízkou).

## 7. Věrný obraz = reconciliace
Paralelní jištění: **náš deník × Helios `TabDenik`** — když sedíme, je to jištění; když ne, ukáže chybu dřív.
Reconciliace per období, skladové/vyloučené účty se přeskakují.

## 7b. Saldokonto = derivát deníku (klíčový postřeh Marti 6.7.2026)
**„Kdo komu dluží" NENÍ samostatný zdroj — je to jen POHLED na zaúčtovaný deník.**
- Helios `TabSaldoFA` (saldokonto otevřených faktur) se opírá o **účetní DENÍK**, ne přímo o doklady/banku.
  Důkaz ve struktuře tabulky: sloupce `Saldo_Ucet`/`SaldoCM_Ucet` (saldo z **účtu** = deníkového zápisu)
  + `Castka_MD/Dal_Doklad` (jen zpětná vazba na doklad). `CisloSalSk` = přímo účet **311/321**, `ParovaciZnak` = VS.
- Mechanika: doklad/banka **se zaúčtuje** → vznikne/změní se položka na saldokontním účtu, párovaná přes VS →
  `Saldo = Σ MD − Σ Dal` na daném VS+účtu. Když = 0, faktura je zavřená a ze saldokonta vypadne.
  **Řetěz: Doklad / Banka → zaúčtování → Deník → Saldokonto.**
- Dvě strany: **311 = pohledávky** (vydané FV, oni dluží nám), **321 = závazky** (přijaté FP, dlužíme my).
  Živě 6.7. (EC): 311 = 2 810 otevřených (nominál ~30,3 M, net 3,56 M po dobropisech/zálohách),
  321 = 17 791 (net −2,89 M). Obří rozdíl nominál×net = vzájemně se rušící položky (net > magnituda).
- **Naše platby NEjedou ze saldokonta** — jedou z `oz_pf_platba − oz_uhrady` (naše vlastní saldo, RW). Saldokonto = jen Helios pohled.

**➜ ROZHODNUTÍ (Marti 6.7.): saldokonto Plzně UŽ NEZRCADLIT — číst z PRAHY.** Když saldo = derivát deníku
a začínáme účtovat v **Praze**, tahat saldokonto ze staré Plzně je tahání mrtvého obrazu. Proto:
- Smazány joby `sync_ec_saldo` + `sync_es_saldo` (Plzeň přes MCP), truncate `tenant.ec_saldo_fa` + `es_saldo_fa`.
- **Saldo ČTEME z pražského Heliosu — NEDERIVUJEME ho.** Helios si `TabSaldoFA` počítá sám z deníku; my ho jen
  zrcadlíme. Nové joby **`saldo_praha_ec` / `saldo_praha_es`** (`_sync_saldo_praha`, čtou `UCTO_EC`/`UCTO_ES.dbo.TabSaldoFA`
  přes `db=mssql188`, mód DEL, denně). Zrcadlo míří na `ec_saldo_fa`/`es_saldo_fa` (stejný tvar → `/banka` beze změny).
- **Proč NE ruční derivace z deníku:** zkusil jsem saldo dopočítat z `TabDenik.CastkaZust` (311/321) —
  **divergovalo** od Helios saldokonta (311: 18,6 M vs 3,56 M; jiné počty). Helios má vlastní pravidla
  (skupiny, agregace, párování) → nedohadovat, **nechat počítat Helios**.
- **Teď pražská `TabSaldoFA` = 0** (Helios nakopírovaný deník ještě nepřepočetl) → zrcadlo věrně ukazuje **0**.
  Naplní se samo, až se v Praze začne účtovat naostro (nebo Helios spustí přepočet saldokonta). Ověřeno 6.7.: oba joby OK, 0 řádků.
- Potvrzuje model §2/§3: **deník = jediný zdroj pravdy; saldo, platáky i příznaky jsou jen jeho pohledy.**

## 8. Širší rámec (kontext, ne teď)
Dvoupruhový model (jednoduché firmy u nás vč. DPH / složité EUROSOFT Helios B), budoucí společné
účetnictví s **Martia 2000** pro řadu firem (klient = tenant), daňový poradce = legislativní zdroj pravdy
+ profesní ručení. Detail: `docs/ucetni_engine_parovani_do_deniku_design.md`.

## 9. Související dokumenty
- `docs/prechod_helios_praha_plan_2026-07.md` — plán přechodu (3 týdny).
- `docs/email_martia2000_prechod_2026-07.md` — informace pro účetní (odesláno 5.7.).
- `docs/ucetni_engine_parovani_do_deniku_design.md` — plná vize enginu + konzultace Marti-AI (24.6.).
- `docs/helios_cloud_knowhow_mzdy_ucto.md`, `docs/parovani_banka_objednavky_model.md`.
- Paměť: [[system-c-mzdy]], [[most-ridici-databaze]], [[zrcadla-cloud-helios]], [[kalkulacni-engine-live]].

## 10. Platby / platáky (systém plateb — vzor stará Centrála, Marti 6.7.2026)
Cíl: naučit se platit **„po našem" přes platáky** (platební příkazy). Vzor = funkční systém staré
Centrály nad PF (~15 let, EC_ procedury zvlášť CZK / zvlášť EUR). Odesílat budeme přes naše
**RB Premium API** (`bank_payment_order`), ne starý Gemini export. Učíme se **na PF**, ověříme
**proti staré Centrále**, pak stejný princip na **mzdy** (Helios platák → náš platák).

**Model (stará Centrála):**
- Výběr PF → `EC_Banka_GenTuzemPlatPrikaz` (CZK) / `EC_Banka_GenZahrPlatPrikaz` (EUR) → smyčka faktur,
  kontrola KS → jádro `hp_OZGenPlat_GenerujTuzPlatakCiInkaso`. Dispečer `EC_Banka_GenPlatPrikazy`, návrh
  `EC_Fin_GenNavrhKPlatbe`.
- Tabulky platáku: **`TabPlatTuz`** (hlavička PP), **`TabPlatTuzR`** (řádek: protistrana účet, částka,
  VS/KS/SS, účel), **`TabPlatTuzRDetail`** (detail: `IDDokZbo` = faktura, `IDUhrady` = úhrada).
- Bank. spojení dle měny: `hp_Get_IDBankSpojeni_VlastniOrg_PodleMeny`. Náš účet: `TabBankSpojeni`
  (vlastní org, `Prednastaveno=1`).

**🔑 KDE JE „ZAPLACENO" + POJISTKA PROTI DVOJÍ PLATBĚ (klíčové — nesmí se opomenout):**
- „Zaplaceno" **NENÍ jeden boolean** — je odvozeno ze **salda faktury** (`TabDokladyZbozi.Saldo`) +
  **úhrad** (`TabUhrady`) navázaných na fakturu. Realizace: `Realizovano` + `DatUhrady`.
- **Pojistka:** při generování platáku se **hned vytvoří úhrada** (`hp_OZGenPlat_Uhrada_Nova_Nebo_Oprava`
  → `TabUhrady`, navázaná na fakturu přes `TabPlatTuzRDetail.IDDokZbo`/`IDUhrady`). Částka k platbě =
  `hp_OZGenPlat_CastkaZFakturyProPlatak` = **faktura MÍNUS už existující úhrady**. Když je faktura už
  uhrazená/přeplacená (`@Preplaceno`) → procedura **odmítne a odroluje** (chyba 50072/50241).
  → **Faktura nejde do platáku dvakrát: podruhé je otevřená částka 0.**
- **Dvě vrstvy jistoty:** (1) **platák** = úhrada sníží otevřené saldo hned (měkký zámek „zadáno k platbě");
  (2) **bankovní výpis** = `EC_Banka_AutoParovaniVypisu`/`AutoPrirazeniUhrad` spáruje reálnou platbu →
  potvrdí `Realizovano`/saldo (tvrdé „zaplaceno").
- Navíc příznak **`Nehradit`** na dokladu (nehradit vůbec) — jádro ho kontroluje a přeskočí.

**Návrh k platbě — KTERÉ PF platit (ověřeno naostro 6.7.2026, `EC_Fin_GenNavrhKPlatbe`):**
Filtr na `TabDokladyZbozi` (+ `_EXT`, + `TabCisOrg_EXT`):
- `DruhPohybuZbo BETWEEN 18 AND 19` (PF), `PoradoveCislo>=0`, `Realizovano=1`, **`Saldo>0`** (otevřené),
  `SumaKcPoZao>0`, `Obdobi>22`.
- **NE** `_FinZakaz=1` (finanční zákaz platby, `_EXT`); ne zálohový daňový doklad (řada `52x`).
- **Splatnost:** `GETDATE() >= (Splatnost − ISNULL(_DnyPredPlatbou,5))` — platí se cca **5 dní před splatností**
  (per-dodavatel `TabCisOrg_EXT._DnyPredPlatbou`; Weidmüller CisloOrg=204 + Skonto → +2 dny tolerance).
- Výsledek značí `_EXT._NavrhPlatby=1` (+ `_FinSchvaleni=1`). Řadu dělí `@RadaDokladuPoslCis`.

**🔑 Zálohový daňový doklad (řada `52x`) — VYLOUČIT z návrhu (Marti 6.7.):** stará selekce má podmínku
`RadaDokladu <> CONVERT(int,'52'+@RadaDokladuPoslCis)`, tj. vyloučí řadu **`52x`** = *„Přijatá platba
o zaplacené záloze — daňový doklad"*. Je to doklad **typu PF** (DruhPohybuZbo 18–19) a **má saldo > 0**,
takže by ho návrh jinak vzal — ALE reprezentuje **už zaplacenou zálohu**, ne nový závazek. Kdyby se dostal
do platáku, **zaplatila by se záloha podruhé.** Proto se vylučuje. → V našem `oz_pf_platba` byl kvůli tomu
rozdíl **8 vs 7 CZK** faktur (ta jedna navíc = `52x`). **Náš filtr proto musí přidat `rada NOT LIKE '52%'`**
(přesně `rada <> '52'+cis`), pak je shoda 100 %.
- **Ověřeno 6.7. na živém DB_EC:** k platbě **7 PF CZK (396 296 Kč) + 19 PF EUR** = reprodukce naší selekce sedí na realitu (po vyloučení `52x`).
- **Test zítra (út 7.7. = platební den PF):** spustit náš návrh + EUROSOFT vygeneruje svůj platák → porovnat (stejné faktury? stejná částka=saldo, VS, účet dodavatele?). Realistické ověření „že to funguje".

**Pro NÁŠ systém (závazné):** platák musí replikovat **úhradový zámek** — při generování zapsat úhradu
proti faktuře, částku počítat jako **otevřené saldo**, odmítnout když je pokryto. Ověřit proti staré
Centrále (stejné faktury → stejný platák/saldo). Odeslání přes RB Premium API. **TODO (další dny):**
dostudovat `hp_OZGenPlat_CastkaZFakturyProPlatak` + EUR variantu; postavit náš platák nad PF; ověřit; RB API; pak mzdy.

**Základ „u nás" — stav 6.7.2026 (Marti: „mít u nás TabUhrady a Saldo dokladu"):**
- ✅ **`TabUhrady` → `tenant.oz_uhrady`** (19 344 úhrad / 10 377 faktur). Sloupce: `id`, `id_fak`
  (→ faktura), `doklad_fak`, `datum`, `castka_uhrady`, `castka`, `castka_po_bance`, `mena`, `puvod`,
  `real_uhrada_hm`. Datum ≥ 2024. Auto-refresh přes `oz_sync_all`. = „co je zaplaceno" + pojistka dvojí platby.
- ✅ **Saldo faktur** v `tenant.oz_prij_fa` (`Saldo`, `Realizovano`, `Splatnost`, `CisloOrg`, `Mena`;
  234 otevřených realizovaných PF se saldem > 0).
- ⏳ **Chybí dedikovaný zdroj `oz_pf_platba`** s plným filtrem návrhu k platbě (`_FinZakaz` = fin. zákaz,
  `_DnyPredPlatbou` per dodavatel, `SumaKcPoZao`, `Obdobi`) — ty v `oz_prij_fa` nejsou. Postavit čistě
  z DB_EC (bez sahání do stromového přehledu 2300), pak nad ním stránka **`/platby-navrh`** pro Peťu.

**Doktrína přechodu (Marti 6.7.): pomalu a systémově, napřed data u nás (TabUhrady + Saldo), pak návrh, pak platák.**

**🔴 SMRTELNĚ DŮLEŽITÉ (Marti 6.7.): `Saldo` se NIKDY nezrcadlí z Heliosu do `oz_pf_platba`.**
Zrcadlo se obnovuje **automaticky (oz_sync_all, 10 min)**. Kdybychom v něm drželi Helios `Saldo`, refresh by
nám **PŘEPSAL naše saldo po vygenerování našich platáků** (Helios o naší platbě neví) → rozbila by se pojistka
proti dvojí platbě i věrný obraz. Proto **`saldo` v `oz_pf_platba` NENÍ** a nesmí se tam vrátit. **Saldo je NAŠE,
počítáme si ho sami:** `otevřené_saldo = částka faktury (suma_po_zao / suma_kc) − naše úhrady (oz_uhrady)`
(+ mínus naše čerstvě vygenerované platáky = úhradový zámek). Zrcadlo nese jen **stabilní fakta faktury**
(částka, dodavatel, VS, splatnost, `nehradit`, období, řada…), **NIKDY běžící saldo.** Platí i pro mzdy a další platby.

**🔴🔴 SMRTELNĚ DŮLEŽITÉ — OVĚŘENÍ ČÍSLA ÚČTU PROTI PODVODU (Marti 6.7.2026):**
Peníze musí odejít na **číslo účtu z faktury** (`TabDokladyZbozi.IDBankSpoj` → `TabBankSpojeni`), **ALE NIKDY slepě.**
Před zařazením do platáku se **MUSÍ ověřit, že účet na faktuře odpovídá evidovanému účtu dodavatele.** Důvod:
obrana proti **podvržené faktuře** (BEC / útok „změněné číslo účtu"). Když nesedí → **STOP, nezaplatit, eskalovat člověku.**
Kontrola má tři vrstvy (data v `TabBankSpojeni`):
- **(a) Vlastnictví:** účet z faktury musí patřit **správné organizaci** — `TabBankSpojeni(IDBankSpoj).IDOrg == cislo_org` dodavatele
  na faktuře. (Podvodný účet pod cizí/žádnou org = red flag.)
- **(b) Známý účet:** účet je mezi **evidovanými účty dodavatele** (ne poprvé viděný). Nový/neznámý účet → flag k ručnímu potvrzení.
- **(c) Zveřejněný u správce daně:** `TabBankSpojeni.UcetVSeznamuSpravDane = 1` (+ `DatPoslOverSpravDaneSys/Uziv` = kdy ověřeno).
  Legální opora §109 ZDPH (ručení za DPH při platbě na nezveřejněný účet). Nezveřejněný účet → varovat/blokovat.
**Doktrína: AI/generátor účet jen OVĚŘÍ a označí; při neshodě NEGENERUJE platbu, ale zvedne varování. Platí i pro EUR (IBAN).**
Verifikace = součást Fáze 0/1 platáku (viz `gemini-render-byte-exact`, `platebni-centrum-plataky`).

**🔴🔴 SMRTELNĚ DŮLEŽITÉ — NAŠE VYGENEROVANÉ PLATÁKY NIKDY DO `oz_platak_*` (Marti 6.7.2026):**
`oz_platak_tuz` / `oz_platak_zahr` jsou **DEL zrcadla staré Centrály** (`oz_mirror_def`, mód **DEL** = při každém
`oz_sync_all` ~10 min **truncate + reload ze zdroje** DB_EC/přehledy 2370/2375). Jsou to **jen RO okna do staré
Centrály**, ne úložiště. **Kdybychom do nich zapsali platák vygenerovaný na Cloudu (Praha), nejbližší synk ho SMAŽE**
(zdroj = Centrála, náš cloudový platák tam není → truncate ho vyhodí). To je přesně ta past.
- **Naše vygenerované platáky patří VÝHRADNĚ do vlastních RW tabulek `tenant.bank_platak` + `bank_platak_polozka`** —
  žádné zrcadlo je nesahá, jsou v bezpečí. Generátor (task #44) zapisuje SEM.
- **`oz_platak_*` = jen dočasné legacy okno** do staré Centrály (pro Peťu k porovnání, dokud běží starý svět).
  Po úplném přechodu naostro se **vyřadí**.
- **Záložka Platáky (`/platby`)** musí po spuštění generátoru číst **UNION**: naše `bank_platak` (Praha/Cloud) +
  legacy `oz_platak_*` (Centrála), se štítkem zdroje u řádku. Po cutoveru zůstane jen `bank_platak`. (TODO u #44.)
Stejná logika jako u salda výše: **co je NAŠE, drží se v NAŠICH RW tabulkách, nikdy v DEL zrcadle.**

---

## Changelog rozhodnutí
- **6.7.2026 (Marti):** Model potvrzen — standardní účtování do peněžního deníku, **bez 080**; dva příznaky
  `Zkontrolováno`/`Rozporováno` jako nástroj účetní; deník = rozhraní mezi světy → **příznaky zrcadlit do
  OBOU** (STRATEGIE i Helios); Helios přes **`TabDenik_EXT`** (my ji vytvoříme). Stav Prahy ověřen.
  Znalostní báze `ucto.md` založena + odkaz v CLAUDE.md.
- **6.7.2026 (Platáky):** Rozklíčován systém platáků staré Centrály (CZK/EUR, `hp_OZGenPlat_*`); zapsáno
  „kde je zaplaceno" (saldo + `TabUhrady`) + pojistka proti dvojí platbě (úhradový zámek). Ověřena selekce
  návrhu k platbě naostro (7 CZK + 19 EUR PF k platbě). Nazrcadleno **`oz_uhrady`** (TabUhrady) k nám.
  Cíl: stránka pro Peťu + test út 7.7. (platební den PF).
- **6.7.2026 (Platební centrum LIVE):** stránka **`/platby`** pro Peťu — endpoint `/app/platby/navrh`
  (CZK 8/396 642 Kč + EUR 19/29 991 €, saldo z úhrad) + `/app/platby/vypisy` (60 tx z RB API). Datová
  páteř: `oz_uhrady` + `oz_pf_platba` (+ `suma_val` pro EUR, BEZ Helios salda). Taby Platáky/Importy = roadmap.
  Ověřeno v prohlížeči, 0 JS chyb. Paměť: [[platebni-centrum-plataky]].
- **6.7.2026 (Saldokonto = derivát deníku → přestat zrcadlit):** Ověřeno strukturou `TabSaldoFA`
  (`Saldo_Ucet`+`Castka_*_Doklad`, `CisloSalSk`=311/321) že saldokonto se opírá o **deník**, ne o doklad/banku.
  Řetěz: Doklad/Banka → zaúčtování → Deník → Saldokonto. Marti: zrcadlit Plzeňské saldo při přechodu do Prahy
  je nesmysl → **smazány joby `sync_ec_saldo`/`sync_es_saldo` + truncate `ec_saldo_fa`/`es_saldo_fa`**. Saldo teď
  **ČTEME z pražského `UCTO_EC/ES.TabSaldoFA`** (nové joby `saldo_praha_ec/es`, `_sync_saldo_praha` přes `db=mssql188`) —
  Helios ho počítá, my zrcadlíme. Ruční derivace z `TabDenik.CastkaZust` **zamítnuta** (divergovala od Helios saldokonta).
  Pražská TabSaldoFA je zatím 0 → `/banka` ukazuje 0 (ověřeno). Viz §7b. Předtím opraven i UI módů zrcadel
  (Spustit teď = inline; přeznačení pravdivě). Paměť: [[zrcadla-mody-del-ro-rw]], [[oz-mirror-engine]].
- **6.7.2026 (Plzeňská zrcadla VYPNUTA — spouštět jen cíleně):** Všech **38 `zrc_*`** (office Plzeň → cloud Helios přes
  @@XFER, truncate+reload) **vypnuto** (`enabled=false`) + label označen „· z Plzně". Skupiny: Mzdy 6, Zakázky 4,
  Číselníky 6, Deník a osnova 10, Předkontace 12. **Důvod:** účtujeme v Praze → plzeňské přepisy jsou destruktivní/mrtvé.
  **Mzdy byly aktivně škodlivé** (`TabMzSloz` = pražské spočítané složky přepisované plzeňskými každou hodinu). Ostatní
  (deník/osnova/předkontace/číselníky) se jen zmrazí na plzeňském snímku — cloud přestane dostávat plzeňské změny (záměr).
  Nic se nemaže; „Spustit teď" (inline) je pustí **cíleně** na vyžádání. Kdyby něco šlo potřeba obnovit z Plzně, zapnout
  ten jeden job. **Kalkulace** (EC_Kalkulace*, ne zrc) naopak povýšeny na RO deltu přes přidaný `SystemRowVersion`
  (backfill 39 s → delta 137 ms). Paměť: [[zrcadla-cloud-helios]], [[zrcadla-mody-del-ro-rw]].
- **6.7.2026 (Gemini render HOTOVÝ + byte-exact):** Starý adaptér — TXT Gemini platák — převzat 1:1 z DB_EC procedur
  `EC_Banka_RB_Gemini_Tuz`/`_Zahr`; `scripts/rb/gemini_render.py` (+ spec `gemini_format.md`). **Ověřeno na bajt na VŠECH
  12 vzorcích** EUROSOFTu (6 TUZ + 6 ZAHR, jedna/více plateb, kombinované platáky). Paměť: [[gemini-render-byte-exact]].
- **6.7.2026 (🔴 OVĚŘENÍ ÚČTU — anti-podvod, Marti „klíčové"):** Peníze na účet z faktury (`TabDokladyZbozi.IDBankSpoj`),
  ale VŽDY ověřit proti evidenci: (a) `IDOrg` účtu == dodavatel, (b) známý účet, (c) `UcetVSeznamuSpravDane`=1 (§109 ZDPH).
  Neshoda → NEGENEROVAT platbu, eskalovat. Součást Fáze 0/1 platáku. Detail §10.
- **6.7.2026 (Přehled platáků pro Peťu — záložka LIVE):** V `/platby` nová záložka **🧾 Platáky** — živý přehled
  vygenerovaných platáků z našich zrcadel (přehledy staré Centrály **2370 tuzemské + 2375 zahraniční** →
  `tenant.oz_platak_tuz` + `oz_platak_zahr`). Endpoint **`/app/platby/plataky`** (router.py) = UNION obou tabulek
  per firma, LIMIT 500 nejnovějších, scope **rodiče + Peťa (u18) + cockpit**. UI: chipy **firma (EC/ES) + typ
  (tuz/zahr)**, sloupce Datum/Firma/typ/Odkud/počet faktur/**seznam faktur**/Splatnost/**stav exportu**
  (✓ exportováno / rozpracováno)/Částka + součty per měna — Peťa vidí přesně to, na co je zvyklá z Centrály
  (*„je to zvyklá si kontrolovat, jsou to prachy"*). Data: EC tuz 466 (197,7 M), ES tuz 129 (52,2 M),
  EC zahr 1 380 (2,76 M €). Zrcadlo `oz_platak_*` = **RO** (jen čte Centrálu); od 7.7. platíme my → časem nahradí
  vlastní generátor (task #44/#45). Commit `4cfd7ea`. Paměť: [[platebni-centrum-plataky]].
- **6.7.2026 (🔴 Marti chytil past): naše cloudové platáky NIKDY do `oz_platak_*`.** `oz_platak_tuz/zahr` jsou
  **DEL zrcadla staré Centrály** (truncate+reload z DB_EC při `oz_sync_all`) → platák vygenerovaný na Cloudu (Praha)
  by při dalším synku SMAZAL (zdroj = Centrála, náš tam není). Bezpečný domov = vlastní RW **`tenant.bank_platak` +
  `bank_platak_polozka`** (už existují, žádné zrcadlo je nesahá); generátor (#44) píše sem. Záložka Platáky pak
  UNION `bank_platak` + legacy `oz_platak_*` (štítek zdroje), po cutoveru jen naše. Doktrína zapsána v §10. Detail §10.
