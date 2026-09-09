# Číselník kontrol docházky — návrh k odsouhlasení

**Stav: NÁVRH, nic nenasazeno.** Připravila C26 (Peťa / Cowork) 29. 7. 2026.
Souvisí s `Kontroly_dochazky_z_Centraly_2026-07-29.md` (analýza a rozhodnutí).
⛔ Čeká se, až Týnka dokončí sloučení `vyroba_work` — nasazení je společné pro celou aplikaci.

---

## 1. Proč

Dnes je šest pravidel napsaných natvrdo v jednom velkém SQL dotazu ve funkci `_att_anomaly_scan()` (`router.py:48859–48995`). Nikde není seznam „co se hlídá", nejde nic vypnout ani přenastavit bez zásahu do kódu a nasazení. Centrála má naproti tomu číselník typů (`EC_Dochazka_ChybyVDochazceTypy`) a limity per člověk (`EC_GlobKonstUziv`) — proto tam šlo zapnout kontrolu svačiny jedinému člověku.

Cíl: **v kódu zůstane jen výpočet, všechno ostatní se dá přenastavit z obrazovky.**

## 2. Návrh tabulek

### `tenant.att_anomaly_rule` — číselník kontrol

| sloupec | typ | k čemu |
|---|---|---|
| `id` | bigserial | |
| `tenant_id` | bigint | multitenant |
| `kod` | varchar | strojový kód, shodný s dnešním `att_anomaly.rule` (`zapomenuty_odchod`…). UNIQUE (tenant_id, kod) |
| `nazev` | text | „Zapomenutý odchod" — co uvidí správce ve frontě |
| `popis` | text | lidsky, co to hlídá (do nápovědy) |
| `aktivni` | bool | zapnuto/vypnuto **bez nasazení** |
| `prah` | numeric | číselná hodnota prahu (12 / 2 / 0.75 …), NULL = pravidlo práh nemá |
| `prah_druh` | varchar | `hodiny` / `minuty` / `podil_uvazku` / `pocet` — aby šlo v UI ukázat správnou jednotku |
| `adresat` | varchar | `spravci` / `spravci_a_zamestnanec` (rozhodnutí Peti 29. 7.) |
| `jen_tydenni` | bool | výjimka „tahle kontrola běží jen v týdenním běhu" (obdoba `@JeDlouhodoba` v Centrále). Výchozí `false` = běží ve všech bězích |
| `okno_dnu` | int | jak daleko zpět se kouká (dnes 14 u nepotvrzeného dne) |
| `poradi` | int | řazení ve frontě oprav |
| `zmenil_id`, `zmeneno` | | kdo a kdy naposledy sáhl — ať je dohledatelné |

### `tenant.att_anomaly_rule_user` — individuální výjimky

| sloupec | k čemu |
|---|---|
| `rule_id`, `employee_id` | koho se výjimka týká |
| `aktivni` | vypnout kontrolu jedinému člověku |
| `prah` | vlastní práh (obdoba `DochKontrolaObedHod` v Centrále) |
| `duvod`, `zmenil_id`, `zmeneno` | proč — ať za rok víme, proč má někdo výjimku |

**Na `att_anomaly` se nesahá.** Zůstává jak je (`tenant_id, employee_id, entry_id, rule, detail, resolved_at` + UNIQUE na `tenant_id, rule, entry_id`). `rule` bude jen nově odpovídat `kod` v číselníku.

## 3. Naplnění — 6 stávajících pravidel (beze změny chování)

Přesně podle dnešního kódu, ověřeno na `router.py:48873–48944`:

| kód | název | dnešní podmínka | práh | četnost | adresát |
|---|---|---|---|---|---|
| `budouci_zaznam` | Záznam v budoucnosti | přítomnost s `entry_date > dnes` | — | denně | správci + zaměstnanec |
| `dlouha_smena` | Dlouhá směna | přítomnost, `hours > 12` | 12 h | denně | správci + zaměstnanec |
| `zapomenuty_odchod` | Zapomenutý odchod | `is_active`, `ended_at` prázdné, `entry_date < dnes`, jen typy `work`/`homeoffice` | — | denně | správci + zaměstnanec |
| `nepotvrzeny_den` | Nepotvrzený den | den s prací bez záznamu v `att_day_confirm` | — | denně, **okno 14 dní** (min. od 6. 6. 2026) | jen dotyčný |
| `prace_pri_absenci` | Práce v den nepřítomnosti | přítomnost v den s absencí ve stavu `pending`/`approved` | — | denně | správci + zaměstnanec |
| `dlouha_pauza` | Dlouhá pauza | typ `break`, `hours > 2` | 2 h | denně, okno 14 dní | správci + zaměstnanec |

Všechna pravidla dnes vylučují importované zdroje `ec_sumaden`, `absence_req`, `centrala1` (u zapomenutého odchodu navíc `import`) — to je **výjimka platná pro všechny**, patří do kódu, ne do číselníku.

**Sloupec `adresat` OVĚŘEN a POTVRZEN Peťou 29. 7.** (kód `router.py:48952–48988`):

- Všechna pravidla kromě jednoho: **zaměstnanec + editoři oprav dle působnosti** (Peťa = kanceláře, Míša + Dušan = výroba; přednost má osobní výjimka v `tenant.att_odpovednost`; když se nikdo nenajde → fallback Jirka `user_id=20`, ať se nález neztratí — Jirka 21. 7.).
- **`nepotvrzeny_den` jde ZÁMĚRNĚ jen dotyčnému** (osobní zodpovědnost, Fáze 1) — správci ne.
- Znění se liší: dotyčný dostane osobní tón („V docházce mám nesrovnalost… napiš mi a opravíme to spolu"), editor věcné „Jméno: co se stalo".

### Adresáti u 6 nových kontrol (rozhodnuto 29. 7.)

| kontrola | zaměstnanec | správci |
|---|---|---|
| Málo hodin | ✅ (zachovat, co lidem chodí dnes z Centrály) | ✅ |
| **Služební cesta (činnost 9)** | ✅ notifikace *„jste se přihlásil na činnost 9 – Služeb.cesta/montáž. Pro tuto činnost je nutné doložit cesťák. Pokud jej nemáte, kontaktujte správce docházky!"* | ✅ |
| Neomluvená absence *(zatím neaktivní)* | ❌ | ✅ |
| Překrytá docházka | ❌ | ✅ |
| Více obědů | ❌ | ✅ |
| Vyhodnocená zakázka | ❌ | ✅ |

⛔ **Úkol do úkolníku NEPŘEBÍRÁME.** Centrála u služební cesty zaměstnanci navíc zakládá úkol (řešitel = on, termín dnes, odhad 0,5 h). Peťa 29. 7.: *„jo tak to nech, samozřejmě kromě toho úkolu do úkolníku."* Vlastní úkolník ve STRATEGII zatím není.

📌 **Notifikace zaměstnanci jen při automatickém běhu.** Centrála posílá lidem jen když `@SpustenaRucne = 0` — při ručním projetí za delší období lidem nechodí nic. **Převzít**, jinak by při měsíční kontrole před výplatami dostali hromadu starých výzev.

## 4. Rozpis tří nových kontrol (přeloženo z Centrály)

### 4.1 Neomluvená absence (Centrála typ 4) — ⏸️ ODLOŽENO, ZALOŽIT JAKO NEAKTIVNÍ

> **Peťa 29. 7. 2026:** *„to budeme muset ještě po výplatách dořešit"* → pravidlo se v číselníku založí s **`aktivni = false`**, aby bylo připravené, ale nic nehlásilo. K rozhodnutí se vrátíme po výplatách (připomínka nastavena na 18. 8. 2026).

**Centrála:** prochází lidi, kteří v pracovní den nemají docházku. Když má jejich činnost zapnuté `DogenerovatDoch`, systém jim docházku **sám dogeneruje** (od 8:00 v délce fondu pracovní doby) — a jinak založí chybu typ 4. Zaměstnanci se **neposílá nic** (zakomentováno: *„Swobi 19.11.2020 — nechceme ukazovat na tabletech"*), jde jen správci.
⚠️ Neověřeno: zdroj kurzoru `CurDopln`, tedy jak přesně Centrála vybírá „lidi bez docházky". Dohledat před stavbou.

**U nás:** pracovní den podle fondu (Po–Pá, mimo svátek), člověk nemá **žádný záznam kategorie přítomnost** a zároveň **žádnou absenci** (podanou ani schválenou). Adresát: **jen správci**. Četnost: denně.
Pozor na kolizi s automatem — dnes `fond_doplneni` prázdný den tiše zaplní. Nález musí vznikat **před** doplněním, jinak nebude co hlásit.

### 4.2 Málo hodin (Centrála typ 3)

**Centrála** (přesná podmínka z procedury):
- jen pracovní den (`@JeVikend = 0` a `@jeSvatek = 0`)
- `CasCelkem` za den **+ náhradní volno (činnost 133)** `< limit` — náhradní volno se přičítá, aby to nehlásilo (Kristýna 27. 3. 2026)
- **a den nesmí mít rozdělaný záznam** (`CasKonec IS NULL`) — jinak by hlásil docházku, která ještě běží
- limit = `ISNULL(DochKontrolaObedHod, 6)` per člověk
- notifikace **zaměstnanci**: *„<datum> jste odpracovali méně než 6 hodin — Kontaktujte svého správce docházky"*, jen když **není** ruční spuštění; správci vždy

**U nás:** stejná logika, ale **limit se počítá z úvazku — 75 % denního úvazku zaokrouhleno dolů na celé hodiny** (rozhodnutí Peti 29. 7.); ruční přepis přes `att_anomaly_rule_user.prah`. Do součtu započítat náhradní volno a **přeskočit dny s otevřeným záznamem**. Adresát: **správci + zaměstnanec** (zachovat, co lidem chodí dnes).

### 4.3 Překrytá docházka (Centrála typ 5)

**Centrála:** vezme všechny záznamy dne z docházky **i z přestávek**, vynechá činnosti s příznakem `NekontrolovatPrekryv` (Kristýna 22. 6. 2023), a hledá dvojice téhož člověka, kde se časy překrývají (`#TMPPrekryta` → `#TMPPrekrytaFinal`). Adresát: **jen správci**.

**U nás:** stejné, nad `att_entry` (přítomnost i přestávky). Dnes máme jen **prevenci při ruční editaci** (`_att_fix_overlap`, `router.py:22516`) — existující překryvy nikdo nehledá. Chybí obdoba příznaku „tuhle činnost nekontrolovat na překryv"; pokud se ukáže potřeba, přidá se do číselníku činností.

## 4b. Rozvrh běhů — ROZHODNUTO (Peťa 29. 7. 2026)

Přebíráme beze změny to, co má Centrála:

| běh | kdy | období |
|---|---|---|
| **denní** | v noci | **předchozí den** (z 28. na 29. 7. → kontroluje se 28. 7.) |
| **týdenní** | v noci **z pondělí na úterý** | **celý předešlý týden Po–Ne včetně víkendu** (z 27. na 28. 7. → dny 20.–26. 7.) |
| **ruční** | na povel | libovolné období — **hlavně na začátku měsíce před výplatami** |

Ruční běh není teorie: v datech Centrály je vidět, že **Dušan 14. 7. 2026 pustil kontrolu za 1.–13. 7.** (`SpustenoRucne = True`). Ve STRATEGII musí jít spustit stejně — tlačítko pro správce docházky s volbou období.

Ve výchozím stavu běží **všechny kontroly ve všech třech bězích**; sloupec `jen_tydenni` je jen výjimka pro pravidla, která nemá smysl řešit den po dni (v Centrále to má jediné pravidlo — typ 22, a to zahazujeme).

## 5. Postup nasazení (až bude volno)

1. Ohlásit práci v `WORK_LOCK.txt`, ověřit, že na docházce nikdo jiný nejede.
2. Založit obě tabulky a naplnit číselník 6 řádky. **Chování aplikace se nemění** — nikdo to nepozná.
3. Přepsat `_att_anomaly_scan()`, aby prahy a `aktivni` bral z číselníku. **Ověření: den před a den po musí dát stejný počet nálezů.** Kdyby ne, hledat proč, ne to zamáznout.
4. Obrazovka na správu číselníku (generovaný přehled + editace).
5. Teprve pak přidávat nová pravidla — už jen jako řádek v číselníku + větev výpočtu.
6. Po sloučení `vyroba_work` doplnit služební cestu (činnost 9) a vyhodnocenou zakázku.

## 6. Co potřebuju od tebe před krokem 2

1. ~~Odsouhlasit sloupce a četnost~~ **HOTOVO 29. 7.** — rozvrh běhů viz kapitola 4b, četnost nahrazena výjimkou `jen_tydenni`.
2. ~~Projít sloupec `adresat`~~ **HOTOVO 29. 7.** — ověřeno v kódu a potvrzeno Peťou, viz kapitola 3.
3. ~~Individuální výjimky~~ **ROZHODNUTO 29. 7.: tabulku `att_anomaly_rule_user` zatím NESTAVĚT.**
   Výjimky v Centrále existují jen jako náplast na pevný limit 6 h. Vzorec „75 % denního úvazku dolů" **vyrobí všech pět dnešních výjimek sám** (20 h → 3 h, 30 h → 4 h, 35 h → 5 h) a navíc opraví 21 lidí, na které se v Centrále zapomnělo. Přidat tabulku jde kdykoli, až se objeví konkrétní člověk, u kterého vzorec nesedí.

   **Místo toho ošetřit chybějící úvazek** (ověřeno v datech 29. 7.): z 206 lidí bez údaje o úvazku má docházku od června **jen 2** — `208 Brigádník Saxana` a `10000 Centrala Centrala` (systémový účet). Zbytek jsou bývalí zaměstnanci.
   - **Bez úvazku → kontrolu „Málo hodin" vůbec nespouštět** (brigádník nemá pevný úvazek; hlásit mu málo hodin je nesmysl). NE náhradní default 6 h.
   - **Systémový účet Centrály vyřadit ze všech docházkových kontrol.**

## 7. Nové k dodělání (vyplynulo 29. 7.)

- **Ruční spuštění kontroly za období** — používá se na začátku měsíce před výplatami.
  Dnes existuje jen ops akce **„Zkontrolovat docházku (anomálie → notifikace)"** (`_OPS_ACTIONS`, `router.py:45514`) — bez volby období a **schovaná pod 🚀 tlačítkem, které je jen pro rodiče**. Peťa ho na své obrazovce nemá (ověřeno screenshotem 29. 7.), takže by tu kontrolu dnes nespustila.
  **Řešení:** nový přepínač **„🔍 Projet kontrolu"** s volbou od–do **přímo v záložce Opravy docházky**, vedle stávajících „K vyřešení / Najít člověka / Historie oprav / Zámek období" — přístupný správcům docházky (Peťa, Dušan), bez vazby na práva rodičů.

  *Poznámka k UI: pravý panel v Opravách docházky už dnes odpovídá „Detailu docházky – chyby" z Centrály — nahoře „Co systému nesedělo" (= Seznam chyb k vybranému dni), uprostřed záznamy dne s Opravit/Storno (= Detail dne), dole Součet dne (= Suma činností). Nové kontroly se jen přidají do horního rámečku.*
