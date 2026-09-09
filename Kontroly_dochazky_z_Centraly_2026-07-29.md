# Kontroly docházky — převzetí z Centrály do STRATEGIE

**Stav: PŘÍPRAVA** (analýza hotová, stavět se bude až po sloučení položkových tabulek `vyroba_work`)
Zapsala: C26 (Peťa / Cowork), 29. 7. 2026. Vše ověřeno v datech a v kódu, ne po paměti.

---

## 1. Kolik kontrol Centrála má

- **Celkem 106 naplánovaných kontrol** v `EC_KontrolySeznam` (ID 1–107, ID 50 chybí) — zakázky, faktury, objednávky, sklad, směrnice, úkoly…
- Docházka je v tom **jedna položka: ID 66 → procedura `dbo.EC_KontrolaDochazky`**
- Uvnitř té procedury je **23 typů docházkových kontrol**, číselník `EC_Dochazka_ChybyVDochazceTypy` (ID 1–24, ID 12 chybí)
- Nálezy se zapisují do `EC_Dochazka_ChybyVDochazce` (+ hlavička `_hlav`), příznak `ChybaJeOK` = odbaveno

## 2. Všech 23 typů + výskyty

| ID | Název | celkem | 2026 |
|---|---|---|---|
| 1 | Neukočená přestávka | 151 | 75 |
| 2 | Zapomenutý oběd | 0 | 0 |
| 3 | Málo hodin | 7 902 | 552 |
| 4 | Neomluvená absence | 19 252 | 1 452 |
| 5 | Překrytá docházka | 1 767 | 76 |
| 6 | Mezery v docházce | 11 121 | 729 |
| 7 | Neukončená přestávka | 0 | 0 |
| 8 | Neukončený den | 2 598 | 156 |
| 9 | Neoprávněná činnost | 0 | 0 |
| 10 | Krátký oběd | 0 | 0 |
| 11 | Automaticky prodloužený oběd | 0 | 0 |
| 13 | Vypnutá kontrola | 5 528 | 404 |
| 14 | Dlouhý oběd | 0 | 0 |
| 15 | Oříznutí docházky | 0 | 0 |
| 16 | Dlouhá svačina | 1 | 0 |
| 17 | Požadavek na úpravu | 2 130 | 179 |
| 18 | Více obědů | 394 | 16 |
| 19 | Dlouhé kouření | 0 | 0 |
| 20 | Chybí kuřácký paušál | 0 | 0 |
| 21 | Překročená max doba činnosti | 0 | 0 |
| 22 | Automaticky generovaný záznam | 24 | 21 |
| 23 | Přihlášení na vyhodnocené zakázce | 145 | 47 |
| 24 | Služební cesta (9) | 341 | 95 |

**12 typů v roce 2026 reálně padá, 11 má nulu.** Nulové většinou proto, že je nikdo neměl zapnuté (např. kontrola svačiny byla aktivní u jediného člověka), ne že by nefungovaly. Limity jsou v `EC_GlobKonstUziv` per uživatel — limit pro oběd 6 h u 274 lidí, výjimky 3 / 4 / 4,5 / 5 h.

## 3. Rozhodnutí Peti (29. 7. 2026)

**Hotové ve STRATEGII — nestavíme (3)**

| kontrola | co to u nás dělá |
|---|---|
| Neukončený den | pravidlo `zapomenuty_odchod` + noční dotaz „mám tě odhlásit?" + půlnoční auto-odhlášení |
| Neukončená přestávka | pravidlo `dlouha_pauza` (break > 2 h) + upozornění na přetaženou pauzu |
| Požadavek na úpravu | rozporování dne / žádost o opravu → fronta oprav jako „rozpory" |

**Zahozeno (3)**

- **Mezery v docházce** — Peťa 29. 7.: *„existuje povinnost, že si docházku kontrolují, takže mi kontrola mezer přijde nadbytečná."* (Pro pořádek: reálně by to bylo 211 mezer nad 15 min za 30 dní u 41 lidí; `nepotvrzený den` to pokrývá nepřímo.)
- **Vypnutá kontrola** — hlídá nastavení Centrály, u nás nemá smysl
- **Automaticky generovaný záznam (22)** — Peťa: nechceme, stačí kontrola 24

**K postavení (6)**

| kontrola | závislost |
|---|---|
| Neomluvená absence | žádná |
| Málo hodin | žádná (ověřit limit) |
| Překrytá docházka | žádná |
| Služební cesta (činnost 9) | **činnost 9** — viz níže |
| Více obědů | odlišit oběd od ostatní pauzy |
| Přihlášení na vyhodnocené zakázce | vazba docházky na stav zakázky |

## 4. Co jsme si vyjasnili o typech 22 a 24

Obě se týkají **činnosti 9**, která se v číselníku Centrály jmenuje **„Služeb.cesta/montáž"** — jedna položka pro obojí, Centrála mezi cestou a montáží nerozlišuje.

- **Typ 22** (Kristýna 25. 3. 2024): existuje ten den řádek s poznámkou *„Automaticky dogenerováno dle nastavení činnosti"*? → hláška jen správci docházky. **Nezajímá ho, jaká činnost to je — ptá se „kdo to zapsal".**
  Podmíněno parametrem **`@JeDlouhodoba`, default 0** → při denní noční kontrole **vůbec neběží**. **Ověřeno v datech:** všech 24 nálezů typu 22 pochází výhradně z **týdenního úterního běhu (02:39)** — `@JeDlouhodoba=1` je tedy příznak „týdenní/dlouhodobý běh".
  Mechanismus dogenerování: číselník činností má přepínače `DogenerovatDoch` + `DogenerovatCasMin`. U činnosti 9 je dnes **vypnutý**. Ukázka z 2024: řádek 08:00–16:00, zakázka Režie.
- **Typ 24** (Kristýna 15. 2. 2025): existuje ten den řádek s **`DruhCinnosti = 9`**? → hláška správci **+ notifikace přímo zaměstnanci**, že musí dodat cesťák. **Ptá se „co je zapsané", je jedno kdo to zapsal.**
  Text úkolu v proceduře: *„Pro činnost č.9 Sužeb.cesta/montáž, je nutné dodat cesťák. Pokud jej nemáte, kontaktujte správce docházky aby změnil činnost."*

**Zadání pro STRATEGII (Peťa 29. 7.):** kontrola 24 = **jen upozornění**. Cesťák jako doklad v systému evidovat nepotřebujeme — správce docházky si ověří, že člověk na cestě opravdu byl, a pohlídá si cesťák sám. **Nezáleží na tom, jestli je zakázka Režie nebo konkrétní číslo — rozhoduje jen činnost 9.**

## 5. Kde na to ve STRATEGII navázat

- Číselník činností **už máme**: `tenant.vyroba_cinnost` se sloupci **`ec_cislo`** (číslo činnosti z Centrály) a `strategie_cislo`; práce na ně odkazuje přes `tenant.vyroba_work.cinnost_id` (+ `work_alloc.cinnost_id`).
  → kontrola 24 = najdi práci, jejíž činnost má `ec_cislo = 9`.
  ⚠️ **Neověřeno:** že řádek s `ec_cislo = 9` v číselníku existuje a kolikrát se používá — most v tu chvíli vracel na PG `HTTP 401 Nejsi přihlášen`. **Doověřit před stavbou.**
- Docházkové typy `tenant.att_entry_type` (15 položek): presence = work / overhead / homeoffice / fond_doplneni / nenarokova · absence = vacation / sick / medical / family_care / sickday / unpaid / osvc_absence · break = break / day_end · travel = commute.
  **Služební cesta ani oběd tu jako typ nejsou.** Služebka z mobilu se dnes uloží jako `work` s poznámkou „služební cesta" (router.py:26894) a takový záznam je v datech **nula**. Pauzy jsou jen „krátká pauza" (425×/90 dní) a „pauza — provětrání/jídlo" (108×) — **pojem oběd u nás neexistuje**.
- Import z Centrály zahazuje činnost: klasifikace je absence → typ, `8` = home office, **ostatní = práce** (router.py:14413). Devítka se tedy dnes importuje jako obyčejná práce.
- Skener anomálií: `_att_anomaly_scan()` — router.py:48859–48995, **6 pravidel natvrdo v jednom SQL** (`budouci_zaznam`, `dlouha_smena`, `zapomenuty_odchod`, `nepotvrzeny_den`, `prace_pri_absenci`, `dlouha_pauza`), nálezy do `tenant.att_anomaly`, fronta `GET /app/attendance/fix/queue`. **Číselník typů pravidel neexistuje** — na rozdíl od Centrály.

## 6. Kdy a jak se to spouští (ověřeno v datech, hlavičky `_hlav`)

Peťa 29. 7. popsala z hlavy, data to potvrdila přesně:

| běh | kdy | období |
|---|---|---|
| **denní** | každý den **02:30**, včetně víkendů | **předchozí den** (29. 7. 02:30 → 28. 7.) |
| **týdenní** | **úterý 02:39** (tj. v noci z pondělí na úterý) | **celý předešlý týden Po–Ne včetně víkendu** (28. 7. 02:39 → 20.–26. 7.) |
| ruční | kdykoli, `SpustenoRucne = True` | libovolný rozsah (Dušan 14. 7. pustil 1.–13. 7.) |

Denní běh dělá typicky 20–55 nálezů, týdenní 80–175. Neděle a pondělí mají 0 nálezů (kontroluje se víkend).
**Týdenní běh navíc zapíná kontroly s `@JeDlouhodoba=1`** — ty, které nemá smysl řešit den po dni.

## 7. Komu se hlásí — rozhodnutí Peti (29. 7. 2026)

*(upřesněno Peťou 29. 7. po prvním nedorozumění — platí tahle verze)*

- **Zaměstnancům zachovat to, co jim chodí dnes** — jak upozornění nastavená Martim ve STRATEGII, tak ta, která jim posílala Centrála (cesťák u služební cesty, „odpracovali jste méně než X hodin").
- **Nechceme jim posílat všechny chyby.** Nově dodělávané kontroly nad rámec toho, co znají, chodí **jen správcům docházky — Peťa a Dušan**.
- Prakticky: u každé z 6 kontrol se před stavbou určí adresát — „zaměstnanec + správci" (pokud to tak chodilo dřív) nebo „jen správci" (pokud je to nové).

## 8. Jak se nálezy dostanou ke správci (rozhodnuto 29. 7.)

**Vzor z Centrály** (Peťa doložila screenshoty): úkolník → úkol *„CHYBY V DOCHÁZCE – 28.07.2026"* (zadavatel Centrala, řešitel Peťa) → záložka **Návazné doklady** → doklad *„Docházka – chyby"* → jádro **„Chyby docházky jádro"** (grid nálezů: PrijmeniJmeno, Nazev chyby, Popis, DatumPripadu, ChybaJeOK, ChybuPotvrdil, Poznamka, SeznamSkupin) → rozkliknutím řádku **„Detail docházky VV – chyby"**, kde je nahoře *Seznam chyb k vybranému dni*, uprostřed *Suma činností*, dole *Detail dne* — **a přímo tam se to opraví** (vč. tlačítka „Oříznout začátek dle prac.doby").

**Ve STRATEGII už tenhle tok existuje** — záložka **Opravy docházky** (`dochazka-opravy.html` + `GET /app/attendance/fix/queue`): vlevo fronta karet, vpravo se po kliknutí otevře **detail dne k opravě**. Nestavíme nový mechanismus, jen do fronty přibude 6 nových zdrojů nálezů. Dnešní členění fronty: ✋ rozporované dny · nesrovnalosti z automatické kontroly · staré skryté.

**ROZHODNUTO (Peťa 29. 7.): jedna karta = člověk + den.** Všechny nálezy jednoho člověka za jeden den se sloučí do jedné karty, uvnitř bude seznam chyb s typem — stejně jako *Seznam chyb k vybranému dni* v Centrále. Nahoru filtr podle typu kontroly s počty. Odbavuje se celý den najednou (to už dnes dělá tlačítko „Hotovo — z fronty", které řeší i sourozenecké karty téhož dne — Peťa 24. 7.).
Zamítnuté varianty: sekce podle typu kontroly (jeden den by se objevil vícekrát) · dělení podle naléhavosti.

## 9. Otevřené body

1. **Čeká se na sloučení položkových tabulek `vyroba_work`** (Peťa 29. 7.: *„možná to lépe uvidíš, až sloučíme ty tabulky a bude se to tvářit tak, jak se to dřív tvářilo v C"*). Plán má poslat Týnka — `Plan_sjednoceni_polozkove_tabulky_vyroba_work_2026-07-28`.
2. Postavit číselník typů kontrol (po vzoru `EC_Dochazka_ChybyVDochazceTypy`), nebo přidat pravidla natvrdo do stávajícího SQL? — **nerozhodnuto**
3. Doplnit služební cestu a oběd jako řádné typy záznamu (oběd stejně bude potřeba kvůli stravenkám)? — **nerozhodnuto**
4. ~~Ověřit limit „Málo hodin"~~ **OVĚŘENO 29. 7.:** práh je `ISNULL(U.DochKontrolaObedHod, @LimitDenHod)` — tedy **per člověka sloupec `DochKontrolaObedHod` z `EC_GlobKonstUziv`, a když není vyplněný, default 6 h**. Je to tentýž sloupec, který se používá i pro kontrolu oběda — proto se ta „šestka" objevuje dvakrát. Hláška zní *„jste odpracovali méně než 6 hodin"* a chodí **zaměstnanci** — tu zachováváme (viz kap. 7).

   **Individuální výjimky — ověřeno 29. 7. proti úvazkům** (Peťa: *„těch 6 hodin je pro 8hodinový úvazek"*). Hypotéza sedí, limit odpovídá zhruba **75 % denního úvazku**:

   | limit | úvazek/týden | denní úvazek | lidí |
   |---|---|---|---|
   | 3,0 h | 20 h | 4 h | 1 |
   | 4,5 h | 30 h | 6 h | 2 |
   | 5,0 h | 35 h | 7 h | 1 |
   | 4,0 h | 40 h (reálně 24) | — | 2 |
   | **6,0 h** | 40 h | 8 h | 147 |
   | **6,0 h** | **25 h** | **5 h** | **21** ⚠️ |
   | 6,0 h | (bez podmínek v EC) | — | 205 |

   **ALE není to dopočítané — je to ruční nastavení a je nekonzistentní.** 21 lidí s úvazkem 25 h/týden (5 h denně) má pořád default 6 h, takže by je kontrola hlásila i za plně odpracovaný den. Konkrétní doložený případ: **Dvořáková Petra, úvazek 30 h (6 h denně), limit 6 h → 42 nálezů „Málo hodin" za rok 2026**, zatímco jiní lidé s týmž úvazkem mají výjimku 4,5 h.

   **ROZHODNUTO (Peťa 29. 7.):** limit z Centrály **nekopírovat**, ale **počítat z úvazku — 75 % denního úvazku zaokrouhlené DOLŮ na celé hodiny** (Peťa chtěla celé hodiny, ne 4,5). Ruční přepis zůstane jen jako skutečná výjimka.

   | úvazek/týden | denní úvazek | 75 % | **limit** | dnes v Centrále |
   |---|---|---|---|---|
   | 40 h | 8 h | 6,0 | **6 h** | 6 h ✓ |
   | 35 h | 7 h | 5,25 | **5 h** | 5 h ✓ |
   | 30 h | 6 h | 4,5 | **4 h** | 4,5 h |
   | 25 h | 5 h | 3,75 | **3 h** | 6 h ✗ (chyba v Centrále) |
   | 20 h | 4 h | 3,0 | **3 h** | 3 h ✓ |

   Sedí na 3 ze 4 hodnot nastavených v Centrále, liší se jen u šestihodinového dne (4 místo 4,5) a opravuje nesmysl u pětihodinového úvazku. Zamítnutá alternativa: „denní úvazek − 2 h" (stejné výsledky kromě 4h dne, kde by dala příliš benevolentní 2 h).
   Fond per úvazek už umíme (`_sync_dochazka_ec`, úvazek_tyden_h / 5).
5. Doověřit `vyroba_cinnost.ec_cislo = 9` (viz výše, most vracel 401)
6. Překlopit tenhle zápis do G2007 (oblast `dochazka`), až most na PG pojede
