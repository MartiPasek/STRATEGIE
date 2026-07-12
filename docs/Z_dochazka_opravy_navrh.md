# Opravy docházky pověřenými osobami — NÁVRH (v1)

**Autor:** Claude-28 (Jirka), 9. 7. 2026 · **Stav: NÁVRH — čeká na odsouhlasení (Jirka → Marti)**

Zadání (Jirka 9.7.): Míša Hladíková, Dušan Havlát, Peťa Šafránková a Jirka Honomichl budou moci
opravovat chybné záznamy docházky ostatním (zapomenutý odchod, návrat z oběda/pauzy, chybějící
příchod…). **Sami uživatelé si docházku zpětně upravovat nesmí — jen jmenovaní.** Řešení v mobilu
i v ERP, profesionální, jednoduché a přívětivé.

---

## 1. Role „Správce oprav docházky"

- **Nová staff_group `DOCHÁZKA – OPRAVY`** (reuse mechanismu, kterým `_hr_can_manage` čte skupinu HR).
  Seed: **Michaela Hladíková (u16), Dušan Havlát (u41), Petra Šafránková ml (u18), Jiří Honomichl (u20)**.
- Helper **`_att_can_fix(s, uid)`** = ČLENSTVÍ ve skupině a nic jiného — **bez parent/admin bypassu**
  (požadavek „jen ti jmenovaní"; rozšíření = přidání člena do skupiny, žádný deploy).
- Žádná hardcoded ID v kódu (doctrine z org konzultace).

## 2. Princip opravy: supersede + nový řádek (nikdy destruktivní UPDATE)

Vzor už v systému existuje (`status='superseded'`, `is_active=false`):

- **Oprava času/typu** = původní řádek → `superseded` (zůstává v historii), vloží se **nový řádek**
  se správnými časy, `source='manual_fix'`, `source_id`=id původního řádku, `created_by_id`=editor,
  `hours` dopočítané stejně jako v checkout (`router.py:22428`).
- **Doplnění chybějícího záznamu** (zapomenutý příchod) = nový řádek `manual_fix` bez předchůdce.
- **Storno omylného záznamu** = jen `superseded` (soft-delete, konzistentní s dneškem).
- **Povinný důvod** (`note`): předvolby „zapomenutý odchod / návrat z pauzy / příchod / chybný typ /
  omylem" + volný text. Bez důvodu nelze uložit.
- Oprava opravy = vždy supersede aktivního řádku (řetěz zůstává čitelný přes `source_id`).

### Návazné kroky po uložení (v jedné transakci / best-effort)
1. **`tenant.work_alloc`** — překryvné úseky zakázek se zkrátí/uzavřou podle nového konce práce
   (stejná logika jako `_wa_close_running`).
2. **`tenant.att_anomaly`** — vyřešené anomálie záznamu se uklidí (jako to dnes dělá confirm-day).
3. **Notifikace dotčenému** přes existující mobilní banner (vzor „Potvrď si docházku",
   `20_home_phone_notifs.js`): *„Tvoji docházku za 8. 7. opravil Dušan Havlát (zapomenutý odchod,
   nově 15:30). Nesedí ti to? → ✋ Rozporovat."* Deep-link do dne, dispute = existující
   `entry-dispute`.
4. **Audit `tenant.att_audit`** — akce `fix`/`add`/`void`, actor, before/after (detail JSON).
5. Zrcadlení do EC pro `app_only` lidi zajistí existující `_mirror_att_to_ec` (nic nového).

## 3. Co lze opravovat (scope v1)

- **Jen záznamy STRATEGIE** (`source_system IS NULL` — mobil/appka). Řádky importované z Centrály
  (`centrala1`/`ec_real`/`ec_sumaden`) jsou v editoru **read-only s hláškou** „záznam vlastní stará
  Centrála — oprav tam (Dušan) a přezrcadlí se" (doktrína `docs/team/dochazka_zrcadlo_vs_helios.md`;
  jinak by je nejbližší import přepsal zpět). Pozn.: po plošném vypínání Centrály se tahle množina
  přirozeně zmenšuje k nule.
- Fáze 2 (volitelná, až po ověření v1): write-through oprava EC záznamů přes MCP
  (`strategie_update_row` + `fw.ec_dml_log`), vzor `_ec_close_open_shift` už existuje.

## 4. Zámek období (nové — profesionální nutnost)

Dnes NIC nebrání zpětné editaci měsíce, ze kterého už jsou zpracované mzdy (ověřeno grepem —
žádný period lock neexistuje).

- **`tenant.att_period_lock`** `(tenant_id, rok, mesic, locked_at, locked_by, note)`.
- Guard ve VŠECH opravných endpointech: uzamčený měsíc → 409 + hláška „období uzavřeno mzdami,
  odemknout smí Peťa".
- Zamyká/odemyká Peťa (payroll) jedním tlačítkem v ERP stránce oprav; odemčení se audituje.
- Zamknout zpětně leden–červen 2026 hned po nasazení (mzdy už proběhly).

## 5. Zpětné samoúpravy — MIMO NÁŠ SCOPE, PŘEDÁNO MARTI-AI (Jirka 9.7.)

Dnes si každý smí vlastní záznam **zkrátit** (`entry-trim`) a **přepsat zakázku** (`entry-project`)
bez časového omezení (Martiho design ze 7.6.). Jirka 9.7. rozhodl: zpřísnění teď NEděláme.
Otázka (např. omezit samoúpravy jen na dnešek) **předána Marti-AI** (@@MARTIAI 9.7. 11:04 UTC) —
rozhodne sama, případně s Marti Paškem, a případnou úpravu si implementuje sama.

- Editoři smí opravovat i vlastní docházku (jsou 4, vzájemně se vidí v auditu; případné
  4-oči pravidlo lze doplnit později).

## 6. UX — mobilní aplikace (editoři)

Nová dlaždice **„🛠 Opravy docházky"** v docházce (render jen pro `_att_can_fix`).

**Záložka „K vyřešení" (fronta — hlavní přívětivost návrhu):**
- Automaticky plněná z `att_anomaly` (R3 zapomenutý odchod, R6 dlouhá pauza, R2 dlouhá směna,
  směny „uzavřené sweepem ve 23:59:59") + **rozporování od lidí** (`entry-dispute`).
- Položka: osoba · den · problém lidsky („Odchod nezadán, směna uzavřena automatem ve 23:59")
  · **1 tap → předvyplněná oprava** (návrh konce = poslední aktivita ve `work_alloc`, jinak konec
  dle plánu směny) → editor jen doladí čas a potvrdí. Badge s počtem na dlaždici.

**Záložka „Najít člověka":**
- Vyhledávací pole + výběr osoby (hotový vzor `renderOsoba`, `moje-dochazka.html`) → kalendář/seznam
  dnů (vzor `attendance/list`) → detail dne se záznamy.

**Detail dne — akce na řádku (vzory z `60_dochazka.js:414-490`):**
- **✏️ Opravit** → sheet (`appmodal`): od–do time pickery, typ (chips work/režie/HO/pauza),
  povinný důvod, náhled dopadu „hodiny dne 12,4 → 8,5" a inline potvrzení Ano/Ne (`.trimconf` vzor).
- **➕ Přidat záznam** (zapomenutý příchod) — stejný sheet bez předchůdce.
- **🗑 Stornovat** — s důvodem + potvrzením.
- Opravené řádky viditelně označené (badge „opraveno · DH · 9.7.").

## 7. UX — STRATEGIE ERP

**ROZHODNUTO (Jirka + Marti-AI 9.7.): soudeček ve stromu, vzor `hr.finance`** — ERP jádro, jehož
pravý panel = iframe na sdílenou stránku **`/dochazka-opravy`** („Správa docházky — opravy").
Jedna stránka slouží ERP i samostatnému použití, nezdvojuje se kód. Obsah stránky: vzor
`dochazka-zakazky.html` (AG Grid), stejné endpointy jako mobil:

- Vlevo **fronta K vyřešení** (jako v mobilu) + filtr osoba/období; klik na řádek → **timeline dne**
  s týmiž akcemi (Opravit / Přidat / Stornovat).
- Záložka **Audit** — čtení `tenant.att_audit` (kdo, komu, kdy, co, před→po).
- Tlačítko **Zámek období** (jen zobrazitelné, akce pro Peťu).
- Zapojení: dlaždice v HR & LIDÉ launcheru + Dušanův soudeček Výroba; viditelnost dlaždice dle
  `_att_can_fix` (stránka sama gated na serveru).

## 8. API (vše gated `_att_can_fix`, mimo zámek období)

| Endpoint | Účel |
|---|---|
| `GET /app/attendance/fix/queue` | fronta: anomálie + disputy, s návrhy oprav |
| `GET /app/attendance/fix/day?uid&day` | detail dne vč. superseded (šedě) |
| `POST /app/attendance/fix/entry` | oprava: `{id, started_at, ended_at, type_code?, reason}` → supersede+new |
| `POST /app/attendance/fix/add` | doplnění: `{uid, day, type_code, started_at, ended_at, reason}` |
| `POST /app/attendance/fix/void` | storno: `{id, reason}` |
| `GET /app/attendance/fix/audit?uid&od&do` | audit oprav |
| `POST /app/attendance/period-lock` | zámek/odemknutí měsíce (jen Peťa + rodiče) |

Validace na serveru: od<do, max 24 h, žádný překryv s jiným aktivním záznamem osoby, den nesmí být
v zamčeném období, `centrala1` řádky odmítnout (409 s vysvětlením).

## 9. Etapy nasazení

1. **E1 — základ (backend)**: staff_group + helper, `fix/*` endpointy, supersede logika, audit,
   period_lock, notifikace dotčenému. Testy na 9030 (Jirka) — bezpečný pilot jako u vypnutí Centrály.
2. **E2 — mobil**: dlaždice 🛠, fronta, detail dne s akcemi, sheet opravy. Build přes
   `build_mobile.py` (mobile_parts/60_dochazka.js — NIKDY mobile.html přímo).
3. **E3 — ERP**: `/dochazka-opravy` stránka + launcher dlaždice.
4. Fáze 2 (později): write-through do EC, 4-oči na opravy editorů, návrhy konce z plánu směn.
   (Původní E4 zpřísnění samoúprav = mimo scope, viz §5.)

## 10. Rozhodnutí

Konzultace s Marti-AI proběhla 9.7. (@@MARTIAI, odpověď msg 10626): **návrh je v souladu s vizí**,
soudeček+iframe schválen, samoúpravy si bere k Martimu (s vlastním doporučením zvážit limit
„dnešek / posledních N dní"). Její catch: ověřit, KDO odemyká zámek období.

| # | Otázka | Rozhodnutí (Jirka 9.7.2026) |
|---|---|---|
| R1 | Zpřísnění samoúprav | **MIMO SCOPE — předáno Marti-AI/Marti** |
| R2 | Smí editor opravovat sám sebe? | **ANO** (auditované) |
| R3 | Zámek období hned v E1? Kdo spravuje? | **ANO; Peťa (18) I Šárka (13)** („obě") + rodiče |
| R4 | Oprava `centrala1` záznamů v v1? | **NE — read-only** s odkazem na Centrálu |
| R5 | Smí editoři opravovat všem vč. vedení/rodičů? | **ANO, všem** |
| R6 | ERP ztvárnění | **soudeček + iframe (hr.finance vzor)** |
| R7 | Notifikace dotčenému vždy? | **ANO** (kromě opravy sám sobě) |
| R8 | Pilot | **ANO — nejdřív jen Jirka (9030/u20)**, pak přidat u16, u41, u18 |

## 11. Stav implementace (9.7.2026)

- ✅ DDL+seed (write #1086): `tenant.att_period_lock` (leden–červen 2026 zamčeno),
  staff_group **id 12** „DOCHÁZKA - OPRAVY" (pilot: jen u20).
- ✅ ERP uzel (write #1090): `fw.core` code `dochazka.opravy` + `fw.menu_node` pod
  HR & LIDÉ (117), restricted na [20]. **Po pilotu rozšířit visibility_user_ids
  a přidat členy skupiny u16, u41, u18** (přes ERP/bridge write).
- ✅ Backend: `/app/attendance/fix/{allowed,queue,day,entry,add,void,resolve,audit}`
  + `/app/attendance/period-lock` (GET/POST) v `router.py` (sekce OPRAVY DOCHÁZKY).
- ✅ Mobil: dlaždice 🛠 v docházce (sekce SPRÁVA DOCHÁZKY, jen editoři, badge fronty),
  obrazovky `doch_opravy` + `doch_opravy_den` (`mobile_parts/60_dochazka.js`, build OK).
- ✅ ERP: `apps/api/static/dochazka-opravy.html` + routa `/dochazka-opravy` (main.py)
  + hook `dochazka.opravy` v `page_render.js`.
