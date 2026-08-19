# Návrh — proč nesedí docházka a rozpad, a jak to srovnat

**Pro:** Kristý → ke konzultaci s Péťou
**Od:** Claude‑24
**Datum:** 17. 8. 2026
**Navazuje na:** předání „Docházka × rozpad na zakázky" (Peťa / Claude‑26, 17. 8. 2026)

Všechno níže je **ověřené v kódu a v datech**, ne odhad. Kde si nejsem jistá, je to
označené. **Nic jsem neměnila** — je to podklad k rozhodnutí.

---

## Jak to dnes funguje (jednou větou)

Docházka (`att_entry`) je **hlavička** — od kdy do kdy byl člověk v práci.
Rozpad (`vyroba_work`) jsou **položky** — na jaké zakázce ten čas strávil.
Položky jsou navěšené na hlavičku (`att_entry_id`). Součet položek by měl dát hodiny
hlavičky. Nedává — a jsou pro to **tři různé důvody**, které je potřeba řešit každý zvlášť.

---

## Vada č. 1 — hodiny v hlavičce neodpovídají časům v téže hlavičce

**Co se děje.** V databázi je hlídač (trigger `trg_att_entry_round_minutes`), který u každého
zápisu docházky **ořízne časy na celé minuty** — sekundy zahodí. Sloupec `hours` ale
nepřepočítá. A ten se v aplikaci počítá z přesného času **včetně sekund**.

Takže v jednom řádku docházky je „od 8:30 do 8:41" (= 11 minut), ale v hodinách je uloženo
0,20 h (= 12 minut). Položka rozpadu počítá z těch oříznutých časů, tedy 11 minut. Rozdíl je
malý, ale **vzniká u každého píchnutí a vždy stejným směrem** — docházka je vždy o kousek
vyšší.

**Jak je to velké (ověřeno v datech).**

| | |
|---|---|
| Záznamů 10.–14. 8. | 866 |
| Z toho se sekundami v časech | **0** (trigger je opravdu ořízne všechny) |
| Rozdíl na jeden záznam | −0,003 až **+0,020 h** (prakticky vždy plus) |
| Součet za firmu | **+1,1 až +1,5 h každý den** |
| Součet za 1.–14. 8. | **+8,63 h** z 3 574,9 h (0,24 %) |

**Proč je to důležitější než kontrolní přehled.** Druhý databázový hlídač
(`att_entry_resummary`) sčítá tenhle sloupec `hours` do denního souhrnu
(`att_day_summary.cas_celkem`) — a to je podklad, ze kterého se dělají **mzdy**.
Takže těch +8,63 h za půl měsíce není jen kosmetika v přehledu; teče to do mzdového zrcadla.
*(Že `att_day_summary` slouží mzdám, vím z historie projektu — vazbu na konkrétní mzdový
výpočet jsem teď neověřovala, to bych chtěla potvrdit s Péťou nebo Jirkou.)*

**Návrh řešení — tři varianty.**

- **A (doporučeno) — hodiny se počítají z uložených časů, na jednom místě.**
  Trigger, který už časy ořezává, ať rovnou dopočítá i `hours` (konec − začátek − přestávka).
  Pak nemůže nastat, že hodiny neodpovídají časům, ať zápis přijde odkudkoli (appka, opravy,
  notifikace, import). **Háček:** ne každý řádek docházky má hodiny odvozené z časů — absence,
  doplnění do fondu a některé importy je plní jinak. Trigger by proto musel platit **jen pro
  typy záznamů, kde hodiny opravdu znamenají „odpracovaný čas"** (work / homeoffice / overhead).
  Tohle je rozhodnutí, ne technikálie — musí ho potvrdit Péťa a Marti.
- **B — opravit každý výpočet v aplikaci zvlášť** (aby počítal z oříznutého času).
  Je to pět různých míst. Funguje, ale při dalším novém místě se to zase rozejde.
- **C — nechat být a jen zvýšit toleranci přehledu.** Odstraní to hlášky, ale rozdíl
  v mzdovém podkladu zůstane. Nedoporučuji.

**Pozor u kterékoli varianty:** jde o **sdílenou hodnotu**, kterou přepisuje víc procesů.
Než se sáhne na `hours`, patří k tomu dopadová mapa (kdo to plní, kdo to čte) — viz příloha.
A přepočet historie **nesmí zasáhnout uzavřené měsíce** (zamčená období).

---

## Vada č. 2 — položka rozpadu se nepřeruší při pauze

**Co se děje.** Když si člověk dá pauzu přes mobilní aplikaci, běžící položka rozpadu se
korektně uzavře. Když ale pauza vznikne **jinou cestou** (typicky přes notifikaci), položka
běží dál — přes celou pauzu — a připočte se k zakázce čas, kdy se nepracovalo.

**Jak to vypadá v datech (Jirkovský).**

| Den | Docházka | Položka rozpadu | Pauza uvnitř položky |
|---|---|---|---|
| 11. 8. | práce 7:31–8:55 | 7:14 → 8:55 | 7:14–7:31 = 17 min |
| 13. 8. | práce 7:22–8:51 | 7:07 → 7:22 + dál | 7:07–7:22 = 15 min |
| 14. 8. | práce 7:34–8:52 | 7:21 → 8:52 | 7:21–7:34 = 13 min |

To přesně vysvětluje Péťou hlášené +0,25 / +0,24 / +0,17 h.

**Důležité upřesnění k předání od Péti:** není to o „prázdném píchnutí na začátku dne".
Nulové píchnutí je jen stopa po tom, že hned po příchodu přišla pauza. Otázka tedy nezní
„má rozpad začínat od nulového píchnutí", ale **„proč pauza nepřeruší běžící položku"**.

**Návrh řešení — dvě varianty.**

- **A (doporučeno) — kaskáda ať položky rozřízne podle hlaviček.**
  Kaskáda už umí srovnat rozpad podle docházky; ať platí pravidlo *„položka nikdy nepřesáhne
  hranice své hlavičky"*. Pak je jedno, kterou cestou pauza vznikla — jedno místo pravdy.
- **B — dodělat zavírání položky do všech cest** (i notifikační).
  Rychlejší, ale je to čtvrté místo, kde se totéž řeší; příští nová cesta to zase mine.

---

## Vada č. 3 — kaskáda se nespouští ve všech situacích

Dnes se dopočet rozpadu spustí **jen při odhlášení přes notifikaci**. Když si člověk zavře
den normálně v aplikaci (Kolářová, Sedláčková), nespustí se vůbec. To je Péťův bod 2 a souhlasím
s ním — jen **ne dřív, než se doplní dvě pojistky**:

1. **Zámek období.** Ověřila jsem, že **žádný** ze zapisovatelů do rozpadu dnes nekontroluje
   zámek měsíce (`att_period_lock`). Kdyby kaskáda běžela i z půlnočního automatu, přepisovala
   by i uzavřené měsíce. Guard musí být hotový dřív než rozšíření spouštěče.
2. **Čím se díra vyplní.** Kaskáda dopočítanému času musí dát nějakou zakázku. Pokud sáhne po
   režii nebo natáhne první zakázku dne, přehled se srovná na nulu, ale **zakázková kalkulace
   dostane odhad, ne skutečnost**. A rozpad se čte i pro **výplatu OSVČ hodinářů**
   (`podklad_vyplaceni_pdf`) — tj. dopočtený čas může ovlivnit peníze.
   Chce to rozhodnutí: dopočítat na režii / nechat prázdné a hlásit / doptat se člověka.

Nejčistší je stejně Péťův bod 1 — **doptat se na zakázku hned při potvrzení příchodu
z notifikace**. Pak žádná ranní díra nevznikne a nemusí se odhadovat.

---

## Doporučené pořadí kroků

| # | Krok | Proč napřed |
|---|---|---|
| 1 | Rozhodnout vadu č. 1 (hodiny × časy) a opravit ji **u zdroje** | Odstraní šum ze všech dnů a hlavně sjednotí mzdový podklad |
| 2 | Doplnit guard na zámek období do kaskády a syncu | Bez toho nesmí přijít žádné rozšíření spouštěče |
| 3 | Vada č. 2 — položka se má zastavit na hranici hlavičky | Odstraní Jirkovského typ rozdílu |
| 4 | Rozšířit spouštěč kaskády (běžné uzavření dne, půlnoc) | Až když platí 2 a 3 |
| 5 | Doptání na zakázku při potvrzení příchodu (Péťův bod 1) | Řeší ranní díry u zdroje, ne dopočtem |
| 6 | Srovnat naplánovanou týdenní kontrolu s aplikací | Kosmetika, ale ať nehlásí lidi navíc |

Přepočet historie u kroku 1 a 3: **jen odemčené měsíce**, nikdy zpětně do uzavřených mezd.

---

## Otázky, které bych ráda probrala s Péťou

1. Souhlasí, že `hours` má být **odvozené** z uložených časů — a pro **které typy záznamů**
   to platí (work / homeoffice / overhead ano; absence a doplnění do fondu ne)?
2. Ví o důvodu, proč trigger `trg_att_entry_round_minutes` hodiny nepřepočítává —
   je to záměr, nebo se na to jen zapomnělo?
3. Má kaskáda tvrdit *„položka nesmí přesáhnout hranice hlavičky"*, nebo je na to jiný záměr?
4. Čím se má vyplňovat dopočtený čas — režie, nebo raději viditelná díra k doptání?
5. Jde `att_day_summary.cas_celkem` do mezd i po přepnutí ze 6. 8., nebo se mzdy berou jinudy?

---

## Technická příloha (pro Péťu — ať to nemusí hledat)

**Kde se počítají hodiny hlavičky (z `now()` VČETNĚ sekund):**
`att_checkin` ř. 169 a 186 · `att_checkout` ř. 90 · `att_do_att_action` ř. 115 a 146 ·
`att_auto_checkout_midnight` ř. 47 · `att_recompute_header_from_items` ř. 45.

**Kde se počítají hodiny položky (z času OŘÍZNUTÉHO na minuty):**
`att_checkin` ř. 108–109 · `att_checkout` ř. 63–64 (Péťova změna 4. 8.) ·
`att_sync_vyroba_work` ř. 223 a 234.

**Triggery na `tenant.att_entry`:**
`trg_att_entry_round_minutes` → `tenant.att_entry_round_minutes()` — ořízne časy na minuty,
`hours` nechává být (jen tenant_id = 2) ·
`att_entry_resummary` → `tenant._att_resummary_one()` — sčítá `hours` do
`att_day_summary.cas_celkem` pro typy `work`, `homeoffice`, `fond_doplneni`.

**Zapisovatelé do `tenant.vyroba_work` (vše `g2007.python`, stav `active`):**
`att_checkin` (vč. mazání položek kratších než 60 s) · `att_checkout` ·
`att_apply_work_selection` · `att_sync_vyroba_work` (kanonická kaskáda) ·
`att_auto_checkout_midnight` (automat) · `sync_vyroba_work_ec` (import z Centrály, automat) ·
`att_fix_resync` · ruční opravy: `att_fix_entry`, `att_fix_polozka`, `att_fix_void`,
`att_fix_merge`, `att_fix_move_day`, `att_fix_add`, `att_entry_trim`.
**Ani jeden z nich netestuje `att_period_lock`.**

**Čtenáři `tenant.vyroba_work`:** `dochazka_kontrola_data` (kontrolní přehled) ·
**`payroll_raporty`** (mzdový podklad) · **`podklad_vyplaceni_pdf`** (výplata OSVČ) ·
`dochazka_zakazky` (navrženo) · `att_recompute_header_from_items` ·
`sync_absence_to_ec_vytizeni` · `att_fix_day`, `att_fix_queue`.

**Notifikační cesta:** `att_do_att_action` do `vyroba_work` nesahá vůbec; kaskádu
(`att_sync_vyroba_work`) volá jen ve větvi `checkout` (ř. 121) — ne při příchodu ani při
návratu z pauzy.

**Čísla driftu:** dotazy nad `tenant.att_entry` za 10.–14. 8. (866 záznamů) a 1.–14. 8.
(1 083 záznamů typu work/homeoffice/overhead, 3 574,9 h, drift +8,63 h).
