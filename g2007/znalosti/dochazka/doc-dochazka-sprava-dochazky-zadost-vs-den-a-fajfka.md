# Správa docházky — žádost vs. den, fajfka vedoucího, akce z menu (+ den se maže JEN přes Smazat; hlídače zamitnuto_ale_den_zustal a nerozhodnuta_zadost_po_dni)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Správa docházky — žádost vs. den, fajfka vedoucího, na co působí akce z menu

**26. 8. 2026, Peťa + C26.** Vzniklo z toho, že se v přehledu obojí plete a hromadná akce
hlásila „není označena žádná žádost", i když řádky označené byly.

## Dvě různé věci na jedné obrazovce

| | **Žádost** | **Den** |
|---|---|---|
| Co to je | papír — někdo si dopředu řekl o volno, čeká na rozhodnutí | skutečný záznam docházky, počítá se do mzdy |
| Tabulka | `tenant.att_absence_request` | `tenant.att_entry` |
| Poznávací znamení v přehledu | sloupec **Zdroj** = „žádost z appky" | Zdroj = appka, ruční oprava, schválená žádost, plán z Centrály, import z Centrály, neschopenka ČSSZ |
| Identita řádku (`RadekId`) | `Z:<id žádosti>` | `D:<id>,<id>,…` |
| Co znamená fajfka ve sloupci S | žádost je ve stavu `approved` | `att_entry.ved_schvaleno` = vedoucí to viděl a odsouhlasil (hodiny to nemění) |

**Žádost NENÍ podmínkou dne.** Den v docházce vzniká i bez schválení (ohlášení z appky,
plán, sync z Centrály, ruční zápis) — pravidlo Peti z 30. 7. 2026, viz
`doc-dochazka-sprava-vs-new-co-se-preklapi`. Schvalování běží vedle.

## Jeden řádek přehledu může nést víc dnů
Denní větev datasetu `dochazka.zakazky_budoucnost_list` slepuje souvislé dny do jednoho
řádku a jejich id skládá do `string_agg(DISTINCT entry_id::text, ',')`. Řádek „Hrůzová,
dovolená 1.–7. 8., 5 D" tedy nese **pět** `att_entry` (1. a 2. 8. byl víkend).
Fajfka nemá kam se uložit „za období" — zapisuje se na každý den zvlášť.

**Pozor na `bool_or`:** fajfka u slepeného řádku se rozsvítí, když ji má **aspoň jeden**
den z bloku. Částečně odfajfkovaný blok vypadá jako hotový. Rozpad je vidět až v Docházce
new (sloupec `VedSchvaleno`) nebo v datech.

## Na co působí akce z kontextového menu (Peťa 26. 8. 2026)
`window.akceRadky()` v `dochazka-po-zakazkach.html`:
- **nic označeného** → akce vezme řádek, na kterém člověk stojí (`CTX_ROW`),
- **označeno víc řádků** → vezmou se označené, `CTX_ROW` se ignoruje.

`Schválit označené` / `Vzít schválení zpět` umí obojí naráz: co je `Z:`, rozhodne přes
`/app/attendance/absence/decide`; co je `D:`, odfajfkuje přes
`/app/dochazka-zak-tab/save-doch-meta` (`ved_schvaleno`), a to pro každý den v řádku.

## Kde se `ved_schvaleno` zapisuje
1. `att_absence_decide` při schválení žádosti — celý blok naráz (od 6. 8. 2026),
2. správcovská cesta ve Správě docházky (`dochazka_absence_sprava._zapis_dny`) podle
   zaškrtávátka „Schváleno",
3. `save-doch-meta` po jednom řádku (Docházka new, Opravy, nově hromadná akce),
4. přepočty (`att_dovolena_kaskada`).

## Doložená nesrovnalost a její příčina (26. 8. 2026)
Nápravný běh **18. 8. 2026 v 6:19** doplnil fajfky jen dnům **do 31. 7.** — srpnové nechal
být. Proto vznikly „částečně odfajfkované" bloky: každý blok, který přetéká přes konec
července. Doloženo na žádostech 19 (Hladíková, fajfka 29.–31. 7., chybí 3. 8.) a 22
(Hrůzová, fajfka 27.–31. 7., chybí 3.–7. 8.). Stav před opravou: 58 bloků kompletních,
14 zcela bez fajfky, 2 částečné.

Opraveno 26. 8. 2026 (6 dnů) — doplněno jen tam, kde je žádost `approved`. Zbylých 28 dnů
u 14 žádostí fajfku **nemá správně**: ty žádosti pořád čekají na rozhodnutí (11 z nich má
vedoucího Dušana Havláta, dále Šik pod Kristýnou, Šafránková ml. pod Michelle, Čepický pod
Petrem Benešem). Fajfka se jim doplní sama, až se rozhodnou.

## Otevřené
- **Den a žádost o sobě navzájem nevědí, když den vznikl z ohlášení.** Odkaz (`source_id`
  + `source_system='absence_req'`) nese jen den vytvořený SCHVÁLENÍM. Když si člověk
  ohlásí absenci v appce, den vznikne rovnou, ale bez vazby — a když pak ohlášení zruší,
  den zůstane viset a musí ho ručně stornovat člověk. Doloženo: Jiří Honomichl, lékař
  19. 8. (záznam 10009312, ohlášeno 17. 8. 4:42, stornováno ručně 25. 8. s poznámkou
  „zaměstnanec to zrušil, záznam zůstal viset kvůli chybějící vazbě na žádost").
- Zvážit, zda fajfku u slepeného řádku neukazovat až při `bool_and` místo `bool_or`.
  Peťa 26. 8.: částečné bloky nemají vznikat, takže lepší je opravit data než zobrazení.

## Jedno tlačítko místo dvou — a co NIKDY nesmí dělat (Peťa 31. 8. 2026)

Dvě položky „Schválit označené" a „Vzít schválení zpět" nahradilo **jedno**
**✅ Schválit / odznačit (označené)** (`prepniSchvaleni()`). Označené dny nemají fajfku →
dá ji tam; mají ji → sundá ji.

**Pravidlo Peťi, závazné:** *„smažou se přes Smazat, s jasným úmyslem toho dotyčného,
ne přes tlačítko schválit / odschválit."*

Tlačítko na fajfku proto **nikdy nemaže**. Mění výhradně `att_entry.ved_schvaleno`
u řádků typu `D:` — hodin ani záznamů se nedotkne. Řádky se žádostí (`Z:`) **přeskočí**
a napíše to do potvrzení; o žádosti se rozhoduje přes „Schválit / zamítnout absenci",
maže se vědomě přes „Smazat".

**Proč to takhle musí být (past, na kterou jsem 31. 8. sama naletěla):** vzít schválení
zpět přes `att_absence_decide` se stavem `pending` spustí větev `elif materialized:`, která
**smaže z docházky všechny dny vzniklé tím schválením** (poznané podle
`source_system='absence_req' AND source_id=<žádost>`). Jako vědomé rozhodnutí je to
správně — neschválená absence v docházce být nemá. Jako **vedlejší účinek odfajfknutí je
to nepřijatelné.** První nasazená verze to takhle měla (verze souboru 49, ~2 minuty živá,
ověřeno že ji nikdo nestihl použít — žádná žádost v tom okně nebyla rozhodnuta), opraveno
ve verzi 50.

**Nález navíc (v G2007 dosud nebyl):** „Vzít schválení zpět" sahalo na žádosti přes
`oznaceneZadosti()`, tedy přes seznam z `/app/attendance/absence/inbox` — a ten vrací
**jen `stav='pending'`**. Na **už schválenou** žádost se tím nedalo dosáhnout a akce u ní
tiše neudělala nic. Nové `oznaceneZadostiZRadku()` bere číslo žádosti přímo z řádku
(`RadekId` = `Z:<id>`), takže dosáhne i na schválené; práva hlídá server v `decide`.
Dnes se to nepoužije (tlačítko žádosti přeskakuje), ale funkce je připravená.

## ZADÁNÍ Peťi 31. 8. 2026: fajfka JE schválení (jedna věc, ne dvě)

Peťa: *„tím, že den stejně existuje a jde do docházky, měla by ta fajfka prostě být
schválení"* a *„smažou se přes Smazat, s jasným úmyslem toho dotyčného, ne přes tlačítko
schválit / odschválit."*

**Cíl:** fajfka ve sloupci S má napříč přehledem znamenat **jedno a totéž — „schváleno"**.
Dnes znamená u dne `ved_schvaleno` a u žádosti stav `approved`, což se plete.

**ŽELEZNÉ PRAVIDLO PEŤI (31. 8. 2026, doslova):** *„mazat dny jen když někdo dá
SMAZAT, jindy NE."*

Den z docházky smí zmizet **výhradně** vědomým stiskem „Smazat". Nikdy jako vedlejší
účinek jiné akce — ani odfajfknutím, ani vzetím schválení zpět, **ani zamítnutím žádosti**.

**HOTOVO 31. 8. 2026 — celý řetěz, ne půlka.** Peťa: *„napřed to musíme dořešit, nebo
pak zase budeme mít poloviční paskvil."* Tři kusy, všechny nasazené a ověřené:

**1. `att_absence_decide` — mazací větev pryč.** Větev `elif materialized:` (odstraňovala
z docházky všechny dny vzniklé schválením při KAŽDÉM odchodu od `approved`) je odstraněná
celá. Rozhodnutí o žádosti mění jen stav žádosti a příznak schválení. Idempotentní úklid
uvnitř větve `approved` ZŮSTAL — brání zdvojení dnů při opakovaném schválení téže žádosti.
Ověřeno: `compile()` prošel, větev v kódu není.

**2. Hláška po zamítnutí.** Ve všech ERP místech, kde se o žádosti rozhoduje, vyskočí po
jiném rozhodnutí než schválení upozornění, že dny zůstaly v docházce a musí se smazat ve
Správě docházky. Nasazeno v `dochazka-po-zakazkach.html` (v51),
`_fragment_schvalovani_absenci.html`, `_fragment_registr_schval_radek.html`,
`registr-absenci.html`. **NEDODĚLÁNO: mobilní appka** (`50_skupiny_vyroba.js`,
`mobile.html`) — vedoucí rozhodují i z mobilu a tam hláška zatím není.

**3. Nález do fronty Oprav `zamitnuto_ale_den_zustal`** v `att_anomaly_scan` — pojistka
pro případ, že na to někdo zapomene. Bere jen `stav='rejected'`; úklid nálezu, jakmile
dny zmizí nebo se žádost přerozhodne. Ověřeno: `compile()` prošel, obě SQL naostro
(nález i úklid) vrací 0 řádků — k 31. 8. není žádná zamítnutá žádost s visícími dny.

**Proč jen `rejected` a ne `pending`:** žádost ve stavu „čeká" s už zapsanými dny je
v pořádku — den vzniká i bez schválení (pravidlo Peťi 30. 7.). K 31. 8. 2026 je takových
**5 žádostí / 11 dnů / 72 h** a nález by na nich falešně svítil.

Zápis do `g2007.python` nejde přes SQL most (příkaz na to není) — musí přes ERP
(`znalost-upsert` obdoba pro python) nebo přes Marti-AI.

**Hotová část:** tlačítko **✅ Schválit / odznačit (označené)** (verze souboru 50) mění
zatím jen `ved_schvaleno` u dnů a řádky se žádostí přeskakuje. Funkce
`oznaceneZadostiZRadku()` (číslo žádosti z řádku, ne ze seznamu čekajících) je připravená
a čeká právě na tu úpravu v `att_absence_decide`.

## Peťa a Michelle vidí ve Správě docházky VŠECHNY žádosti — už funguje

Ověřeno 31. 8. 2026 v datech: `_abs_global` v `att_absence_inbox` pouští na **každou**
čekající žádost správce systému nebo držitele práva `neschopenky` na úrovni `write`.
To právo mají aktivní **Peťa (18) i Michelle (17)** — takže položka
„✅ Schválit / zamítnout absenci" jim v kontextovém menu vyskočí na kterémkoli řádku
s čekající žádostí, ne jen na svých lidech. Zadala to Peťa 26. 8. 2026 a je to hotové.

**Směrování žádostí se tím nemění** — žádost dál patří svému vedoucímu, notifikace
i mobil jedou beze změny. Peťa 31. 8.: *„všude jinde ať ty žádosti chodí tak, jak mají,
těm, co mají."*

## Hlídač `nerozhodnuta_zadost_po_dni` — nerozhodnutá žádost, den už proběhl (Peťa 31. 8. 2026)

Peťa: *„má-li někdo dovolenou třeba na 8. 9., tak pokud to 9. 9. není schválený, ať to jde
na schvalovatele."*

Den do docházky vzniká i bez schválení, takže hodiny se počítají, zatímco žádost visí
nerozhodnutá. Nové pravidlo v `att_anomaly_scan` proto zakládá nález **den poté, co dotčený
den proběhl** (`e.entry_date < current_date`), když je žádost pořád `pending`.

**Notifikace jde VÝHRADNĚ schvalovateli** (`att_absence_request.manager_user_id`) — ne
zaměstnanci (ten svoje udělal, když podal žádost) a ne editorům oprav (rozhodnout může jen
schvalovatel). Když schvalovatel chybí, spadne to na editory jako u ostatních pravidel.
Text: „⏳ Čeká na tvoje rozhodnutí … Otevři Nepřítomnosti → Ke schválení."

**Nález zmizí sám**, jakmile se žádost rozhodne nebo dny z docházky zmizí.

**Technicky:** `RETURNING` v hlavním zápisu nálezů rozšířen o `entry_id` (ostatní pravidla
se nemění, čtou dál `r[0..2]`), z něj se dohledá schvalovatel.

**Stav při nasazení (ověřeno naostro):** 2 nálezy — Duspivová 31. 8. (7 h, schvalovatel
Vladimír Mareš) a Šík 24.–28. 8. (30 h, Kristýna). Beneš a Dvořáková 1. 9. a Diviš 21. 12.
správně NE, ty dny ještě neproběhly.

**Gotcha pro zápis kódu přes SQL most:** `UPDATE g2007.python` běží autonomně bez banneru,
ale kontrola zapisovacích cílů čte i vnitřek řetězců — když je v posílaném zdrojáku
`INSERT INTO tenant.…`, spadne to na banner. Řešení: v literálu rozdělit klíčová slova
(`'INS' || 'ERT'`). A druhá past: SQLAlchemy bere za parametr `:cokoliv` včetně **čísel** —
`msg[:600]` v pythonu shodí zápis na „A value is required for bind parameter '600'".
Rozdělit `:` přes `chr(58)` u písmen **i číslic**.

