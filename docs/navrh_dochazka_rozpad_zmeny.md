# Změnový list — srovnání docházky a rozpadu

**Pro:** Kristý → Peťa (konzultace 18. 8. 2026)
**Od:** Claude‑24 · 17. 8. 2026
**Navazuje na:** `navrh_dochazka_rozpad_sjednoceni.md` (rozbor příčin)

---

## ✅ Stav k 18. 8. 2026 — co už běží (autorizovala Kristý)

Nasazeno v `g2007.python` (projeví se hned, bez restartu, na obou instancích API).
Každá změna ověřena stažením zdroje z DB a kompilací; předchozí verze archivuje trigger.

| Kód | Co se změnilo | Verze |
|---|---|---|
| `att_sync_vyroba_work` | **guard na `att_period_locked`** — do zamčeného měsíce kaskáda nezapíše nic (fail‑closed) | 5 |
| `att_checkout` | kaskáda po uzavření úseku z aplikace | 7 |
| `att_do_att_action` | kaskáda i ve větvi `checkin` a `resume_work` (dřív jen `checkout`) | 5 |
| `att_auto_checkout_midnight` | `RETURNING` vrací i den + kaskáda po půlnočním uzavření | 5 |
| `att_confirm_day` | kaskáda po potvrzení dne | 2 |

**Nezměněno:** chování u zapomenutého odchodu (dopsaný konec 23:59 se do rozpadu nepřebírá,
Peťa 31. 7.) a pravidlo pro živý den (kaskáda jede konzervativně, nic nezakládá).

## ✅ Doplněno 19. 8. 2026

| Kde | Co se změnilo |
|---|---|
| `att_checkin`, `att_checkout`, `att_do_att_action` | **A1** — hodiny hlavičky se počítají z času ořezaného na celé minuty (5 míst) |
| `att_wa_close_running` (nový) | sdílená implementace uzavření běžící položky, s ořezem |
| `att_wa_open` (nový) | sdílená implementace založení nového úseku, s ořezem |
| `router.py` ř. 26384 a 26421 | **A2** — obě funkce jsou tenké delegáty do G2007 (commit `a0e2789d`, nasazeno) |
| `att_auto_checkout_midnight` | opravena nesouměrnost — položky se zavírají podle **svého** dne (jen naše `app` položky, včerejšek a dnešek) |
| `tenant.vyroba_work` | zneaktivněny 2 osiřelé běžící položky po opravených dnech (Honomichl 7. 8. #25347, Šárka 11. 8. #25364) |
| G2007 | znalost `doc-dochazka-rozkol-hodiny-vs-casy-a-spousteni-kaskady` |

**Ověřeno v provozu 19. 8. v 09:11** — Kristý přepnula zakázku a činnost v mobilu, Beneš píchl
režii; všechny nové položky mají **nuly na sekundách** (ráno jich 23 z 81 sekundy ještě mělo)
a správně vyplněnou vazbu na píchnutí.

---

## 🗣️ K PROJEDNÁNÍ S PÉŤOU — 372 běžících položek ze staré Centrály

**Nález 19. 8. 2026.** V `tenant.vyroba_work` je **372 aktivních položek bez konce**
(`konec IS NULL`), `source_system = 'centrala1'`, s daty od **30. 9. 2025 do 30. 6. 2026**.
Jsou to importované řádky, které nikdy nedostaly konec. Zakázku mají všechny.

**Proč to zatím nikoho netrápilo.** Půlnoční automat je nevidí (bere jen aktuální den),
kontrolní přehled porovnává uzavřené položky, a sync z Centrály je od 14. 8. 2026 zastavený —
takže nové nepřibývají. Je to **uzavřená množina k jednorázovému úklidu**.

**Proč to řešit dřív než backfill.** Jakmile se pustí kaskáda nebo backfill přes starší
období, tyhle řádky se do zpracování dostanou. A kdyby se jim někdy dopočítal konec podle
vzoru „konec dne", šlo by o **4 835,7 h** připsaných zpětně — přes uzamčená období.

**⚠️ Doplněno 19. 8. odpoledne — ověřeno přímo v Centrále, NENÍ to chyba importu.**
Vytáhla jsem tři zdrojové řádky (`EC_Dochazka` ID 1818886, 1829691, 1834421) a všechny mají
`CasKonec = NULL`, `CasCelkemZakazka = 0`, `HodinyDoFPD = 0`, `PraceAktivni = 0`. **Jsou tedy
rozdělané už v Centrále** — někdo si otevřel práci na zakázce a nezavřel ji. Naše zrcadlo je
kopíruje věrně, takže **docházka na Centrálu sedí** a „opravou" bychom se od ní naopak odchýlili.

Další profil: všech 372 nese **nula hodin** (proto nezkreslují žádný součet a nikdo si jich
nevšiml) · všechny mají činnost · **140 nemá vazbu na píchnutí** · jen **6** má na stejný den
a zakázku uzavřenou dvojnici (nejsou to duplicity) · vznikly ve třech dávkách importu —
**4. 7. (179), 31. 7. (153, velký reimport), 5. 8. (40)** · typický tvar je `DatumPripadu`
na konci měsíce a `CasZacatek` o dva až tři dny později (měsíční uzávěrkové řádky Centrály).

**Rozhodnutí Kristý 19. 8.: nechat být.** Sync z Centrály je od 14. 8. zastavený, nové
nepřibývají. Jde jen o to, aby o nich Peťa věděla a aby s nimi počítal každý, kdo bude
zpracovávat starší období — v naivním dotazu se tváří jako věčně běžící práce.

> **Poznámka k tomu, jak se to našlo (a poučení).** Když jsem 19. 8. opravovala nesouměrnost
> v půlnočním automatu, první verze podmínky brala *všechny* otevřené položky do dneška —
> tedy i těch 372. Chyba se chytla až při ověřování, před nočním během, takže nic nezapsala.
> Ponaučení do doktríny: i „jednořádková" změna v automatu si zaslouží dopadovou mapu
> (kolik řádků nově spadne do záběru), ne jen kontrolu syntaxe.

---

## 🗣️ PRO PÉŤU — Jana Lišková 3. 8.: dvě položky na tomtéž úseku (naše × Centrála)

**Poslední řádek, který kontrolní přehled po 19. 8. hlásí.** Rozpad má o **0,95 h** víc než
docházka (8,89 vs 9,84).

**Příčina, ověřeno v datech.** Na úseku **05:55–07:48** leží dvě aktivní položky najednou:

| Položka | Čas | Hodin | Zakázka | Zdroj |
|---|---|---|---|---|
| `21495` | 05:55–07:48 | 1,883 | VR10674 | `app` (naše) |
| `21649` | 05:55–06:51 | 0,940 | Rezie | **`centrala1`** (import) |

Překrývají se o **0,94 h** — přesně o to má rozpad navíc.

**Proč to kaskáda neuklidila.** `att_sync_vyroba_work` bere „naše" položky **schválně bez**
`source_system='centrala1'` (pojistka Claude‑26 + Peťa z 31. 7. 2026 proti zdvojení u lidí, kteří
píchají na tabletu staré Centrály). Řádky z Centrály tedy bere jako existující pokrytí, ale
nikdy je needituje ani nevypíná. Duplicita proto přežije jakýkoli přepočet.

**Rozsah: jediný případ.** Prověřeno celé období 1. 7. – 19. 8. 2026 — tahle kombinace
(naše položka × položka z Centrály na stejném čase) je v datech **jednou**, u Liškové 3. 8.
Není to tedy systémový jev, ale zbytek po přechodu z Centrály.

**Návrh:** zneaktivnit `21649` (0,94 h, Režie). Sahat na `centrala1` data je jinak zapovězené,
proto to nechávám na rozhodnutí Péti — Kristý o tom ví.

---

## 🗣️ PRO PÉŤU — naplánovaná týdenní kontrola má zastaralý dotaz

**Kde je, jsem nenašla.** Prohledala jsem tabulky úkolů a plánovačů (`public.tasks`,
`g2007.ukol`, `tenant.task`, `tenant.ai_wake_schedule`, `fw.mirror_job`) i naplánované úlohy
Kristý — nikde uložený dotaz nad `vyroba_work` není. **Nejspíš je to Péťin vlastní naplánovaný
úkol v jejím Claudovi**, na který zvenčí nevidím. Níže je proto **aktuální živá definice**
(`g2007.python`, kód `dochazka_kontrola_data`, `_KONTROLA_ROZPAD_SQL`) k porovnání.

**Dvě věci, které v té staré kopii podle Péti chybí — obě v živém přehledu jsou:**

1. **Lidé, kteří se nekontrolují** —
   `cislo_zam NOT IN ('21','2','15','41','349','9005','9017','9030','9103')`
   (Marti Pašek, Honomichl, Šik, Pillár, Jan Svoboda, Mareš, Marešová). Bez toho přehled hlásí
   lidi, kteří docházku vůbec nevedou.
2. **Ohlášený home office** — `COALESCE(e.source_system,'') <> 'absence_req'` (Peťa 5. 8.).
   Ohlášená práce z domova je informace, ne práce na zakázce; bez filtru vzniká falešný rozdíl
   (Hladíková 16. 7. = −2,33 h).

**A tři věci, které se od té kopie taky změnily — stojí za kontrolu:**

- `COALESCE(e.source,'') <> 'plan_ec'` (plánované nepřítomnosti z Centrály ven),
- **období** = běžící měsíc, plus předchozí dokud **není zamčený**, a **nikdy před 1. 7. 2026**
  (leden–květen jsou z Centrály jiným postupem, červen je přechodový),
- **dnešek se vynechává** (`do = current_date - 1`) — rozdělané směny nejsou chyba;
  práh je `abs(rozdíl) > 0,1 h`, typy `work / overhead / homeoffice` kategorie `presence`.

---

## 🗣️ K ROZHODNUTÍ S PÉŤOU — pravidlo o „parazitním úseku"

**Jak to funguje dnes.** `_wa_open` (nově `att_wa_open`): když poslední zavřená položka trvala
**méně než 60 s**, smaže ji a nová položka **převezme její začátek**. Zavedl to Marti 19. 6. 2026
proti úsekům o nulové délce, které vznikaly při výběru zakázky a hned poté činnosti.

**Problém A — pravidlo umí sníst pauzu.** Když mezi smazaným úsekem a novým byla pauza, nová
položka začne **před ní** a přičte ji k zakázce. Odtud Jirkovského rozdíly 11., 13. i 14. 8.
(13 až 17 minut) a Honomichl 12. 8. (137 minut). Nejde o hodiny navíc v docházce, ale o čas
připsaný zakázce, na které se nepracovalo.

**Problém B — ořez na minuty změnil, kdy pravidlo vůbec zabere.** Délky úseků jsou teď vždy
násobky minuty, takže podmínka „méně než 60 s" projde **jen když oba kliky padnou do stejné
minuty**. Kdo vybere zakázku a činnost o minutu později, tomu zůstane **jednominutový útržek
bez činnosti** (Kristý 19. 8., 09:11–09:12). Hodiny to neubírá, ale kazí to přehled.

**Návrh (Claude‑24).** Přeformulovat podmínku ze samotné délky na **návaznost**:
*„převezmi začátek smazaného úseku, jen když na něj nová položka bezprostředně navazuje —
tzn. mezi jeho koncem a teď není mezera (např. do 60 s)."*

- Vyřeší **A** — po pauze nová položka začne normálně teď, nic se nesní.
- Vyřeší i **B** — útržek se smaže i tehdy, když trval přesně minutu, protože rozhoduje mezera, ne délka.
- Riziko je malé a lokální: jde o jednu podmínku v jedné (už sdílené) funkci.

**Otázky na Péťu:**

1. Souhlasí s posunem od „krátký úsek" k „navazující úsek"? Byla za původní podmínkou i jiná
   situace, kterou neznám?
2. Jaká tolerance mezery dává provozně smysl — 60 s, nebo víc (člověk hledá zakázku v seznamu)?
3. Má se útržek **mazat** i tehdy, když už má vyplněnou činnost, nebo jen ten prázdný?

---

## ⚠️ Oprava mého předchozího závěru

V rozboru jsem u Jirkovského psala, že příčina je v notifikační cestě. **To bylo nepřesné.**
Po přečtení kaskády a `_wa_open` je to takhle:

- Kaskáda **už umí** oříznout položku na hranice píchnutí (`att_sync_vyroba_work` ř. 131–132)
  i vyplnit okraje úseku (ř. 121–128). Kdyby proběhla, Jirkovského přesah by srovnala.
- **Neproběhla** — spouští se jen při odhlášení přes notifikaci a při ručních opravách.
  Jirkovský si den zavřel v aplikaci, takže nic nesrovnalo nic.
- Vznik toho přesahu je v `_wa_open`: když poslední položka trvala < 60 s, **smaže ji a nová
  položka převezme její začátek** (pravidlo proti „parazitním" úsekům, Marti 19. 6.).
  Když mezi tím byla pauza, natáhne se položka i přes ni.

Takže bod 2 a bod 3 z rozboru jsou ve skutečnosti **jedna věc: kaskáda se nespouští všude.**
To je dobrá zpráva — logika je hotová, chybí jen volání.

---

## Změna A — nikde sekundy, všude celé minuty

**Problém:** hodiny se počítají z času **se sekundami**, ale časy se do DB ukládají
**oříznuté na minuty** (trigger `trg_att_entry_round_minutes`). Hodiny pak neodpovídají
vlastním časům. Za 1.–14. 8. to dělá **+8,63 h** za firmu a teče to i do `att_day_summary`
(mzdový souhrn).

**A1 — hodiny hlavičky (5 míst, `g2007.python`):**

| Kód | Řádek | Změna |
|---|---|---|
| `att_checkin` | 168–169 | `now()` → `date_trunc('minute', now())` |
| `att_checkin` | 185–187 | totéž |
| `att_checkout` | 89–91 | totéž |
| `att_do_att_action` | 113–116 | totéž |
| `att_do_att_action` | 144–148 | totéž |

`att_auto_checkout_midnight` **měnit netřeba** — počítá z času 23:59, sekundy tam nevznikají.
(V rozboru jsem ho uváděla, to beru zpět.)

**A2 — položky rozpadu (starý kód v `router.py`).** Péťa 4. 8. ořezal časy položek na minuty
v `g2007.python`, ale **stejné funkce zůstaly i v `router.py`** (`_wa_close_running`
ř. 26494–26500, `_wa_open` ř. 26531+) a ty ořez **nemají** — pořád píšou `konec=now()`
se setinami. Proto má **408 z 1 277 srpnových položek sekundy v `od`** a 365 v `konec`.
Podle pravidla „kód jako data" by tyhle dvě funkce měly být tenké delegáty do DB, ne kopie.
**Otázka na Péťu:** rovnou zmigrovat, nebo zatím jen doplnit ořez i do `router.py`?

**A3 — dorovnání srpna.** Přepočet `hours` z uložených časů pro typy work / homeoffice /
overhead, období 1.–17. 8., **jen v odemčených měsících**. Efekt: ~−8,6 h za firmu.
Připravím jako jeden skript s přehledem před/po. **Schvaluje Marti** (dotýká se mzdového
podkladu) — já to sama nepustím.

---

## Změna B — kaskáda po každém uzavření dne (řeší přesahy i ranní díry)

**Dnes se spouští:** ruční opravy (`fix/entry`, `fix/add`, `fix/void`, `fix/merge`),
`fix/resync` a odhlášení přes notifikaci (`att_do_att_action` ř. 121).

**Má se spouštět i:** při běžném odhlášení v aplikaci (`att_checkout`), při návratu z pauzy
(`att_do_att_action`, větev `resume_work`), po půlnočním automatu
(`att_auto_checkout_midnight`) a po potvrzení dne (`att_confirm_day`).

Volání je jednořádkové a vzor už existuje — `_att_sync_po_notifikaci()`
(`att_do_att_action` ř. 55–71), včetně `try/except`, aby chyba kaskády neshodila píchnutí.

**Povinná pojistka:** před zápisem ověřit zámek období. Funkce **`att_period_locked`
už existuje** („True = měsíc dne d je uzamčen") — stačí ji do kaskády doplnit a při zámku
neprovádět zápis. Dnes zámek nekontroluje **ani jeden** zapisovatel do rozpadu, takže tohle
musí být hotové **dřív** než rozšíření spouštěčů.

---

## Změna C — aby přesah nevznikal (prevence)

`_wa_open`: pravidlo „smaž položku kratší než 60 s a začni od jejího začátku" nechat,
ale použít jen tehdy, když **mezi smazanou položkou a novou není mezera** (např. do 60 s).
Když mezi tím byla pauza, nová položka začne normálně teď.

Bez změny C se přesahy budou dál zakládat a změna B je bude uklízet zpětně. Se změnou C
nevzniknou. V srpnu šlo o **7 položek u 4 lidí, celkem 3,2 h, největší 137 minut** — takže
to není časté, ale když to nastane, je to velké.

---

## Změna D — chybějící zakázka do Oprav (Kristýn návrh)

**Dobrá zpráva:** kaskáda si zakázku **nevymýšlí** — do nového řádku dá tu z píchnutí
(`att_sync_vyroba_work` ř. 170–172). Když u píchnutí zakázka není, vznikne řádek
s **prázdnou zakázkou**. Přesně jak Kristý chce.

**Co chybí:** ani `att_fix_queue`, ani `att_anomaly_scan` dnes nehlídají „položka rozpadu
bez zakázky" — ověřeno, takový typ tam není. Doplnit do fronty „K vyřešení" novou položku:
*aktivní řádek rozpadu na uzavřeném dni s prázdnou zakázkou* → kontrolor ji doplní.

Hlídání při přihlášení (aby si člověk zakázku musel vybrat) je Péťin bod 1 — tam nezasahuji.

---

## Co zbývá dodělat (stav 19. 8. 2026, 11.00)

| # | Krok | Proč / riziko | Kdo rozhodne |
|---|---|---|---|
| 1 | **Zapomenuté odchody v srpnu** — 9 směn nad 10 h zavřených půlnočním automatem, celkem **135,6 h** (Honomichl 7×, Marti 2. 8., Šárka 3. 8.; nejvíc 18,18 h). Seznam: `Zapomenute_odchody_srpen2026_pro_Petu.xlsx` | hodiny, které se nestaly, jdou přes denní souhrn do mzdového podkladu; **musí se opravit dřív než backfill**, jinak je backfill zabetonuje. Honomichl 7. 8. a Šárka 11. 8. už opravené | Kristý + Peťa |
| 2 | **Backfill položek za srpen** (`att_fix_resync`, `dry_run` napřed) — srovná zbylé přesahy | ⚠️ **nelze spustit z mostu** — je to jen API endpoint, nemá tlačítko v ERP ani `@@` příkaz. Buď ho pustí Peťa, nebo doplníme příkaz (další deploy) | Peťa |
| 3 | **Pravidlo o parazitním úseku** (změna C) — viz sekce výše | odstraní přesahy u zdroje i minutové útržky | **Peťa** |
| 4 | **372 běžících položek ze staré Centrály** — viz sekce výše | uzavřená množina 9/2025–6/2026; hrozí až při zpracování starších období | **Peťa** (+ Jirka) |
| 5 | **Dorovnání hodin za srpen** (A3) — přepočet `hours` z uložených časů, jen odemčené měsíce, ~−8,6 h za firmu | **mzdový dopad** | **Marti** |
| ~~6~~ | ~~**Dokončit sjednocení**~~ — **HOTOVO 19. 8. odpoledne**: `att_checkin` i `att_checkout` mají místo vlastních kopií tenké delegáty na `att_wa_open` / `att_wa_close_running`. `att_checkin` 277 → 255 řádků, obojí ověřeno kompilací | jedno místo pravdy — pravidlo se teď opravuje jen jednou | — |
| ~~7~~ | ~~**„Chybí zakázka" do fronty Oprav**~~ — **HOTOVO 19. 8.**: nové pravidlo `chybi_zakazka` v `att_anomaly_scan` (uzavřené píchnutí, k němuž existuje aktivní položka rozpadu s prázdnou zakázkou nad 0,1 h, posledních 14 dnů, od 1. 8.) + **vlastní úklid**, takže hláška zmizí sama, jakmile kontrolor zakázku doplní. První běh ve 14:48 našel **5 případů** (Pěchouček 11. 8., Honomichl 7. a 18. 8., Novotná 10. a 19. 8.) — přesně tolik, kolik předpověděla dopadová mapa | kontrolor doplní zakázku tam, kde ji člověk nevybral | — |
| 8 | **Doptání na zakázku při potvrzení příchodu z notifikace** | řeší ranní díry u zdroje; Péťin bod 1, já do toho nezasahuji | Peťa |
| 9 | **Naplánovaná týdenní kontrola má zastaralý dotaz** | hlásí lidi navíc (chybí filtr na ohlášený home office z 5. 8.) | Peťa |
| 10 | **Honomichl — proč se sedmkrát za měsíc neodhlásí** | není to chyba systému, ale opakující se jev u jednoho člověka | Kristý + vedoucí |

**Hotovo a odpadá:** ~~A1 celé minuty~~ · ~~A2 sjednocení `router.py`~~ · ~~zámek období do kaskády~~ ·
~~rozšíření spouštěčů kaskády~~ · ~~nesouměrnost půlnočního automatu~~ ·
~~spouštěče mostu v `.gitignore`~~ (řeší se 19. 8. samostatným deployem).

Zpětně se řeší **jen srpen**, uzavřené měsíce se nesahají — potvrzeno Kristý 17. 8.

**Zbytkový rozdíl, se kterým je potřeba počítat i po všech opravách:** `att_entry.hours` je
`numeric(5,2)`, položky mají 3 desetinná místa. Zaokrouhlení dělá ±0,005 h na záznam — nově
ale náhodně na obě strany, takže se nesčítá jako dřív (dosud šlo vždy nahoru).
