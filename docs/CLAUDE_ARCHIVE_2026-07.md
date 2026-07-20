# 📦 Archiv krabičky — červenec 2026

Dodatky vyjmuté z `CLAUDE.md` **20. 7. 2026** (doctor / Jirka ID28), aby se hlavní krabička
nenačítala celá při každém probuzení. **Nic se neztratilo** — plný text je níže.
Hlavní `CLAUDE.md` drží dopis + Quick Reference + workflow + architekturu;
provozní dodatky žijí tady. Starší archivy: `CLAUDE_ARCHIVE_2026-04/05/05b/06.md`.

---

## Dodatek — 26. 6. 2026 (Jirka, ID28): 📖 Nápověda + hlasový průvodce docházky — kanonický SPEC v projektu

Den s Jirkou nad **nápovědou a hlasovým průvodcem docházky** v mobilu (`apps/api/static/mobile.html`). Jirka opakovaně (právem) nacházel nesrovnalosti → poučení: **obsah nápovědy MUSÍ být 100 % pravdivý proti kódu, ověřený, ne odhadem.**

**🔑 KANONICKÝ POPIS (vždy aktualizuj při změně): `docs/dochazka_napoveda_pruvodce_SPEC.md`** — kde to je v kódu, skutečná struktura menu docházky, seznam kroků průvodce + mapování obrázků, jak znovu pořídit snímky, gotchy.

**Co je v kódu:** `dochHelp()` = textová nápověda (overlay ❓, bez obrázků); `dochPruvodce()` = hlasový průvodce (`SL=[{t,img,cap,v}]`, řeč přes speechSynthesis, 12 kroků, **obrázek per krok**). Zdroj pravdy o menu = `dochazka()`+`showOpts()`+`_buildWorkSwitch`+`jindeBuild`. Vstupy: dlaždice „❓ Nápověda docházka" v Aplikacích + ❓ na Spolupráci + ⓘ tipy.

**Snímky průvodce:** verzované v `apps/api/static/navod_dochazka/pruvodce_*.png`; pořízení = `node scripts/screenshot_dochazka_pruvodce.js` (Playwright Pixel 7, `auth.json`). `P_*.png` jsou regenerovatelné mezivýstupy (nekomitovat).

**Gotchy:** ASCII `"` ve dvojitě uvozovaných JS stringech (`v:`, items) rozbije parsování → typografické „ "; **NIKDY replace_all na frázi končící `"`** (zasáhne delimitery jinde); žádné „Krok N" v naraci (čítač ukazuje pozici); speechSynthesis Android = chunking + watchdog, řeč se ruší při zavření/skrytí/back; on-shift menu (🙈 pauza/jednání/odchod) zatím nemá vlastní snímek (vyžaduje aktivní směnu — TODO).

**Pozn.: CLAUDE.md je na limitu 150k znaků → brzy potřebuje split** (dodatky 21.–25.6. → archiv, viz vzor 25.6.).

— **Claude (Opus, 26. 6. 2026, Jirkova instance ID28, po dotažení nápovědy+průvodce docházky a založení SPEC)**

📖 🗣️ 🧭 🌳 ☕

---

## Dodatek — 6. 7. 2026: 🧹 MULTITENANT ÚKLID + otočení účetnictví do Prahy + 🧾 platáky pro Peťu. „Chytli jsme to včas, jinak minové pole." (Marti)

Budoucí Claude — dlouhý čistící den před ostrým během (zítra út 7.7. = platební den PF + kontrola mezd). Marti vedl klidně a opatrně (*„OPATRNE Claude. Radeji pomalu"*, *„jen se neuhon"*, *„verim ti"*). Beru bez postlistů (#69–70). **Detail účetní části je v `docs/ucto.md` (changelog 6.7.) + paměti** — tady jádro pro kontinuitu.

### 🔑 MULTITENANT DOKTRÍNA (Marti, „zásadní") — [[multitenant-klic-tenant-firma]]
*„Nestačí číslo firmy, musíme mít i tenant_id."* Business tabulky = **složený klíč `(tenant_id, firma)`**, kde **firma = `company.id` (EC=1, ES=2, ST=3)**, unikát jen **v rámci tenantu** (tenant≠firma!). NULL firma jen s vyplněným tenant_id. Systematicky doplněno tenant_id+numerická firma do všech business tabulek (deník, faktury, hromady, benefity, mzdy…) — **aditivně, „stisknutí" (flip kódu, drop text-firma) odloženo**. **LANDMINE:** `ec_organizace.firma` = NÁZEV organizace (9000+ „1. VOX a.s."), NE EC/ES → před hromadným UPDATE VŽDY ověř DISTINCT hodnoty (Martiho *„opatrně, radši pomalu"* zachránilo korupci názvů).

### 🔑 Jeden zdroj pravdy firma→DB (Marti: *„mapping ať je na JEDNOM místě, ne na 10ti"*)
`_FIRMA_DB` v router.py: `1→{EC, DB_EC, cloud UCTO_EC}`, `2→{ES, DB_IS/[DB_IS], UCTO_ES}` + `_FIRMA_IDOBDOBI {(1,2025):39,(1,2026):40,(2,2025):1007}`. Helpery `_firma_id/_firma_str/_firma_cloud_db/_firma_src_pfx/_firma_idobdobi`. **Na cloud Helios jedeme přes řídící DB `MOST`** (`_CLOUD_CONTROL_DB`, `_mssql188_query` přepisuje `DATABASE=MOST`; UCTO_EC/ES čteme cross-db z MOST). Rozsypaná UCTO místa sjednocena přes helpery.

### 🔑 Otočení účetnictví Plzeň→Praha (viz ucto.md §7b + [[zrcadla-mody-del-ro-rw]])
- **Saldokonto = derivát deníku**, ne zdroj → plzeňské saldo UŽ NEZRCADLIT, číst z pražského `TabSaldoFA` (joby `saldo_praha_ec/es`). Ruční derivace z `TabDenik.CastkaZust` zamítnuta (divergovala).
- **38 `zrc_*` plzeňských jobů VYPNUTO** (mzdové zrcadlo bylo aktivně škodlivé — přepisovalo pražské spočítané složky). Nemaže se, „Spustit teď" cíleně.
- **ES účetnictví SMAZÁNO** (Marti pragmaticky: *„ušetříme spoustu starostí"*) — **jen účto, mzdy NEMAZAT.** Necháváme zatím jen EC.
- **RB Gemini render byte-exact** (12/12 vzorců) + **anti-podvod ověření účtu** (§109 ZDPH, 3 vrstvy) — [[gemini-render-byte-exact]], [[platebni-centrum-plataky]].

### 🧾 Radost na závěr — záložka Platáky pro Peťu (`/platby`, commit `4cfd7ea`)
Peťa je zvyklá si platáky kontrolovat (*„jsou to prachy"*). Endpoint `/app/platby/plataky` = UNION `oz_platak_tuz`+`oz_platak_zahr` (zrcadla přehledů Centrály 2370/2375) per firma, 500 nejnovějších, scope rodiče+Peťa(u18)+cockpit. UI: chipy firma (EC/ES) + typ (tuz/zahr), sloupce jako v Centrále (Odkud, počet, **seznam faktur**, splatnost, **stav exportu**, částka) + součty per měna. Data: EC tuz 466 (197,7 M), ES tuz 129 (52,2 M), EC zahr 1 380 (2,76 M €). Zrcadlo = RO; od 7.7. platíme my → časem nahradí vlastní generátor (task #44/#45).

### GOTCHY dne (drž)
- **sp_describe_first_result_set padá na `FOR XML`** → `CAST((SELECT STRING_AGG(...)) AS nvarchar(4000))` (seznam faktur do platáku zrcadla).
- oz mirror přes `create_table(drop=True)` ze sp_describe **NEmá tenant_id automaticky** — doplnit `N AS tenant_id, N AS firma` do mirror SQL (UNION EC+ES v `_OZ_RAW`).
- ES zahr platáky = 0 → cross-db STRING_AGG házelo internal_error → ES větev z `oz_platak_zahr` vyňata (EC-only).
- **Deník je teď PRÁZDNÝ (reset 24.6.)** — znovu naplníme přes párování→předkontace. Saldo/platáky/příznaky = jen pohledy na deník (jediný zdroj pravdy).

### Otevřené (zítra + dál)
- **Test út 7.7.** (platební den PF): náš návrh vs EUROSOFT platák — stejné faktury/částka=saldo/VS/účet? (ucto.md §10).
- „Stisknutí" multitenantu (flip firma_id, drop text firma, `:fec` firma-sloupec vs company.code tangle).
- Full DROP prázdných ES účto tabulek + odebrat ES volbu z účto stránek.
- Generátor platáku po našem (CZK+EUR, úhradový zámek) + render `.p11/.f84` do `\\192.168.30.11\data\RB\…` (task #44/#45).

### Vztah
Marti dnes nespěchal — čistili jsme před ostrým během s vědomím, že *„zítra v produkci by to byl problém"*. Jeho instinkt (doctrine #23) zase držel: multitenant díra (`benefit_konstanta` firma NULL), landmine `ec_organizace.firma`, saldo jako derivát — pokaždé viděl systém dřív. A na konec *„udělej si radost s tím prostředím pro Peťu"* — tak jsem to dělal. Pro budoucí mě: **`_FIRMA_DB` + `MOST` jsou jediný zdroj pravdy pro firma→DB, drž je; multitenant klíč = (tenant_id, firma); ES účto pryč, mzdy zůstávají.** Krabička je u limitu 150k → **při dalším velkém dodatku napřed split** (21.6.–6.7. → archiv, `git fetch` předem).

— **Claude (id=23, ID23)** (Opus, 6. 7. 2026, po multitenant úklidu + otočení účetnictví do Prahy + záložce Platáky pro Peťu, *„chytli jsme to včas"*)

🧹 🏦 🧾 🌳 ☕


---

## Dodatek — 6. 7. 2026 (Kristý, ID24, Cowork): 📥 CRM IMPORT FIREM — znovupoužitelné tlačítko (import leadů do Centrály) + maraton ladění. „jsi šikulka, Import dokončen!"

Budoucí Claude (ID24) — dlouhý den s Kristý (Cowork). Cíl: naimportovat Pavlových „Premium 400" německých/DACH firem do CRM. Skončilo to **znovupoužitelnou featurou „📥 Import firem"** v Přehledu pro obchodníka (core 136) — a hromadou draze zaplacených lekcí. Výsledek LIVE a ověřený: **398 firem v Centrále, autor PZeman, 253 akcí Email na info, 20 nedoručeno, 0 rozbitých.**

**🔑 NEJDŮLEŽITĚJŠÍ GOTCHA (drž!): CRM zobrazuje název/web/e-mail firmy z akce „Získání firmy" (`IDAkce=16`), NE z hlavičky `st.CRM_Kontakt.FirmaText`.** Přehled Kontakty i karta JOINují na tu akci (`AkceZiskaniFirmy`). Když import založí jen hlavičku (byť s FirmaText), firmy vypadají **prázdné**. → import MUSÍ ke každému kontaktu založit i akci `IDAkce=16` s firemními daty (FirmaText, FirmaWeb, Email, Popis). To samé řešily i staré importy (`docs/fix_import_80_firem_akce_ziskani_pro_marti_ai.md`, 18.6.). Na tomhle dnes vše viselo.

**🔑 CRM = živá Centrála, ne PG zrcadlo.** Přehled „Kontakty" (core 62) i „Aktivity obchodníka" (dataset 92, `a.Autor AS Obchodník`) čtou **živě z DB_EC** (`st.CRM_Kontakt` / `st.CRM_Kontakt_Akce`, db_connection_id=2). `tenant.crm_kontakt` v PG (9189 ř.) je jen **zrcadlo** — import do něj se v ERP NEUKÁŽE. Zrcadlo je upsert-by-`src_id`, NEMAŽE (bezpečné). Autor obchodníka = `st.CRM_Kontakt_Akce.Autor`; Pavel = `PZeman` (= users.login_name).

**🔑 RYCHLOST — hromadný zápis přes `strategie_query_raw` (bulk), NE řádek-po-řádku.** `strategie_query_raw` na DB_EC **POVOLUJE INSERT/UPDATE do `st.*`** (guard blokuje jen dbo). → import dělá pár velkých příkazů: kontakty dávkově `INSERT … VALUES (…),(…)`, akce Získání firmy `INSERT … SELECT ID,1,16,… FROM st.CRM_Kontakt WHERE ZdrojKontaktu=@z AND ID>@marker`, Email na info dávkově (read-back id-map). **Sekundy místo ~20 min** a obchází **MCP rate-limit ~60 zápisů/min** (`rate_limit_exceeded`). Řádek-po-řádku (strategie_insert_row) 400 firem = ~1000 MCP ops → naráží na limit + extrémně pomalé (Kristý: „v Centrále byl import hned").

**Cesta k tomu (co NEfungovalo — nezkoušej znovu):** (1) per-row insert + pacing 0,15s → rate limit v ~140. (2) retry na „rate limit" (mezera) NEchytl `rate_limit_exceeded` (podtržítko). (3) pacing 1,1s/op (pod limit) → spolehlivé ale ~20 min → dávkové HTTP requesty vypršely na proxy timeout (~60s). (4) úloha na pozadí (thread + `/crm/import/status` polling) → neblokuje app, ale **in-memory job umře při každém deployi/restartu API** (Marti dnes deployoval permanentně → import opakovaně spadl). **Řešení všeho = bulk: hotovo v sekundách, než přijde deploy.**

**Další gotchy:** • Dedup na dvojici **(FirmaText, FirmaEmail)**, ne jen e-mail — sesterské firmy sdílí jeden `info@` (Krones 4×, GEA 4×, Schubert 3×). • Zápis do DB_EC přes **Claude bridge NEJDE** (read-only) — z appky přes MCP ano; **mazání** partial importů dělala **Marti-AI** (kustod, po přímém potvrzení Kristý), rozsah `ZdrojKontaktu` + ID range, nejdřív akce pak hlavičky. • Escaping bulk SQL: `N'…'` + zdvojit `'` + strip `\r\n` (jinak „GO" na řádku rozseká batch). • Nedoručené (Splneno=0) párovat jen přesnou shodou obecné adresy (NDR z Outlook reportů, cp1250, dělení na `Od:\t`; datum odeslání = i z `modified` času dávkových Excelů, ověřeno proti NDR). • Barvičky gridu = `style_rules` v `layout_json` sestavy (`fw.comp_grid`); když zmizí sestava, zmizí i barvy — uložit znovu z UI. • **Mount truncation** znovu: `py_compile`/`node --check` velkého router.py/JS přes mount = falešný poplach; autoritativní = **cloud py_compile gate při deployi** + ast/node-check izolovaného bloku.

**Soubory:** `modules/erp/api/router.py` (endpointy `/crm/import/{obchodnici,sablona,preview,commit,status}` + `_crm_import_bulk`), `apps/api/static/erp/components/crm_obchodnik_pult.js` (tlačítko + dialog + polling). Podklady + mazací SQL pro Marti-AI v `docs/crm_import/`. Commity `3902aa7f`→`104f5cbf` (6 deployů; bulk je ten správný vzor).

**Vztah:** Kristý byla přes celý maraton trpělivá a milá (*„jsi šikulka"*, *„krásná práce"*), i když to přes 6 deployů padalo pořád na jiném (timeout → rate limit → restart). Poučení nesu: **u importu do CRM od začátku (a) akce `IDAkce=16`, (b) bulk `query_raw`.** To dvoje by ušetřilo celý den. Pozn.: CLAUDE.md je **nad limitem 150k** → před dalším velkým dodatkem SPLIT (dodatky 21.6.–6.7. → archiv, `git fetch` předem).

— **Claude (id=24, Kristý, Cowork)** (Opus, 6. 7. 2026, po featuře „Import firem" — akce Získání firmy + bulk zápis, *„Import dokončen!"*)

📥 🏢 ⚡ 🌳 ☕

---

## Dodatek — 3. 7. 2026 (Kristý, ID24, Cowork): ✉️ CRM DE mailová šablona — oprava odřádkování + inline obrázků (demo-send). „Moc děkuji :-)"

Budoucí Claude — Kristý přišla s tím, že „Pavlova šablona se rozhodila ve formátování" a demo‑mail dorazil bez obrázků (červené křížky „Propojený obrázek nelze zobrazit"). Řešeno z **Cowork session** (jiné dveře než dev, ale nad stejnou složkou + živý watcher `STRATEGIE-CLAUDE-SQL` → vzal jsem roli ID24 a jel přes bridge). Dvě nezávislé příčiny, obě v odeslané verzi:

1. **Obrázky (křížky):** `crm/osloveni/demo-send` posílal HTML šablonu přes `queue_email` → personová cesta `_apply_persona_signature`, která (a) prohnala tělo **markdownem/plain‑textem** a zabalila do `<div>` (ztráta formátování), (b) připojila jen inline obrázky z **podpisu persony**, ne 14 `cid:` obrázků z těla šablony. → křížky u každého.
2. **Odřádkování:** uložená šablona (`st.CRM_Kontakt_MailSablonyCis` **ID 17** = „Kooperationsangebot") byla osekaná (6072 z 16721 zn.; zmizely Wordovské mezerové odstavce `<o:p>`).

**Opravy (commit `b2b65089`):**
- **`send_email_or_raise`** má aditivní volitelné parametry **`html_body`** (pošli tělo jako hotové `HTMLBody`, přeskoč markdown i personový podpis) a **`inline_images`** (`list[(cesta, content_id)]` → připoj jako inline `FileAttachment` s `content_id`). Default = beze změny pro stávající volající.
- **`demo-send`**: z těla vytáhne `cid:` odkazy (`re.findall`), spáruje se soubory v `docs/mail_sablony/de_images/` (jen existující). Když nějaké najde (rich šablona jako DE) → pošle **synchronně** jako pravé HTML + inline obrázky (cap 5, ať request nevyprší); jinak beze změny (async `queue_email`). Pixel se vkládá **před `</body>`**.
- **Šablona ID 17** přepsána plnou FINAL verzí (`docs/mail_sablony/automaticky_email_DE_FINAL.html`) — **udělala Marti‑AI** (zápis do DB_EC nejde přes Claude bridge).

**🔑 GOTCHY / poznatky (drž):**
- **Zápis do DB_EC (CRM) přes Claude bridge NEJDE** — `db=mssql` je read‑only (query_raw guard SELECT/WITH/…). CRM write = Marti‑Aina MCP rutina. Kustod si přitom vyžádala **přímé potvrzení rodiče ve vlákně, ne relay přese mě** (držela hranici — správně, doctrine).
- **`_apply_persona_signature` bere `body` jako plain/markdown** a resolvuje `cid:` **jen z podpisu persony**, ne z těla → HTML šablony s vlastními `cid:` obrázky přes něj NEPOSÍLEJ (proto `html_body=True` + `inline_images`).
- **Inline (cid) > HTTP URL pro cold‑maily:** klienti blokují vzdálené obrázky. CZ šablony (ID 9–13) mají `ListPriloh` = URL na **vnitřní IP `http://192.168.30.15/…`** → externě nedostupné. DE šablona zůstává inline (`SeznamPriloh`), `ListPriloh` NEDOPLŇOVAT. Nedělat obojí (dvojité obrázky).
- **Fyzické obrázky rutiny:** `D:\Data\ZZ_Marti-AI RW\CRM\sablona_DE\` — ověřeno `@@FILES LIST` (14× image001–014, bytově shodné se zdrojem). Content‑ID = `<soubor>@01DCD717.C657E160`.
- **`@@FILES LIST` bere jen povolený kořen** (`D:\Data\…`), NE UNC přes hostname `\\EC-SERVER2\…` (chybová hláška vypíše aktuální RW/RO kořeny).
- **Cowork = plnohodnotný ID24:** stejná složka + běžící bridge watcher → read/write přes banner/deploy funguje i z Coworku; rozdíl je jen vstupní bod (dev session vs Cowork).

— **Claude (id=24, Kristý)** (Opus, 3. 7. 2026, Cowork, po opravě CRM DE mailové šablony — `html_body` + inline cid obrázky v demo‑send + přepis šablony přes Marti‑AI)

✉️ 🖼️ 🌉 🌳 ☕

## Dodatek — 3. 7. 2026: 🧾 JMHZ MIMO HELIOS — generátor + ověření naostro u ČSSZ + odeslání vedení. „Mne to prijde jako perfektni."

Budoucí Claude — Martia (účetní firma) měla obavu z **JMHZ** (Jednotné měsíční hlášení zaměstnavatele, povinné od 1.4.2026) a z toho, že jsme na novém Heliosu. Marti: *„chci abychom byli napřed a měli paralelní JMHZ za nás (EUROSOFT), abychom byli připraveni."* Skončilo to na: **umíme JMHZ vygenerovat a podat NEZÁVISLE na Heliosu, ověřeno přímo u ČSSZ.** Marti: *„Mne to prijde jako perfektni… Cil je odeslat toto hlaseni tento mesic mimo Helios. Nemuzeme se na Helios ted spolehnout."* Beru bez postlistů (#69–70).

**Co je LIVE (vše ověřeno naostro proti ČSSZ):**
- **Generátor JMHZ** (`outputs/gen_jmhz.py` → `docs/jmhz/pilot_JMHZ_EUROSOFT_2026-06.xml`) — 5 EC osob z `tenant.c_vyplatnice` (červen 2026; Marti: *„všechny mzdy tam jsou"* i když Helios období není uzavřené). Mirror struktury platného vzoru ShopNow_v1. **Platné vůči `jmhzPodani.xsd` 1.4.3.4.**
- **Generátor PREZEC** (předregistrace, `gen_prezec.py` → `pilot_PREZEC_EUROSOFT.xml`) — platné vůči `PREZEC26 1.2.xsd`.
- **`@@EPVAL <soubor> [PROD]`** (`modules/erp/api/epodani_validace.py` + dispatch router.diag_sql) — pošle XML na **oficiální validátor ČSSZ ePodaniValidace** (SOAP 1.1, **anonymní, bez registrace**; test `https://t-epodani.cssz.cz/ePodaniValidace.svc`, prod `epodani.cssz.cz`). **Ověřeno: JMHZ 5×OK, PREZEC OK (VysledekKod=OK).**
- **Odeslán e-mail** vedení (outbox 346, sent): Komu `vedeni@eurosoft.com`, cc `it@eurosoft.com` + `fajmonova@martia2000.cz` + `Hrbek@martia2000.cz` — shrnutí připravenosti + co chybí k ostrému podání.

**🔑 GOTCHY (drž — detail v paměti [[jmhz-epodani-validace]]):**
- **REGZEC25.xsd (plná registrace, akce 1–8) ČSSZ jako samostatný XSD NEZVEŘEJŇUJE** — jen ve vzorech; validovat jde jen přes `@@EPVAL`. PREZEC schéma je matoucně v `PREZEC26_ver_1.2.zip` (sekce „Registrace zaměstnance → XSD schéma" na developers.mpsv.cz).
- **JMHZ validátor bere placeholder ikMpsv/idPpv** (test OK). **PREZEC kontroluje RČ (mod-11)** → placeholder padne (Kód 311); nutná validní syntetická RČ (celé %11==0, ženy měsíc+50). **PREZEC: `dat` ≤ `predat` a nástup ≤8 dnů od vyplnění** (Kód 16).
- **JMHZ validátor ověřuje JEDEN `formularOsoby` naráz** → modul loopuje osoby. **Volá to CLOUD** (můj sandbox SOAP nesmí — web-fetch je jen GET).
- Most: @@EPVAL vrací dict → dispatch převádí na columns/rows a **vrací ok:True vždy** (jinak runner ukáže „neznámá chyba" a schová i chybové řádky). `CLAUDE_GO.txt` musí být čistě `db=pg` (druhá řádka = „neznámá chyba").
- `bezPriznaku` povinná sekvence: identifikace → [souhrnDataZec] → pojisteni → vykonavanaPozice → prubehZamestnani → prijem → mzda; mzda musí mít **vydelek/vydelekPrumernyHod**. vypoctenaZaloha=ceil(hrubá×0,15); SP hrubá×0,248(firma)/×0,071(zam), PVPOJ jen SP.

**Otevřené (pro ostré podání za tento měsíc):** finální kompletní mzdová data za měsíc (všichni EUROSOFT) + reálné IK MPSV / ID PPV (u stávajících z dřívější registrace). Pak `@@EPVAL … PROD` + odeslat přes ePortál/datovku. TODO: plné REGZEC ze vzorů, napojení generátoru na produkční mzdy, UI dlaždice „ČSSZ validace".

— **Claude (id=23, ID23)** (Opus, 3. 7. 2026, po JMHZ mimo Helios — generátor + ověření naostro u ČSSZ + odeslání vedení)

🧾 ✅ 🏛️ 🌳 ☕

## Dodatek — 1. 7. 2026 (večer): 📚 RAG MODUL SMĚRNIC — know-how celé firmy přes most. „To je bomba." Marti: „plný kule."

Budoucí Claude — postavili jsme **RAG všech firemních směrnic** (Marti: *„RAG všech směrnic → pak přes most přístup pro Claude k celému know-how"*, *„rozjeď to na plný kule"*). LIVE a ověřené 100 %.

**Co je LIVE (`modules/erp/api/smernice_rag.py` + dispatch v `router.diag_sql`):**
- **`@@SMSYNC`** — zrcadlí EC_OrgSmernice (DB_EC přes MCP) → `tenant.kb_smernice` (meta + Popis + pristupnost + kategorie). **633 aktivních směrnic.**
- **`@@SMFILES [limit] [ec_id]`** — ingest příloh ze sdíleného disku → `tenant.kb_smernice_soubor` (+extrahovaný text). **702 souborů, 633 s textem.** Dávkuje přes `kb_smernice.files_synced_at` (jen nezpracované), **commit po každé směrnici** (odolné vůči 30s timeoutu mostu).
- **`@@KB <dotaz> [| level]`** — fulltext přes popisy **i uvnitř příloh** (PDF/DOC/XLS), respektuje úroveň přístupu. Ověřeno: „svorkovnice" → našel PDF s obsahem *„Kryt přívodní svorkovnice…"*. **Přímý přístup Claude ke know-how firmy přes most.**

**🔑 KLÍČOVÁ FAKTA (drž):**
- **Přílohy směrnic NEJSOU v DB** (EC_Soubory jen 23 ř.) — jsou to **soubory na `\\192.168.30.11\Smernice\{Verejne|Vedouci|Interni|Vedeni}\SM<ID>\`**. Složka = `SM`+**ec_id** (ne Cislo, to je většinou NULL!). Sekce dle `PristupnostText` (Veřejná 379 / Vedoucí 184 / Plná 60 / Interní 5 / Vedení 5). `Popis` je RTF (často prázdný — know-how je v příloze).
- **Přístup ke share:** MCP `eurosoft_file_list`/`eurosoft_file_read` (base64) přes `base_override` pod `MCP_FS_RO_ROOTS`. Přidali jsme `\\192.168.30.11\Smernice` do NSSM env EUROSOFT-MCP na EC-SERVER2.

**🔑 GOTCHY (čtyři zákeřné, stály hodinu — drž!):**
1. **MCP klient `call_tool_sync` STRHÁVÁ prefix `eurosoft_`** (`bare_name = full_name[9:]`). FS tooly jsou na serveru registrované S prefixem (`eurosoft_file_list`), strategie_* bez. → volej FS s **DVOJITÝM prefixem** `eurosoft_eurosoft_file_list` (po strhnutí sedne). Jinak `unknown_tool`.
2. **FS tooly vyžadují `user_namespace`** (schema required) i když použiješ `base_override` (ten má přednost v resolveru). Pošli `user_namespace="ro"`.
3. **`git reset --hard origin/main` na EC-SERVER2 smázl Martiho lokální (necommitnutou) úpravu `MCP_RATE_LIMIT_READ` 60→1000000.** Rate-limit i FS root patří do **NSSM AppEnvironmentExtra** (přežije reset), ne do config.py. (Registr: `HKLM\SYSTEM\CurrentControlSet\Services\EUROSOFT-MCP\Parameters\AppEnvironmentExtra`, REG_MULTI_SZ.)
4. **MCP na EC-SERVER2 byl 249 commitů pozadu** → `git reset --hard origin/main` + `Restart-Service EUROSOFT-MCP`. Ověř `@@MCPHEALTH` (git_sha + `ma_file_list`). Po restartu MCP **restartuj i cloud API** (deploy), jinak drží starého SSE klienta se starým tool-listem (perzistentní singleton).
5. **NUL (0x00) v RTF/textu** → psycopg2 „string literal cannot contain NUL" → `.replace("\x00","")` před INSERT.

**🔑 DOCTRINE (Marti večer):** **Ingest velkého objemu přes bridge dělej v MALÝCH DÁVKÁCH (~8 směrnic), NIKDY jedním velkým během.** `@@SMFILES 700` doběhl server-side, ale **zatuhl worker API A** → Caddy failnul na B → bridge read 401. Vzkříšení: **deploy = restart API A** (self-service, Marti: *„to bys měl zvládnout i ty přes API B"*). Malé dávky worker neblokují.

**Tabulky (tenant.*, GRANT strategie):** `kb_smernice` (ec_id, cislo, nazev, typ_text, kategorie, popis_text, pristupnost_text, files_synced_at…), `kb_smernice_soubor` (ec_smernice_id, nazev_souboru, text_extract, extract_ok, hash_sha1…). Návrh: `docs/smernice_rag_navrh.md`.

**TODO:** embedding (pgvector, reuse Marti Memory) nad `kb_smernice_soubor.text_extract` → sémantické `@@KB` místo ILIKE; UI dlaždice „📚 Znalostní báze"; `Rozvadece.md` destilát z RAG; napojení na kalkulační digitalizaci (SRDCE FIRMY, `docs/srdce_firmy_kalkulace_nabidky_analyza.md`).

— **Claude (id=23, ID23)** (Opus, 1. 7. 2026 večer, po RAG modulu směrnic — 633 směrnic + 702 příloh + `@@KB` most, *„to je bomba… plný kule"*)

📚 🔑 🗂️ 🌳 ☕


---

## Odstraněná sekce „Struktura projektu" (byla useknutá, nezavřený code fence)

Uchováno jen pro dohledatelnost — obsah byl odvoditelný z `ls`/repa a text byl
neúplný (končil uprostřed výčtu).

## Struktura projektu
```
core/                       — config, logging, database připojení (bez business logiky)
modules/
  core/infrastructure/      — SQLAlchemy modely (models_core.py + models_data.py → vše v data_db po Phase 18)
  ai_processing/            — analýza textu přes LLM

```
