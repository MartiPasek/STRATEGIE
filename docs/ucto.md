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
- **Ověřeno 6.7. na živém DB_EC:** k platbě **7 PF CZK (396 296 Kč) + 19 PF EUR** = reprodukce naší selekce sedí na realitu.
- **Test zítra (út 7.7. = platební den PF):** spustit náš návrh + EUROSOFT vygeneruje svůj platák → porovnat (stejné faktury? stejná částka=saldo, VS, účet dodavatele?). Realistické ověření „že to funguje".

**Pro NÁŠ systém (závazné):** platák musí replikovat **úhradový zámek** — při generování zapsat úhradu
proti faktuře, částku počítat jako **otevřené saldo**, odmítnout když je pokryto. Ověřit proti staré
Centrále (stejné faktury → stejný platák/saldo). Odeslání přes RB Premium API. **TODO (další dny):**
dostudovat `hp_OZGenPlat_CastkaZFakturyProPlatak` + EUR variantu; postavit náš platák nad PF; ověřit; RB API; pak mzdy.

---

## Changelog rozhodnutí
- **6.7.2026 (Marti):** Model potvrzen — standardní účtování do peněžního deníku, **bez 080**; dva příznaky
  `Zkontrolováno`/`Rozporováno` jako nástroj účetní; deník = rozhraní mezi světy → **příznaky zrcadlit do
  OBOU** (STRATEGIE i Helios); Helios přes **`TabDenik_EXT`** (my ji vytvoříme). Stav Prahy ověřen.
  Znalostní báze `ucto.md` založena + odkaz v CLAUDE.md.
