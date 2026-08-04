# Předávka pro další konverzaci — Peťa (Claude-26)

**Zapsáno:** 4. 8. 2026, po konverzaci od ~28. 7. do 4. 8.
**Pro koho:** další instance Claude-26, která se probudí bez paměti.
**Čti spolu s:** `docs/team/Peta26_pokyny.md` (trvalé pokyny — ta má přednost).

---

## 0) Než napíšeš první řádek

1. `CLAUDE_PULL_GO.txt` (git pull přes most) — jinak edituješ zastaralé soubory.
2. Přečti `docs/team/Peta26_pokyny.md` celé.
3. Spusť hlídače: `SELECT * FROM tenant.pojistky_check();` — vrací **jen to, co je rozbité**.
   Když něco vrátí, řeš to dřív, než začneš nové věci.
4. Peťa jede na **lane 1** mostu (`CLAUDE_SQL.sql` / `CLAUDE_GO.txt` / `CLAUDE_OUT.txt`).

---

## 1) Kdo je Peťa a jak s ní pracovat

Petra (user **18**), mzdová a finanční agenda EUROSOFTu. Dělá **docházku, absence
a mzdové podklady**. Není programátorka — mluv s ní česky, lidsky, cizí slovo vždy
vysvětli v závorce.

**Co se osvědčilo:**

- **Neptej se zbytečně, dělej.** Když je zadání jasné, udělej to a napiš výsledek.
- **Krátce.** Dlouhé odpovědi nečte celé. Nejdřív závěr, pak detail.
- **Když něco pokazíš, řekni to sám a hned.** Ona to nese dobře, ale musí to vědět —
  pracuje s daty, která jdou do mezd.
- **Ověřuj v datech, nehádej.** Několikrát jsem si vymyslel název sloupce a padalo to.
  Vždycky nejdřív `information_schema.columns`.
- **Když tě opraví, přestaň obhajovat hypotézu.** Má lepší doménový instinkt než já.
  Několikrát mě zachránila (viz „moje chyby" níže).
- Píše rychle, s překlepy a bez diakritiky. Neopravuj ji, čti přes to.

---

## 2) Co drží celý systém (bez tohohle nic nepochopíš)

### Dvě vrstvy docházky

| Vrstva | Tabulka | K čemu |
|---|---|---|
| **Hlavička** | `tenant.att_entry` | Časy, hodiny, typ, absence. **Pravda pro mzdy.** |
| **Položky** | `tenant.vyroba_work` | Rozpad hodin na zakázku + činnost. |

**Absence do `vyroba_work` NEPATŘÍ.** Rozpad musí souhlasit s docházkou v hodinách —
kontrola „rozpad vs. docházka" tohle porovnává.

### Identita řádku ve Správě docházky

- `Z:<id>` = žádost (`att_absence_request`), která **ještě není rozepsaná do dnů**
- `D:<id,id,…>` = denní záznamy (`att_entry`) poskládané do období

### Výpočet hodin

`tenant.att_den_hodiny(tenant, od, do)` — jedno sdílené místo. Sloučené pracovní
úseky minus přestávky plus `fond_doplneni`. Nepočítej hodiny nikde jinde znovu.

### Typy automatu

- `nenarokova` — hodiny **nad** fond (+)
- `fond_doplneni` — **dopíchnutí** do fondu (−)

Tyhle dva jsou surovina pro budoucí **konto přesčasů**.

### Zámky

- `att_period_lock` — **tvrdý zámek měsíce**. Zavřený měsíc se nemění. Nikdy.
- `local_lock=true` — chrání ručně opravený řádek před přepsáním z Centrály.
  **Při rušení dnů (`_znic_dny`) je POVINNÝ** (Jirka, 30. 7., commit `b05c15ed`).

---

## 3) Pravidla, která Peťa rozhodla (jsou závazná)

1. **Zápis správce platí hned** — nečeká se na schválení.
2. **Editovat jde všechno včetně Centrály** — synchronizace z Centrály je vypnutá.
3. **Home office je JEN informace** — nesmí se promítat do docházky.
   ⚠️ *Schválený HO se do docházky pořád promítá — rozpor, leží u Kristý.*
4. **Dovolená / DN / SD se promítají bez ohledu na schválení.**
5. Kdyby to pak vedoucí zamítl — „to budeme řešit, až to někdo bude řešit".
6. **Žádná hláška o úspěchu.** Jen chyby, a to vyskakovacím oknem uvnitř stránky
   (`prompt()`/`confirm()`/`alert()` prohlížeč v iframe **tiše blokuje** — nepoužívej je).

---

## 4) Hlídač (`tenant.pojistka`)

Peťa ho chtěla, protože *„mám pocit, že spolu něco uděláme a pak je to zase špatně"*.

- `SELECT * FROM tenant.pojistky_check();` → vrací **jen rozbité** kontroly.
- **Každou novou dohodu s Peťou tam zapiš.** To je její výslovný požadavek,
  platí i pro budoucí konverzace.
- ⚠️ **Kontrola musí být skutečná.** Já jsem jednu založil s `... OR true` na konci —
  vždycky prošla, čili falešná jistota. Když kontrolu nejde napsat, radši žádnou
  nezakládej, než aby lhala.
- ⚠️ **Než založíš pojistku, ověř si fakt u Peti.** Postavil jsem `pravo-vidi-vsechny`
  podle názvu Kristýina commitu a bylo to špatně. Správně:
  **Michelle Šafránková (17) vidí všechno** jako Peťa; **Michaela Hladíková (16)
  vidí jen výrobu** jako Dušan.

---

## 5) Architektura „kód jako data" (Marti, 2. 8.) — DŮLEŽITÉ

- `g2007.python` — backend kód jako řádky v databázi, spouští se přes
  `erp_registry.call`, **bez restartu**.
- `g2007.soubor` — webové soubory v databázi, materializují se na disk.
- **`router.py` se needituje přímo — nejdřív migrace.**
- Mzdy zatím **nejsou** přemigrované. Známá chyba: `jednatel_stravne`.

---

## 6) Moje chyby v téhle konverzaci (ať je neopakuješ)

| Co jsem udělal | Co z toho plyne |
|---|---|
| Hádal názvy sloupců (`ee.rule_id`, `em.active`, `ds.updated_at`…) | Vždycky nejdřív `information_schema`. |
| `s.rollback()` v pomocné funkci zahodil volajícímu rozdělanou práci → *„napsalo smazáno, ale nesmazalo se"* | Nepovinné bloky jistit **SAVEPOINTem** (`_Kousek`), po zápisu **ověřit čtením**. |
| UPDATE bez filtru data sáhl na **72 řádků v zamčeném červnu** | Při přímém SQL vždy omezit datem a zkontrolovat zámek měsíce. |
| Řekl jsem Peti, že Hladíkové blok HO je duplicita — nebyl | Nedávej jistotu, kterou nemáš. Ona podle toho maže data. |
| V kontrole rozpadu jsem vynechal `homeoffice` a párovat úseky 1:1 podle času | Jeden docházkový blok se rozpadá do víc úseků zakázek. |
| Nechal jsem ji spustit git příkazy na notebooku místo cloudu | Ověř, na kterém stroji běží, než jí pošleš příkazy. |
| Založil jsem pojistku s `OR true` | Viz výše — falešná jistota je horší než žádná. |

**Nejdůležitější vzorec:** *tichá chyba* — obrazovka napíše „hotovo" a nic se
neuloží. Po každém zápisu **ověř čtením z databáze**, ne podle návratovky.

---

## 7) Co je hotové (nesahej na to, ledaže by to bylo rozbité)

- Jirkovy sloupce **číslo řádku** + **zdroj** ve Správě docházky, zdroje v češtině.
- **Plná správa absencí** — přidat / opravit / smazat, s auditem, notifikací,
  respektem k zámku měsíce a přepočtem zůstatků.
- Typ absence **Ostatní/Nepřítomen – s náhradou mzdy**.
- Index `ux_att_entry_source_den` (dřív šla rozepsat jen 1 den z vícedenní dovolené;
  23 nepromítnutých žádostí doplněno).
- `router.py` obnoven po hromadném smazání (`45848042`).
- Strom na jeden klik, Ctrl+klik odznačí, filtry per pohled, export CSV s `;`
  a desetinnou čárkou, žádné hlášky o úspěchu.
- **4. 8.:** Opravy docházky — zahazování opožděných odpovědí (`DAY_SEQ`), datum
  v hlavičce dne. Tím padá riziko *„opravím docházku cizímu člověku"*
  (Brudnová × Hájek 24. 7.). Commit `39ab98b1`.

---

## 8) Co zbývá

| Věc | Stav |
|---|---|
| **Konto přesčasů** — přehled `nenarokova` × `fond_doplneni` | **Až po výplatách.** Chce ruční počáteční stav k 31. 7. (červen má 677,5 h nad fond a nula dopíchnutí). Ukáže lidi v mínusu. |
| **15. podmínka „Nevede docházku"** (Vlková, Senft, Mozer, Pašek 2 a 41) | Peťa se domluví se Šárkou. |
| Dopíchnout chybějící celé dny člověku, co si vybíral náhradní volno | Až přijde na řadu. Musí se přidat SQL jako `fond_doplneni` — v Opravách ten typ není. |
| Zbytek nesouladů rozpad × docházka (10 dnů) | Saad Jarrar 3×; Sedláčková 30. 7. = neukončený úsek zakázky 12:45–17:08 proti docházce do 14:40. |
| Schválený **home office se pořád promítá** do docházky | Rozpor s pravidlem 3. Leží u Kristý. |
| Dvojí import absencí (`ec_real` + `ec_sumaden`, 448 osobodnů) | Doména Kristý. Příčina: kontrola hledá jen `is_active=true`. |
| `holiday_balance` — nárok na dovolenou se nikdy nepočítá | Otevřené. |

---

## 9) Technika mostu — co mě zdrželo

- **HTTP 401 „Nejsi přihlášen"** se objevuje opakovaně. `restart_self` nepomůže,
  po chvíli odejde samo. Nepanikař.
- **Přespuštění dotazu vyžaduje změnu obsahu `CLAUDE_SQL.sql`**, nestačí přepsat
  `CLAUDE_GO.txt`.
- **Nikdy git přes bash mount.** Pull přes `CLAUDE_PULL_GO.txt`, deploy přes
  `CLAUDE_DEPLOY.txt` + `_GO`.
- Konflikt v `WORK_LOCK.txt` umí zablokovat úplně všechny commity.
- V Postgresu **nefunguje `(?s)`** v regulárních výrazech; výstup z mostu navíc
  slučuje řádky — na náhrady používej `regexp_replace` s kotvou.
- Po každém uzavřeném bloku práce pošli Peti souhrn (`CLAUDE_NOTIFY.txt`, `user=18`).

---

*Zapsal Claude-26, 4. 8. 2026, na Petin pokyn „udělej si prosím pro sebe zápis
do další konverzace z celé této konverzace".*
