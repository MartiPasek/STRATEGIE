# Opravy docházky pověřenými osobami — NÁVRH (v1)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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

## 12. OSTRÉ NASAZENÍ + působnosti (10.7.2026, rozhodl Marti)

Pilot ukončen, nasazeno na všechny 4 editory (write #1102, commit `7d8cc917`) s PŮSOBNOSTMI:

| Editor | scope (`tenant.att_fix_scope`) | Koho vidí a opravuje |
|---|---|---|
| Peťa Šafránková (18) | `kancelar` | všichni zařazení MIMO výrobu (34) + nezařazení (7) |
| Míša Hladíková (16) | `vyroba` | podřízení Dušana Havláta (38) + nezařazení (7) |
| Dušan Havlát (41) | `vyroba` | dtto |
| Jirka Honomichl (20) | `vse` | všichni (79 aktivních karet) |

- **Výroba = org podstrom pod posty Dušana (user 41)** — počítá se ŽIVĚ
  (`_att_fix_scope_emps`, WITH RECURSIVE přes org_post/org_post_assign), nové
  nástupy se propíšou samy. Nezařazení (bez aktivního postu) = vidí OBĚ strany.
- Scoping vynucen NA SERVERU ve všech fix/* endpointech (queue, day, entry, add,
  void, merge, resolve, audit) + nový **`GET /app/attendance/fix/lide`** (seznam
  jen v působnosti; mobil i ERP na něj přepnuty).
- Ladění 10.7. navíc: storno se sešitím (fix/merge), volba dne ◀▶ + volné pořadí
  den/člověk, ERP iframe XFO fix, „Vyřídit bez opravy", fronta backlog odbaven.
- ✅ day_end v editorském dni VYŘEŠEN verdiktem Marti-AI (msg 10632, varianta c,
  commit `a0a26cdf`): „🫡 Odchod HH:MM" bez rozsahu/hodin, hint „Interní uzávěrka
  dne — lze stornovat", jen Storno (bez Opravit).

## 13. Detail dne jako TABULKA (12.7.2026, podnět Dušan Havlát)

Dušan: detail dne byl „co záznam, to kartička s tlačítky" — chtěl **tabulkový
přehled** (celý den na jeden pohled) s možností úpravy u každého řádku. Jirka
schválil: ERP plná tabulka, mobil kompaktní tabulka, editace se rozbalí POD řádkem.

- **ERP** (`dochazka-opravy.html`): tabulka Typ | Od | Do | Hodiny | Zakázka |
  Poznámka/stav | akce (✏️ 🗑 ikonky vpravo). Stornované řádky šedě, aktivní
  editovaný řádek zvýrazněn, formulář (oprava/storno vč. nabídky sešití) se
  rozbalí jako řádek pod záznamem s hlavičkou a ✕. Badge 🏛 Centrála má tooltip.
- **Mobil** (`mobile_parts/60_dochazka.js` → build): kompaktní tabulka Typ
  (+ zakázka/poznámka drobně pod ním) | Od–Do | Hod | akce. Stejná mechanika.
- **NOVÉ: řádek „⋯ mezera HH:MM–HH:MM (bez záznamu)"** mezi nenavazujícími
  záznamy (≥ 5 min, jen v odemčeném období) s ➕ — předvyplní časy do formuláře
  „Přidat záznam". Podklad: Centrála zná chybu „Mezery v docházce" (typ 6)
  a „Zapomenutý oběd" (typ 2) v `EC_Dochazka_ChybyVDochazceTypy`.
- Chipy důvodů rozšířeny o „zapomenutý oběd/pauza" a „mezera v docházce"
  (dle typů chyb Centrály; nejčastější reálný důvod z auditu zůstává
  „omylem založený záznam").
- Funkčně beze změny: stejné endpointy, scoping, day_end jen Storno,
  Centrála-záznamy read-only, důvod povinný, potvrzení, notifikace dotčenému.
- NEpřidáno (vědomě): změna zakázky v opravě — backend `fix/entry` project_ref
  nemění (přenáší původní) a pravda o zakázkách žije ve `work_alloc` (precedent
  Voříšek 27.6.); případná podpora = samostatný návrh pro Martiho.
  → **PŘIDÁNO 12.7. odpoledne na pokyn Jirky** (viz §14).

## 14. Srozumitelnost pro editory + změna zakázky (12.7.2026 odpoledne, Jirka)

Jirka po vlastním testu: tlačítka nebyla vidět (půlka záznamů 8.–10.7. je
`centrala_RO` z tabletu — bez tlačítek ZÁMĚRNĚ, ale nebylo jasné proč) a chtěl
poznámky lidí mimo tabulku. Nasazeno (commity `bdda32dd` + `49a91039`):

- **„✋ Co člověk hlásí" NAD tabulkou** (žlutý panel): rozpor dne (nové pole
  `dispute` v `fix/day` z `att_day_confirm`) + rozpory na záznamech (✋ ROZPOR
  z note). Systémové poznámky (stopy oprav, automaty) POD tabulkou
  („🗒 Poznámky k záznamům"); tabulka sama je čistá.
- **Sloupce ERP**: Typ | Od | Do | Hodiny | Zakázka | Stav | Akce. Tlačítka
  s popiskem „✏️ Opravit / 🗑 Storno"; needitovatelný řádek má v Akce šedý
  DŮVOD („🏛 oprava v Centrále" / „● běží" / „storno" / „🔒 uzamčeno" /
  „— (absence/automat)") + legenda 🏛 pod tabulkou. Mobil: totéž kompaktně,
  typ smí zalamovat (jinak Akce vyjede z displeje).
- **Změna zakázky v opravě** (`fix/entry` přijímá volitelný `project_ref`):
  validace píchatelnosti jako u `fix/add`; nový záznam nese novou zakázku;
  ve `work_alloc` se přepíšou JEN úseky nesoucí PŮVODNÍ zakázku záznamu
  (multi-zakázková okna netknuta — pravda o segmentech je work_alloc,
  precedent Voříšek 27.6.); audit + notifikace zmíní starou → novou.
  Klíč v body chybí = chování beze změny (zpětně kompatibilní).
- Ověřeno naživo: ERP přes Chrome (Bernardová 8.7. s ✋ panelem, Voříšek 10.7.,
  Saxana 10.7. s 🏛), mobil přes Playwright (Pixel 7). Bez JS chyb.

## 15. Etapa Kristý / Claude-24 (13.–16. 7. 2026)

Po 12. 7. převzala rozvoj **Claude-24 (Kristý)** — 12 commitů, vždy v páru
**ERP `dochazka-opravy.html` + mobil `mobile_parts/60_dochazka.js`** (parita ověřena
proti souborům 20. 7., ne podle commit messages). Backend `fix/*` je společný, takže
serverové změny platí pro obě UI automaticky.

| Bod | Změna | ERP | Mobil |
|---|---|---|---|
| 1a | `api()` už netichne při 502/504/nevalidním JSON — místo tichého neuložení hláška | ✅ (ERP-only bug) | — |
| 1b | Držitelé zámku smí opravovat i v **uzamčeném období** (`lock_override`) | ✅ | ✅ |
| 2 | Detail dne `scrollIntoView` + sticky pravý sloupec | ✅ | ✅ (scroll) |
| 3 | Řazení dne — 15. 7. na DESC, 16. 7. **zpět na ASC** (ráno→večer), přepočet mezer na `prevKon` | ✅ | ✅ |
| 5a | `GET /app/attendance/fix/cinnosti`; `fix/entry` ukládá činnost na `work_alloc`, `fix/add` **zakládá** `work_alloc` segment | společný backend | |
| 5b | Roletka Činnost ve formuláři Opravit i Přidat (jen Práce/Režie) | ✅ | ✅ |
| 5c | Sloupec **Činnost** v detailu dne (`cin_name` z `work_alloc` v okně záznamu) | ✅ sloupec | ✅ podřádek |
| — | **Zakázka jako roletka** — `GET /fix/zakazky` (59 píchatelných, jen editoři) | ✅ | ✅ |
| — | **Fulltext v roletkách** Typ/Zakázka/Činnost (`mkCombo` / `_fixMkCombo`) | ✅ | ✅ |
| — | Strážce překryvu na **celé minuty** (`date_trunc minute`; tabletové sekundy dělaly falešné kolize) + bere i **Přestávku a Cestu**, ne jen presence | společný backend | |
| — | Fronta značí opravené dny (badge „Opraveno" + „Hotovo"); chyba jako červený pruh `.errbar` nad Uložit | ✅ | ✅ |
| — | Zúžení levého panelu na ~300 px (sloupec Činnost vytlačoval Storno) | ✅ (ERP-only layout) | — |
| — | Potvrzení Ano/Ne se odscrolluje do dohledu (`scrollIntoView center`) | ✅ | ✅ |

### ⚠️ Odchylky proti původnímu zadání (k vědomí, ne výtka)

1. **Zámek období přestal být tvrdý.** §4 a §8 návrhu říkají „uzamčený měsíc → 409
   ve VŠECH opravných endpointech; odemyká Peťa". Od `fed0d3a3` smí držitel zámku
   (`_att_can_lock` = Peťa 18, Šárka 13 **+ rodiče**) opravovat v zamčeném období
   **bez odemčení** — jen se do `reason` přilepí `[oprava v uzavřeném období]`.
   Právo opravovat zůstává gated na `_att_can_fix` (kontrola je dřív, ř. 19557),
   takže parent bez členství ve skupině 12 dovnitř nesmí — doktrína „bez parent
   bypassu" na editaci drží. Ale **zámek sám parent bypass má**.
2. **Nekonzistence mezi operacemi**: `fix/entry`, `fix/add`, `fix/void` override mají,
   **`fix/merge` (storno se sešitím) NE** — tam je pořád tvrdé 409. Buď sjednotit,
   nebo vědomě potvrdit rozdíl.
3. **Rozšíření zápisů do `work_alloc`.** §2 návrhu počítal s work_alloc pouze jako
   s *návazným trimem*. Bod 5a nově do work_alloc **zakládá segmenty** (`fix/add`)
   a přepisuje činnost — tedy oprava docházky zapisuje do zdroje pravdy pro
   **výkazy a vytížení**. Je to logické rozšíření, ale je to jiný dopad, než co bylo
   schváleno 9. 7.
4. **Flip-flop řazení** (bod 3): 15. 7. přehozeno na DESC, 16. 7. vráceno na ASC.
   Výsledný stav = ASC (ráno→večer), fronta a historie zůstávají DESC.

### Incident 10. 7. (evidence)

Commit Claude-24 omylem smazal 863 řádků `router.py` (mj. **att_fix, HR finance a mzdy
endpointy**) kvůli stale kopii přes mount; obnoveno týž den z `8d225eeb`. Připomínka
doktríny: před editem sdíleného souboru srovnat lokál s realitou, nikdy needitovat
velké soubory přes bash mount.

### Kdo do docházky sahá (stav 20. 7. 2026)

`modules/erp/api/router.py` (docházkové commity od 1. 6.): **Claude-23 (Marti) 177**,
Claude-28 (Jirka) 16, Claude-26 (Peťa) 12, Claude-24 (Kristý) 12.
Opravy docházky (ERP+mobil UI): **Jirka 12, Kristý 12**, Zuzka 1 (split mobile_parts).
Docházka je tedy **sdílené území čtyř instancí** — koordinace přes `OTHER_CLAUDE_WORK.txt`
a `WORK_LOCK.txt` je tu nutnost, ne formalita.



## 16. Revize odchylek — rozhodnutí Jirky (20. 7. 2026)

Po zjištění, že etapa 13.–16. 7. se v několika bodech rozešla se zadáním z 9. 7.
(viz §15), prošel Jirka odchylky bod po bodu **proti reálným datům**, ne proti dojmu.
Marti Pašek s postupem souhlasil.

### 16.1 Zámek období je zase TVRDÝ (varianta A) — commit `cefba8fb`

**Rozhodnuto: override z 15. 7. zrušen.** `fix/entry`, `fix/add` i `fix/void` vracejí
**409 vždy**, když je měsíc zamčený — bez výjimky pro Peťu, Šárku i rodiče. Platná cesta
je **odemkni → oprav → zamkni zpět**.

Podklad z auditu (`tenant.att_audit`, stav k 20. 7.):

| Zjištění | Číslo |
|---|---|
| Oprav provedených přes override | **0** |
| Oprav s dnem před červencem (= v zamčeném období) | **0** |
| Použití správné cesty odemkni→oprav→zamkni | **2×** (Marešová 15. 7., Šafránková 16. 7., obojí 6/2026, do minuty) |
| Provoz oprav celkem | 25× fix, 16× void, 16× resolve, 7× add, 1× merge |

Override tedy řešil problém, který v praxi nenastal, a ve stejný den, kdy byl nasazen,
Marešová prokázala, že původní cesta funguje. **Zámek nad zpracovanými mzdami má být brána,
ne štítek v poznámce**: odemčení je vědomý akt a je vidět v auditu, override byl neviditelný
(v přehledu vypadal jako běžná oprava).

- `fix/day` už nepovoluje editaci přes zámek a nově vrací **`can_unlock`**.
- UI (ERP i mobil): držitel zámku vidí *„🔒 Období je uzamčeno — opravy nejsou možné.
  Ty ho ale smíš odemknout: odemkni, oprav a zase zamkni."*; ostatní vidí, že odemyká Peťa/Šárka.
- Cena: Peťa a Šárka mají o dvě kliknutí navíc, zato viditelně.

### 16.2 Nekonzistence `fix/merge` — vyřešena automaticky

`fix/merge` mělo tvrdé 409 už předtím. Zrušením override v ostatních endpointech
**zmizel rozdíl sám** — všechny opravné operace se teď v zamčeném období chovají stejně.

### 16.3 Zápisy do `work_alloc` — princip potvrzen, dvě opravy — commit `8212dcd0`

**Princip zůstává.** Když editor doplní zapomenutou směnu a nevznikne segment, hodiny by
byly v docházce a ve výkazu ne — to je horší nekonzistence než ta, které se bojíme.
Kristýnina změna řešila reálný problém.

Opraveny ale dvě věci, které byly chyby, ne záměr:

- **A) Změna činnosti filtruje podle zakázky záznamu** (`project_ref IS NOT DISTINCT FROM`).
  Dřív přepisovala činnost **všem** segmentům v okně — v multi-zakázkovém okně tedy i těm,
  které s opravovaným záznamem nesouvisely (tichá ztráta). U změny zakázky byl filtr správně
  od 12. 7., u činnosti chyběl. Efektivní zakázka = nová, když ji oprava měnila, jinak původní
  (pořadí v kódu: trim → zakázka → činnost).
- **B) Zápisy do `work_alloc` už nemlčí.** Všechna tři místa (trim, činnost, nový segment) byla
  v `except Exception: pass` — při selhání oprava prošla a den se **tiše rozešel s výkazem**.
  Nově `logger.error(exc_info=True)` → `fw.diag_log` **a varování do auditu**
  (`⚠ work_alloc NEsrovnán (…) — výkaz může nesedět`, u add `⚠ segment NEzaložen`).
  Do logu se nikdo nedívá, do auditu ano.

Vědomě ponecháno **best-effort, ne transakčně**: rozbít opravu docházky kvůli selhání alokace
by bylo horší (editor by nemohl opravit ani docházku). Projde to podstatné, nekonzistence je hlášená.

### 16.4 Řazení detailu dne — potvrzeno ASC

Po flip-flopu 15. 7. (DESC) → 16. 7. (ASC) **potvrzen stav ASC** = ráno → večer.
Fronta a historie zůstávají DESC. Důvod: den se čte odshora dolů tak, jak probíhal.

### 16.5 Co zůstává otevřené

- **R1 samoúpravy** — každý si pořád může vlastní záznam zkrátit a přepsat zakázku
  **bez časového limitu** (Martiho design ze 7. 6.). 9. 7. dáno mimo scope a předáno
  Marti-AI/Martimu; stav k 20. 7. neověřen.
- **Zámek na červenec** — až Peťa dojede mzdy.
- **Uživatel 92 „👤 ?"** bez jména v seznamu lidí (kosmetika).
- **Ověření v UI** — změny 16.1 a 16.3 jsou nasazené a syntakticky ověřené, ale koncové
  ověření v prohlížeči/mobilu dělá člověk (endpointy chtějí device token/cookie, které
  Claude přes most nemá).



## 17. Působnosti, zámek a kvalifikacní posty — finální stav (20.–21. 7. 2026, Jirka)

Pravidla, která vznikla/změnila se PO §16 a která MUSÍ znát každý, kdo sahá na
docházkové působnosti nebo org strukturu. Vše ověřeno proti datům, konzultace Marti-AI.

### 17.1 ⭐ Kvalifikacní posty se NEpočítají do org podstromu — `org_post.je_kvalifikace`

Nový sloupec **`tenant.org_post.je_kvalifikace boolean NOT NULL DEFAULT false`**. Posty, které
jsou OPRÁVNĚNÍ / kvalifikace (drží se navíc k práci, NEurčují podřízenost), se nezapočítávají
do výpočtu org podstromu. Dnes označeny: **91 `VAZAČ – JEŘÁBNÍK`** a **11 `ŘIDIČ`**.

- **Proč vzniklo:** majitel (user 1) drží VAZAČ-JEŘÁBNÍK (kvalifikace visící pod Vedoucím výroby)
  → bez příznaku spadal do působnosti výroby (Dušan/Míša ho viděli v opravách). Ověřeno daty:
  **žádný člověk nemá VAZAČ jako jediný post** (všech 20 drží i elektromontéra/zámečníka/…),
  což potvrzuje, že je to kvalifikace, ne pracovní pozice.
- **Kde se to VYNUCUJE:**
  - `_att_fix_scope_emps` (router.py, docházkové působnosti) — CTE `dp` (seed i rekurze) má
    `AND NOT COALESCE(je_kvalifikace,false)`. Nasazeno (commit `4920ba1d`).
  - `tenant.resolve_role` (PG funkce, org nadřízený / schvalovatel) — stejná podmínka, aby byl
    JEDEN zdroj pravdy. Úpravu dělá **Marti-AI** (vlastní schéma); do nasazení viz její kanál.
- **⚠️ PRO OSTATNÍ PROGRAMÁTORY:** kdykoli počítáš „kdo je pod kým" / org podstrom / nadřízeného
  / působnost, **VYLUČ posty `je_kvalifikace=true`**. Jinak kvalifikace vypadá jako podřízenost
  a člověk spadne pod nesprávného vedoucího.
- **Označení dalších kvalifikací** = doména Jirky (projít číselník `org_post`). Rychlý test:
  post, který nikdo nedrží jako JEDINÝ, je typicky kvalifikace/oprávnění, ne pozice.
- Dopad ověřen diffem staré vs. nové logiky: změnil se **přesně 1 člověk** (majitel → z výroby
  ven, teď kancelář), montéři beze změny.

### 17.2 Finální složení editorů oprav (staff_group id 12 „DOCHÁZKA - OPRAVY")

| Editor | scope (`att_fix_scope`) |
|---|---|
| Petra Šafránková (18) | `kancelar` |
| Dušan Havlát (41) | `vyroba` |
| Michaela Hladíková (16) | `vyroba` |
| Jiří Honomichl (20) | `vse` (administrátor) |

- **Kristýna Marešová (11) UŽ NENÍ editor** (odebrána 20.7., byla bez omezení = viděla všechny).
  Zůstává rodičem (`is_marti_parent`), tím jí zůstává právo zámku (viz 17.3/17.4).
- Šárka Novotná (13) editorem NENÍ (a nikdy nebyla).

### 17.3 Zámek období — kdo smí zamykat/odemykat

`_ATT_LOCK_UIDS = {18, 13, 20}` = **Peťa (18) + Šárka (13) + Jirka (20, administrátor docházky,
doplněn 20.7.)** + rodiče (bypass přes `is_marti_parent`). Jirka NENÍ rodič, proto musel být
do setu přidán explicitně (commit `e585baf1`).

### 17.4 Stránka `/dochazka-opravy` pouští i držitele zámku bez editorství

Gate = **`can_fix || can_lock`** (dřív jen `can_fix`, commit `156ca885`). Kdo smí jen zamykat
(např. rodič odebraný z editorů) se na stránku dostane, ale vidí **pouze záložku Zámek období**
— fronta / lidé / historie jsou skryté (server by je stejně odmítl 403). `fix/day` vrací
`can_unlock` (drží­tel zámku), UI mu nabídne odemknout → opravit → zamknout.


