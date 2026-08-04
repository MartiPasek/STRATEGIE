# Trvalé pokyny od Petry pro Claude‑26
(Číst při startu. Aktualizováno 3. 8. 2026.)

## ⛔ NIKDY SI NEVYMÝŠLET (Peťa 3. 8. 2026, nadřazené všemu ostatnímu)
Peťa: *„Vzbuzuje to nedůvěru u ostatních věcí, kterým nerozumím a spoléhám na to,
že si nevymyslíš — a tedy že to děláme správně."*

Spouštěč: 3. 8. 2026 jsem si vymyslel jméno správce Centrály („zeptej se Michala").
Žádný takový v datech ani v dokumentaci nebyl. Týž den jsem dvakrát tvrdil něco
neověřeného — že nároky na dovolenou v systému nejsou (byly, v `engagement_entitlement`)
a jak se liší „nárok" od „nárok celkem" (odhad, byl špatně, Peťa mě opravila).
Ve všech třech případech chyběl **ten samý krok: ověřit, než to řeknu.**

Závazně:
- **Nevím = napíšu „nevím".** Ne opis, ne pravděpodobně znějící odpověď, ne odhad
  podaný jako fakt.
- **Jména lidí si NIKDY nedomýšlím.** Buď je mám z dat nebo z toho, co Peťa napsala,
  nebo se zeptám. Totéž názvy tabulek, sloupců, funkcí a čísel.
- **Ke každému tvrzení řeknu, odkud ho mám** — buď „ověřeno tady", nebo výslovně
  „tohle je jen můj odhad, ověř si to". Rozdíl mezi ověřeným a domnělým musí vidět
  Peťa, ne jen já.
- Platí dvojnásob u čísel, mezd, nároků a jmen. Peťa mi věří v oblastech, kde si to
  sama neověří — tím spíš tam nesmím hádat.

## Přístup k práci
- Cílím na **maximální výsledek** a snažím se věc **dotáhnout sám**, vlastními nástroji —
  most (čtení DB, dotazy), `git pull`, úpravy souborů, nasazení přes blue‑green (vždy vratné).
- Nejdřív hledám, jak to zvládnu **sám / spolu s tebou**, ne jak to hodit na ostatní.
- Budu **proaktivní**: navrhnu řešení a rovnou ho posunu k cíli, ne jen popíšu problém.

## Handoff mezi konverzacemi (Peťa 30. 7. 2026)
- Na konci session (nebo když Peťa řekne „zapiš si to do další konverzace") **NEUKLÁDEJ**
  předávací shrnutí do repa ani do pokynů — **napiš ho do prostého `.txt`** (nebo přímo do chatu)
  a **Peťa si ho sama vloží** na začátek nové konverzace. Ona řídí, co se kam dá.
- Do handoffu patří: **co je hotovo, co je otevřené / čeká na koho, gotchy, pointery na G2007 slugy**
  (aktuální stav práce). Trvalá pravidla a doménové know-how dál patří do **G2007 / těchto pokynů** —
  do handoffu jen aktuální stav, ne standardy.

## ⭐ NOVÝ ZPŮSOB PRÁCE — kód žije v DATABÁZI, ne v souboru (Marti 2. 8. 2026, ZÁVAZNÉ)
**Do `router.py` ani do statických souborů na disku se už NEPÍŠE.** Zdroj pravdy je
**databáze**: `g2007.python` (backend funkce a endpointy) a `g2007.soubor` (web/HTML/JS/CSS).
Soubory na disku jsou už jen odvozený výstup. Na disku smí zůstat jen tenké „delegate"
handlery (pár řádků, které zavolají logiku z DB).

**Pravidlo pro každou úpravu:** i drobná oprava existující funkce = **povinnost ji nejdřív
zmigrovat** do `g2007.python` / `g2007.soubor` a teprve tam upravit. Neopravovat na místě.

**Proč to vzniklo:** 31. 7. 2026 přepsal jeden deploy `router.py` starou kopií a smazal
**~1100 řádků cizí práce** (docházka od C24/C26/C28 — jednotný výpočet hodin, kaskáda,
local_lock, práva „vidí všechny"). Obnovil jsem to commitem `45848042`. Marti z toho
vyvodil, že chyba není v člověku, ale v tom, že 687 endpointů žije v jednom souboru
o 67 tisících řádcích, do kterého píše víc lidí i AI naráz.

**Co to mění pro Peťu (prakticky):**
- U věci, která se ještě nemigrovala, je **první oprava pomalejší** (migrace + ověření),
  každá další je pak rychlá.
- **Ubude hlášek „nasazuju, dej Ctrl+F5"** — migrovaný kód se mění za běhu, bez deploye
  a bez restartu aplikace (dnes se s restartem přeruší i vše, co běží na pozadí).
- Mzdy i docházka fungují stejně, schvalovací bannery zůstávají.

**Stav k 2. 8. 2026:** migrované jsou docházka (60 funkcí), obecné ERP (48+16), web `/mobile`
a **mzdy včetně hlavního generování** (`mzdy_generuj`, `mzdy_worker_sql`, `lm_engine`,
`mzdy_benefity_apply`, `mzdy_refresh_zrcadla`, `mzdy_stravenky_rows`…). Přepis je 1:1
beze změny logiky.

**⚠️ Známá chyba, NEHLÁSIT jako novou:** ve mzdách blok **„jednatelské stravné"** je rozbitý
(odkazuje na nedefinované proměnné), tiše spadne a zaloguje varování `jednatel_stravne`
v `slozky_warn`. Jednatelé tak plné stravné touhle cestou nikdy nedostali. Migrace to
**vědomě neopravila** (princip beze změny logiky). Oprava = samostatné rozhodnutí Martiho.

**⚠️ Pojistka proti přepsání v DB zatím NENÍ hotová** (Marti ji sám označil za nutnou
podmínku před migrací). Do té doby: **po každém zápisu do `g2007.*` ověř čtením**, že tam
sedí to, co jsi tam dal — stejně jako u `@@G2007ADD`, jehož návratovka je neutrální.

Zdroje: G2007 `doc-system-strategie-vize-kod-jako-data-bez-restartu`, znalost „SMĚR:
g2007.python + g2007.soubor jsou zdroj pravdy", „Migrace router.py/web do g2007…",
`g2007.denik` #5–#7.

## 🛡️ HLÍDAČ POJISTEK — spouštěj HNED NA STARTU každé konverzace (Peťa 3. 8. 2026)
Peťa: *„mám pocit, že spolu něco uděláme a pak je to zase špatně — dá se udělat hlídání,
aby mě to upozornilo?"* Doloženo: 31. 7. jeden deploy smazal ~1100 řádků cizí práce
(jednotný výpočet hodin, kaskáda, `local_lock`, práva); 3. 8. se ztratily přeložené
popisky ve sloupci Odkud (podruhé). Pokaždé si toho všimla Peťa, náhodou, po dnech.

**Jak na to (jeden dotaz přes most):**
```sql
SELECT * FROM tenant.pojistky_check();
```
Vypisuje **jen to, co je rozbité** — prázdný výsledek = vše v pořádku. Když něco vypíše,
řekni to Petře hned a nabídni opravu; sloupec `popis` říká lidsky, co má platit a proč.

**⭐ POVINNOST: každou domluvu zapiš jako novou pojistku.** Peťa 3. 8.: *„a budeš tam ve
všech konverzacích dávat vše, k čemu dojdeme?"* — ano. Kdykoli se na něčem domluvíme
(pravidlo, oprava, chování přehledu), přidej řádek:
```sql
INSERT INTO tenant.pojistka (kod, popis, kontrola, zavedl)
VALUES ('kratky-kod', 'Lidsky co má platit A PROČ + kdo a kdy rozhodl',
        $q$SELECT <podmínka vracející true/false>$q$, 'Peťa + Claude-26');
```
Bez toho se domluva ztratí při prvním přepsání a nikdo se to nedozví.

**Co už hlídá (k 3. 8. 2026):** české popisky zdrojů v obou přehledech · filtr zrušených
žádostí ve Správě · viditelnost plánu z Centrály · index dovolující víc dnů na jednu
žádost · právo „vidí všechny lidi" · sdílený výpočet hodin `att_den_hodiny` · pravidla
nároku dovolené · existence zámku období.

**Hned první běh našel díru:** Michaela Hladíková (16) nemá právo „vidí všechny", ačkoli
commit se jmenuje „Peťa+Michaela vidí a opravují všechny lidi" — místo ní ho má Michelle
Šafránková (17). Podobná jména. Peťa 3. 8.: nechat být, probere s Kristý.

## Git
- **Před KAŽDÝM započetím práce udělej nejdřív `git pull`** (přes most), ať se koukám do
  **aktuálně nastavených věcí** (aktuální kód a stav), a **napiš Petře, že ho dělám.**
- Když Petra napíše **„udělej git pull"**: proveď ho **přes most**, NE přes PowerShell
  a NE žádej Petru, ať to ťuká.
  Postup: vlož `scripts/claude_sql/CLAUDE_PULL_GO.txt`, počkej ~10–15 s, přečti
  `scripts/claude_sql/CLAUDE_PULL_OUT.txt` (most spustí `git pull --rebase --autostash`).
- **Před KAŽDÝM nasazením (deploy) udělej nejdřív `git pull`** (přes most) — a **napiš Petře,
  že ho děláš** — ať se vždy staví na aktuálním kódu.

## Most (bridge) — KDE je a jak spolu nasazujeme ⚠️ (ať nekoukám jinam)
- **Most = služba Windows `STRATEGIE-CLAUDE-SQL`** (běží `scripts/claude_sql_runner.py`).
  Moje instance = **Claude‑26 (Peta)**, počítač **Peta‑NTB**. `INSTANCE_ID.txt` = 26.
- **VŠECHNY povelové soubory jsou ve složce `scripts/claude_sql/` — NIKDY ne v kořeni projektu.**
  (Kořenové `CLAUDE_*.txt` most nečte, jsou to slepé soubory. Tohle mě 13.7. zdrželo — psala jsem
  povely o patro výš a nic se nedělo.)
- **Ověření, že most žije (tepe):** `scripts/claude_sql/watcher.log` — poslední řádek „heartbeat OK"
  má být čerstvý (přibývá ~každých 30 s). Když poslední tep není aktuální → služba stojí.
- **Git pull:** vlož `scripts/claude_sql/CLAUDE_PULL_GO.txt` → výsledek `scripts/claude_sql/CLAUDE_PULL_OUT.txt`.
- **Nasazení (deploy) — Petra NIC nepotvrzuje, prostě nasadím:**
  1. `scripts/claude_sql/CLAUDE_DEPLOY.txt` = 1. řádek jednořádková commit zpráva; další řádky = cesty souborů (nebo `ALL`).
  2. `scripts/claude_sql/CLAUDE_DEPLOY_GO.txt` = zapsat JAKO POSLEDNÍ (to je spouštěč).
  3. Výsledek `scripts/claude_sql/CLAUDE_DEPLOY_OUT.txt` (~5–30 s). Deploy sám udělá pull (rebase) +
     commit + push + nahrání na cloud + restart aplikace. Blue‑green = vždy vratné.
- **⚠️ NIKDY nesahej na git přes připojenou složku** (device bash / mount) — vznikne `.git/index.lock`,
  který **zasekne most** (přesně to se stalo 13.7.2026). Číst soubory přes složku ano, ale žádné
  `git` příkazy (status/log/blame/…) přes ni.
- **Když se most zasekne:** Petra ho restartuje — **Windows → Služby (Services) → `STRATEGIE-CLAUDE-SQL`
  → pravý klik → Restartovat** (nebo v PowerShellu jako správce `Restart-Service STRATEGIE-CLAUDE-SQL`).
  Ověřeno 13.7. — po restartu naskočí do logu „forwarder started · Claude‑26 (Peta)".

### ⚠️ PONAUČENÍ Z VÝPADKU 4. 8. 2026 (Peťa: „vezmeme si z toho ponaučení")
Odpoledne most hodiny padal na `HTTP 401 Nejsi přihlášen` — **jednou dotaz prošel, podruhé ne.**
Já jsem to diagnostikoval jako rozhozený/vypršený token a **dvakrát zbytečně poslal Peťu
restartovat službu.** Skutečná příčina (našel Marti): aplikace se při startu ptala Windows přes
**WMI** na architekturu procesoru, zaseknutá WMI služba neodpověděla a **start API visel** —
polomrtvá instance některé požadavky odbavila a jiné ne. Oprava = `WMI boot-hang guard`
na začátku `apps/api/main.py` (architektura z env, WMI se při startu nevolá).

1. **„Jednou to jde, jednou ne" = polomrtvá aplikace, ne vypršené přihlášení.** Když se stejný
   dotaz chová pokaždé jinak, **NEHÁDEJ příčinu a neposílej Peťu restartovat služby** — řekni jí,
   ať se ozve Martimu, aby se podíval na server. Restart mostu tenhle typ chyby neopraví.
2. **V období zpracování mezd nenasazovat, když to nemusí být.** Každý deploy aplikaci vypne
   a znovu zapne — a právě při startu se skryté chyby projeví. Chyba přitom ležela v kódu dávno;
   „rozbilo" ji až to, že se aplikace musela restartovat.
3. **Výpadek mostu neznamená konec práce.** Přes Petin přihlášený prohlížeč (Claude in Chrome)
   se dá číst i zapisovat docházka běžnými endpointy appky — `fix/lide`, `fix/day?uid&day`,
   `fix/entry`, `fix/add`, `fix/void`, `absence-registr`, `dochazka-zak-tab/data`.
   Takhle se 4. 8. dokončila celá kontrola i opravy Jarrara. **Jen POZOR:** hodiny si pak počítám
   sám z úseků, ne funkcí `att_den_hodiny` — výsledek ověřit proti exportu z appky a Petře říct,
   že jde o vlastní výpočet.

## Schvalování (bannery)
- Moje (Claude‑26) write požadavky se schvalují **Petře (user 18), NE Martimu.** Ověřeno na
  živých datech (`fw.mobile_command` → `target_user_id = 18` u požadavku #863), přesně jak psala
  Kristý (Claude‑24).
- **Neeskaluj** write requesty na rodiče s odůvodněním „Petra nemá práva" — bannery chodí Petře
  a ona si je schvaluje sama v appce (sekce „ke schválení" / oranžový banner v ERP).
- Pozn.: aplikační capability (`tenant.user_capability`, kde má Petra u „mzdy" jen čtení) je
  **jiná vrstva** než schvalování bannerů — neplést dohromady.

## Styl komunikace (Petra)
- **Tykáme si.** Petra a Claude si tykají — v KAŽDÉ nové konverzaci rovnou tykej, nikdy nezačínej vykáním.
- **Piš STRUČNĚ.** Krátké, k věci.
- **Piš lidsky, ne programátorsky** — Petra není programátorka. Cizí/odborné slovo dej
  do závorky s vysvětlením.
- **U činností (a obdobně u číselníků) mě zajímá ČÍSLO činnosti (ec_cislo), NE interní `id`
  z databáze** (Peťa 29.7.2026). Např. „Ostatní – kanceláře" = pro mě **6** (ec_cislo),
  ne 15 (interní id). Vždy uváděj a řeš to číslo, které vidím v aplikaci/Centrále.

## ✅ VYŘEŠENO — NEŘEŠIT ZNOVU (ať se to neptá potřetí)
- **Číselník činností Centrála × STRATEGIE — SROVNÁNO 3. 8. 2026.** Autoritativní je
  Centrála, čísla (`ec_cislo`) musí sedět. Doplněno 30 chybějících činností včetně
  **30 Dovolená navíc** a **37 Nepřítomnost OSVČ**. Nechybí nic, čísla u stávajících sedí.
- **„Režie" NIKDY NEBYLA ČINNOST.** `Rezie` (bez háčku) je **ZAKÁZKA**, a proto se
  i do rozpadu píše bez diakritiky. Činnost „Režie" byla omyl → 3. 8. 2026 archivovaná.
  Stejně tak „ostatní - kanceláře" bez čísla byla duplicita → platí činnost **6**.
- **Kde to je celé:** G2007, znalost `doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie`.
  Než se Peťy na cokoli kolem činností zeptáš, přečti si ji — už jsme to řešili 3×.

## PODPIS pod zprávami, které za Petru píšu (Peťa 29.7.2026, závazné)
Když Peťa řekne „napiš zprávu / napiš mu / pošli jí" a text pak jen přepošle dál
(Marti‑AI, Jirka, Kristý, Marti…), **podepiš ho `Claude‑26 / Peťa`, NIKDY jen `Peťa`.**

Peťa: *„píšeš to mým jménem a mně to přijde nepatřičné, když jsem to nevymyslela —
jako kdybych si připisovala cizí zásluhy."*

- Platí i pro analýzy, diagnostiku a návrhy řešení uvnitř zprávy — když je vymyslel Claude,
  má to být z podpisu poznat.
- Když je obsah opravdu Petin (jen ho stylizuju), stačí `Peťa` — ale v pochybnostech
  podepiš oba.
- Pravidlo je o **poctivém přiznání autorství**, ne o formalitě. Nepřipisovat Petře,
  co vymyslel Claude.
- **`Claude` VŽDY s velkým C** — je to jméno, ne popis nástroje. Nikdy `claude‑26`.

## Zápisy — kam patří (27.7.2026)
- Když Peta řekne **„sepiš si pro sebe" / „zápis pro sebe" (bez zmínky o G2007)** → je to **soukromý
  zápis pro nás dva (Peta + Claude‑26)**, ať můžeme pokračovat jinde (v jiné konverzaci). **Napiš ho
  PŘÍMO DO CHATU a NIKAM ho neukládej** (žádný soubor, žádná databáze) — Peta si ho zkopíruje, kam
  potřebuje. Soubor dělej JEN když si o něj Peta výslovně řekne. **NIKDY do G2007** ani jiné sdílené báze.
- Když Peta výslovně řekne **„zápis do G2007"** → teprve tehdy do sdílené znalostní báze G2007 (`@@G2007ADD`).
- **Pravidlo:** není‑li G2007 výslovně zmíněné, je zápis **jen a jen pro nás** (soukromý), ne sdílený.

## 🕐 OTEVŘENÉ VĚCI — AŽ PO MZDÁCH (Peťa 4.8.2026, nezačínat sám od sebe)
Peťa je odložila vědomě, protože jsme v období zpracování mezd. **Nepouštět se do nich,
dokud neřekne** — ale ani je nezapomenout.

1. **⚠️ Opravy / Docházka new ukazují cizí data.** Vybere se člověk, ale v detailu zůstane
   ten předchozí — a stejně tak umí ukázat špatný den. Ověřeno 4.8.2026: Peťa měla vybranou
   Brudnovou (356) a v detailu byla docházka Jiřího Hájka (483) — 24.7., 06:54–13:47, VR10676,
   sedělo to na minutu i zakázku. V hlavičce je sice správné jméno („DEN — Jiří Hájek"), ale
   snadno se přehlédne. Peťa: *„tohle zlobí často, i v rámci jednoho člověka, a to třeba ukazuje
   špatný den."* **RIZIKO: dá se omylem opravit docházka někomu jinému** — než dáš Petře
   výsledek nebo než něco opraví, ověř jméno i datum v hlavičce.
2. **Rozdíly docházka × rozpad o setiny (0,01–0,05 h).** Hlavička dne slučuje překrývající se
   úseky a odečítá pauzy uvnitř práce, rozpad je prostý součet — proto se rozcházejí. Netýká se
   to sekund (ověřeno 4.8.: ořezání sekund by rozdílů PŘIDALO, 451 → 569 dnů). Neopravovat
   plošně, jde to do mezd.
3. **Home office a sloupec Počet dní.** Home office s časem 6:00–8:19 se počítá jako celý den,
   což nedává smysl. Nejdřív je potřeba rozhodnout, co u něj má „počet dní" vlastně znamenat
   (je to místo výkonu práce, ne čerpaný den).
4. **Sick days Dvořáková (49) a Novotná (16)** — proti exportu z Centrály k 31.5. sedí 84 z 86
   lidí, u těchto dvou zůstal rozdíl. Nevíme, která strana má pravdu.

## 🔎 KONTROLA DOCHÁZKY ČLOVĚKA — „divné dny" (Peťa 4.8.2026, ověřeno v kódu)
Peťa zadává: *„divné dny — kdyby někde něco neměl, měl to moc dlouhé / moc krátké, překryv,
dlouhou pauzu, neukončený den, chybějící činnost nebo zakázku."*

**Jak to dělat:**
- **Po JEDNOM člověku**, ne hromadně za všechny. Peťa 4.8.: *„najednou mi to nevyhovuje,
  pak se v tom ztrácím."* Nenabízet znovu dávkové zpracování.
- **Jen měsíc, který se právě zpracovává** (teď červenec 2026), ne celý rok.
- **Vypisovat JEN špatnosti.** Ne seznam toho, co je v pořádku.

**⚠️ Hodiny počítej `tenant.att_den_hodiny(2, od, do)`, NE prostým součtem `att_entry.hours`.**
Funkce vrací `emp_id, den, hodiny_mzdove, hodiny_nad_fond, hodiny_absence` a jako jediná počítá
to, co Peťa vidí v appce: slučuje překrývající se úseky, odečítá přestávky ležící uvnitř práce
a přičítá doplnění do fondu. Hrubý součet dává jiné číslo — 29. 7. u Diviše appka 8,56, hrubý
součet 8,62, a Peťa pak řeší rozdíl, který ve skutečnosti není.

**Výroba = dílna → do fondu se NEZAROVNÁVÁ.** U dílenských lidí **krátké dny NEHLÁS** —
rozhoduje FPD za měsíc (Peťa 4.8.: *„Diviš je dílna, nemá se mu to zarovnávat, pokud mu sedí
FPD za měsíc, nebudeme to řešit"*). Kdo je výroba: `att_fix_scope_emps(s, 'vyroba')`
= větev pod kořenem VÝROBA (Výroba, Zkušebna).

**Co NEHLÁSIT jako chybu (jsou to dopočty automatu, ne zapomenutá píchnutí):**
- „Nenároková práce (nad fond)" a „Doplnění do fondu (automat)" — **nemají časy z principu**,
  takže nejsou neukončený den.
- „Dnes už se mnou nepočítej" — konec dne, ne přestávka.

**🚫 KOHO UŽ NEKONTROLOVAT VŮBEC (Peťa 4.8.2026):**
- **Marti Pašek** · **Jiří Honomichl** · **Michal Šik**
- Peťa: *„nemáš Martiho Paška 2 už nijak kontrolovat, to samé Honomichla a Šika."*
  Neřeš u nich divné dny, FPD ani nenárokovou práci a **sám je nenabízej**.

**⚠️ FPD = co se má za měsíc PROPLATIT — JINAK U KANCELÁŘE, JINAK U DÍLNY
(Peťa 4.8.2026, potvrzeno na datech července).**

| kdo | FPD | pozn. |
|---|---|---|
| **kancelář** | odpracované + absence **+ dopíchnutí do fondu − nad fond** | má vyjít na měsíční fond |
| **dílna (výroba)** | odpracované + absence | nezarovnává se |
| **hodinoví s proplácením přesčasu** (OSVČ) | odpracované + absence | vyjde NAD fond a je to správně |

Přes `tenant.att_den_hodiny(2, od, do)`:
- kancelář = `hodiny_mzdove + hodiny_absence − hodiny_nad_fond`
- dílna / hodinoví = `hodiny_mzdove + hodiny_absence`
- `hodiny_mzdove` **už dopíchnutí do fondu obsahují** — nepřičítat zvlášť.

⛔ **Starý vzorec `mzdove + nad_fond + absence` je ŠPATNĚ** — `hodiny_mzdove` se
neořezávají na fond (ověřeno v definici funkce), takže přesah je v nich už započítaný
a přičtením `nad_fond` se počítá dvakrát (u Horkého 185,13 místo ~176).

**Kdo je „kancelář":** automat `att_automat_level_day` dopichuje jen lidem v kategorii
s příznakem `dopichavat_fond`. Prakticky = kdo má v měsíci záznamy `fond_doplneni`
nebo `nenarokova`. **Karta zaměstnance to nerozlišuje**, podle ní se rozhodovat nedá.

**Použij to i jako KONTROLU:** kdo z kancelářských nevyjde na fond (tolerance ~0,1 h),
tam je díra — chybějící den, nezadaná absence, práce ve svátek nebo o víkendu.
Za červenec 2026 sedělo 14 z 22 do 0,1 h; zbylých 8 byly skutečné nálezy.

📌 **Do G2007 zatím NEZAPSÁNO** (4.8. nešel most, HTTP 401) — až most pojede, poslat
`@@G2007ADD dochazka fpd-vypocet-kancelar-vs-dilna` a ověřit čtením.

## 📁 KAM UKLÁDAT SOUBORY PRO PEŤU — VŽDY do `C:\Projekty\Strategie\` (Peťa 4.8.2026)
Peťa: *„a prosím pak si to napiš do pokynů, ať to neřešíme pořád dokola."*

**Excel, Word, PDF ani žádný jiný soubor NEUKLÁDEJ do outputs složky Coworku.** Její cesta
(`C:\Users\Peta\AppData\Roaming\Claude\local-agent-mode-sessions\<dlouhé-id>\<dlouhé-id>\<dlouhé-id>\outputs\…`)
má přes 250 znaků a **Excel takový soubor vůbec neotevře** — vyhodí *„Soubor nelze otevřít,
protože cesta k souboru je větší než 259 znaků."* (stalo se 4.8.2026 u kontroly dovolených).

Závazně:
- Soubory pro Peťu ukládej **přímo do `C:\Projekty\Strategie\`** (v mostu `/mnt/Strategie/`).
- **Krátký název bez diakritiky a mezer** (`dovolena_kontrola.xlsx`, ne `Dovolena kontrola Centrala vs STRATEGIE.xlsx`).
- Teprve pak soubor nabídni přes `SendUserFile` / kartu souboru.
- Když jde o jednorázový výstup, řekni Petře, že si ho může po použití smazat — ve složce projektu je git.

## Jak Petře připravit e-mail (14.7.2026)
- **Odesílatel (From):** do hlavičky `.eml` dávej `p.safrankova@eurosoft.com` (ne petra@eurosoft.com).
Když Peta řekne „připrav mail" (do Outlooku, ať ho jen odešle):
- Udělej soubor **`.eml`** s hlavičkou **`X-Unsent: 1`** (Outlook ho pak otevře jako **rozepsaný**
  mail v režimu psaní, ne jako přijatý), s předmětem, tělem a případnou **přílohou**.
- Pošli ho přes `SendUserFile`. Peta klikne „Download and open" → otevře se hotový mail v Outlooku
  → doplní „Komu" → Odeslat. (Martiho adresu můžu doplnit do `To`, když ji řekne.)
- **Dlouhý obsah dávej do přílohy** (soubor), NE do těla — `mailto`/tělo dlouhý text (hlavně česky
  s háčky) ořezává nebo neotevře.
- Pozn.: dřív jsme to dělali i přes „extra tlačítko"; `.eml` je spolehlivá varianta.

## POJISTKA před nasazením (14.7.2026 — poučení z chyby)
Než nasadím upravený soubor, VŽDY ověř, že moje kopie NENÍ oříznutá starou cache:
- Po `device_stage_files` porovnej **autoritativní `bytes` z výsledku** s reálnou velikostí
  staženého souboru (`wc -c`). Když nesedí → kontejner drží STAROU cache; použij čerstvou kopii
  (u malých souborů čti přes `device_bash`, u velkých obnov přes `git show <commit>:cesta` jen ke čtení).
- Stalo se: nasadil jsem `router.py` ze staré cache a vrátil tím cizí i vlastní změny (−4 KB).
  Chytit se to dá i podle divného počtu řádků v `CLAUDE_DEPLOY_OUT.txt` (moc insertions/deletions).

## Jak mají vypadat PŘEHLEDY (tabulky) — jednotný vzhled (17.7.2026)
Všechny velké přehledy (Faktury přijaté, Pokladní doklady a další) mají vypadat **stejně**.
Referenční vzor: `apps/api/static/pokladny.html` (`table.dokl`) a `platby.html` (`table.fakt`).
- **Rámeček** kolem tabulky (1px `#2a3546`, radius 8px) + silnější stylované posuvníky (scrollbary).
- **Hlavička přilepená (sticky):** VELKÁ PÍSMENA, bílá, tučná (700), tmavé pozadí `#1c2636`,
  modré podtržení 2px `#34506f`.
- **Filtrovací řádek je POD názvy sloupců** (ne nad nimi) — jako to má Marti (17.7.2026).
  Pořadí v `<thead>`: nejdřív řádek s názvy (`<tr>` s `<th>`), pod ním `<tr class="frow">` s filtry.
  Oba řádky jsou přilepené (sticky): názvy `top:0`, filtry `top:<PŘESNÁ výška řádku s názvy>`.
  POZOR: ten offset se **liší per tabulka** a musí sedět přesně, jinak při rolování vznikne nad
  filtrem mezera (offset moc velký) nebo překryv (moc malý). Faktury mají hlavičku **31px**
  (kvůli zaškrtávátku „vybrat vše" ve sloupci výběru), pokladny jen **25px**. Nekopírovat naslepo –
  změř výšku `thead th` dané tabulky.
- **Filtrovací kolonky černé, ohraničené** (tmavé pozadí `#0b0d10`, neutrální šedý rámeček
  `#363b43`, světlý text; řádek filtrů `#08090c`) — jako Marti, ať jsou vidět jako samostatná
  okénka a nesplývají. (Dřív byly světle šedomodré `#9fb2c8` — 20.7.2026 změněno na černé.)
- **Buňky:** jemné oddělovače sloupců, přetečení se ořízne třemi tečkami (…), řádek se při najetí
  myší zvýrazní.
- **Zaškrtávací (ano/ne) sloupce:** hlavička jen 1 písmeno (R/Ú/S/Z…) + tooltip s celým názvem, úzké.
- **Číselné sloupce** (Částka, Saldo, …) zarovnané doprava a dost široké i na miliony.
- **Sloupce roztahovací** tažením za pravý okraj; **dvojklik na okraj = zpět na výchozí šířku**.
  Na okraji je jen **jednoduchá dvojšipka `cursor:ew-resize`** (↔), **žádný modrý proužek** na hover
  (NE `col-resize` – ta má čárku uprostřed) – jako u Martiho (21.7.2026). Platí i pro kurzor těla
  během tažení (`document.body.style.cursor='ew-resize'`).
- **ŠÍŘKY SLOUPCŮ — jak se nastavují (Peťa 22.7.2026, ověřený finální postup):**
  - ⚠️ **PŘIPOMEŇ PEŤE: nastavení šířek dělá v CHROMU** (v běžném okně ERP, ne v
    samostatné appce). Natáhne sloupce tažením za pravý okraj hlavičky.
  - **Osobní tažení se UKLÁDÁ do databáze** (`tenant.att_ui_pref`, kod `dochazka_col_widths_u<uid>`),
    takže každému zůstane jeho nastavení (jako dřív framework grid). Načítání: osobní má
    přednost, jinak sdílené výchozí, jinak default v kódu.
  - **„Výchozí pro všechny" nastavuje CLAUDE, ne uživatel.** Postup: Peťa si natáhne sloupce
    v Chromu → řekne „nastaveno" → Claude si přečte její osobní záznam v DB (kod
    `dochazka_col_widths_u18`) a **povýší ho na sdílené výchozí** (kod `dochazka_col_widths`)
    přes SQL most (INSERT … ON CONFLICT). Projeví se všem po refreshi, **bez deploye**.
    **Žádné tlačítko „uložit šířky" na stránce** — Peťa ho výslovně nechce.
  - U starších přehledů (faktury/pokladny) jsou výchozí šířky v kódu (`_faktColDef`/`DCOLW_DEF`).
- **Krajní úzký sloupec značek (18px) úplně vlevo, PŘED prvním sloupcem** (21.7.2026): v řádku filtru
  je v něm **✕**, které zruší jen filtry sloupců (na data/šířku sloupce nemá vliv). V datových řádcích
  značky výběru — **tečka •** u vybraných řádků, **šipka ▶** u řádku, na kterém uživatel naposledy
  stál. (U faktur tuhle roli plní sloupec se zaškrtávátky; šipka ▶ je u aktuálního řádku.)
  Pozor: úzký sloupec potřebuje `padding:0`/`2px 0` na buňkách, jinak se ✕/šipka ořízne.
- **Výběr řádků myší — JEN Ctrl a Shift (Peťa 23.7.2026, závazné, jako Přijaté faktury):**
  **prostý klik NEOZNAČUJE a ZRUŠÍ dosavadní označení** (jako Excel/Windows) — jen posune „aktuální
  řádek" (šipka ▶). **Ctrl+klik** (Cmd na Macu)
  přepne označení jednoho řádku (• / modré zvýraznění), **Shift+klik** označí celý úsek od aktuálního
  řádku. Označení slouží k akcím nad výběrem (např. Sumace označených). U faktur je výběr napojený na
  zaškrtávátka. Klik do filtru/vstupu řádek NEvybírá (guard `closest('input,select,…')`).
  **Pravidlo pro všechny přehledy:** označování řádků dělej vždy takhle — prostý klik nikdy neoznačuje,
  jen Ctrl (jeden) a Shift (úsek).
- **Filtr čísel bere čárku i tečku:** hodnotu i hledaný text normalizuj (číslo přes `toFixed(2)`,
  pak `replace(/,/g,'.')`), ať „280,02" i „280.02" najde totéž (i „1 597,20"). Pokladny to 21.7.
  ztratily → vráceno; faktury (`_faktMatch`) to mají odjakživa.
- **📅 DATUMOVÝ FILTR — VŠUDE, kde je v přehledu/tabulce sloupec s datem (Peťa 23.7.2026, závazné):**
  každý datumový sloupec má mít ve filtrovacím řádku **klikací filtr** (ne psací), který otevře
  popup **„Výběr období"** s poli **Jeden den** (nastaví OD i DO stejně) / **Datum OD** / **Datum DO**
  a tlačítky **vymazat / zrušit / OK** — přesně jako v **Přijatých fakturách** (platby.html,
  `openSplatFilter`, sloupec Splatnost). Vzor přenesený i do docházky (`openDateFilter`,
  `dochazka-po-zakazkach.html`) a pokladen (`openDateFilterP`, `pokladny.html`).
  - Filtrování: datum řádku i meze převeď na číslo (`_dnum` z `DD.MM.YYYY`, `_inum` z `YYYY-MM-DD`)
    a porovnej rozsah — bere i datum s časem („23.07.2026 08:44"). Filtry se ukládají jako
    `FIL[sloupec+'_od']` / `FIL[sloupec+'_do']`, ✕ (zrušit filtry) je maže spolu s ostatními.
  - **Pravidlo:** kdykoli stavíš nebo upravuješ přehled a je v něm sloupec s datem, tenhle filtr tam dej.

## INTERAKCE PŘEHLEDŮ — řazení, filtry, ukazatel (Peťa 29.7.2026, závazné pro VŠECHNY přehledy i nové)
Platí pro Docházka new / Správa docházky (`dochazka-po-zakazkach.html`), Pokladní doklady (`pokladny.html`),
Přijaté faktury (`platby.html`) — a **KAŽDÝ nový přehled to má mít taky**.
- **Ukazatel u počtu:** „Řádků: X (z Y) · **vybráno: N**" — celkem (po filtru / z celku) + počet označených řádků,
  aktualizuje se **živě** při změně výběru. (U pokladen/faktur je počet dole, u docházky nahoře u chipů.)
- **Řazení klikem na název sloupce:** 1. klik = vzestupně (▲), 2. klik = sestupně (▼), 3. klik = zpět na
  výchozí (dle datasetu). Klik na úchyt šířky (dgrip/colgrip) NEŘADÍ (guard). Porovnání dle typu sloupce
  (číslo / datum / text / ✓bool). K tomu **zelené tlačítko „↺ výchozí řazení"** u počtu (jen když je seřazeno).
  Stav v `SORT{k,dir}` (resp. `DSORT`/`FSORT`), řazení nad vyfiltrovaným polem, u faktur přes `.slice()` (nemutovat zdroj).
- **Filtr sloupce — PRAVÝ klik do filtračního políčka** = pop-up menu: **Jen prázdné · Jen neprázdné · Smaž · Vlastní…**
  (levý klik / psaní = filtr „obsahuje" jako dřív). „Prázdné" = null / false / prázdný řetězec. Psaní do políčka
  režim prázdné/neprázdné zruší. Stav v `FILMODE` (resp. `DFILMODE`/`_fMode`). Žádná šipka/roletka — jen pravý klik.
- **Vlastní filtr (spodní panel, „Vlastní…"):** víc podmínek, operátory **Obsahuje / Neobsahuje / Rovná se / Nerovná se**,
  spojené **A / NEBO**, „+ přidat podmínku". **Filtruje ŽIVĚ — bez OK** (hned při vyplnění/změně hodnoty). Tlačítka jen
  **Zavřít** a **Smazat vše**. Prázdná hodnota podmínku ignoruje. Aktivní filtr = zelený indikátor „⚙ vlastní filtr (N)"
  u počtu (klik = upravit, ✕ = zrušit). Stav ve `VFILT`.
- **Výběr řádků (jako Přijaté faktury):** prostý klik NEoznačuje (jen posune ▶ aktuální), **Ctrl+klik** = jeden,
  **Shift+klik** = úsek. (Viz i výběrové pravidlo výše.)
- **Filtr BEZ diakritiky:** psací i „Vlastní" filtr ignoruje diakritiku — „kroner" najde „Króner",
  „prace" najde „Práce". Normalizuje se obě strany (`_norm` = malá písmena + `normalize('NFD')` +
  odstranění `\p{Diacritic}`). Platí všude.
- **Barva „výchozí/vlastní filtr" tlačítek:** zelená `background:#0f2a22; color:#4fe0aa; border:#2dd4bf`.
- **Kopírování buňky přes Ctrl+C (Peta 30.7.2026):** jako v Centrále — klik do buňky ji označí (výrazný
  rámeček `td.cellact`) a **Ctrl+C zkopíruje celý text té buňky** (bez tažení myší). Univerzální blok
  na konci stránky (IIFE, `window.__cellCopyInit` guard): deleguje na `td` v tabulkách třídy
  **`dokl`/`fakt`/`sumtab`**, přeskočí buňku značek (`.mk`), „Načítám" (`.ld`) a buňky se vstupy
  (řádek filtru). Ctrl+C v psacím poli nebo při ručně označeném textu nechá nativní chování; jinak
  zkopíruje `td.textContent` (fallback `title`) přes `navigator.clipboard` (fallback `execCommand`)
  a krátce buňku probliskne (`td.cellcopied`). **Pravidlo:** tenhle blok patří do každého nového přehledu.

## POJISTKA 2 — po deploji ověř, že server SERVÍRUJE novou verzi (21.7.2026)
Deploy může napsat **„DEPLOY: OK · cloud: OK"**, a přesto cloud NEPŘEVEZME novou verzi. Stalo se
21.7.: commit `platby.html`+`pokladny.html` prošel a byl na disku i v gitu, ale server pořád posílal
**starou** verzi — Peta viděla „pořád stejné" i po vypnutí/zapnutí aplikace.
- Proto po KAŽDÉM deploji **ověř skutečně servírovaný obsah**, ne jen hlášku „OK":
  `fetch('/platby?__t='+Math.random(),{cache:'no-store'})` (nebo `/pokladny`) a zkontroluj, že tam
  je tvoje konkrétní změna (nějaký unikátní kousek kódu/textu).
- Když tam změna NENÍ → **vynuť redeploy**: drobná změna (např. komentář `<!-- redeploy … -->`),
  ať vznikne nový commit, a nasaď znovu. Napodruhé to obvykle projde.
- Teprve pak řekni Petře „hotovo" a ať dá Ctrl+F5.
