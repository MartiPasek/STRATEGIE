# Přehled „Plnění FPD" pro výrobu — zadání

**Zadal:** Dušan Havlát (vedoucí výroby) přes Jirku Honomichla · **Sepsal:** Claude-28, 22. 7. 2026
**Stav:** zadání odsouhlasené Jirkou po rozhovoru s Dušanem, PŘED konzultací s Marti-AI. Nic není postaveno.

FPD = **fond pracovní doby** (kolik hodin má člověk za období odpracovat).

---

## 1. Odkud požadavek přišel

Dušan: *„další důležitý je přehled Nesplněný FPD"* + screenshot z Centrály.
V Centrále jde o dva přehledy v `EC_DELPHI_TabObecnyPrehled`:

| přehled | ID / číslo | filtr | hodiny |
|---|---|---|---|
| Docházka – Hlídání FPD HPP | 1081 / 1088 | `DruhSmlouvy=2`, vyloučeni 21, 41, 15, 2, 47, 361 | `SUM(EC_Dochazka.CasCelkemInterni)` |
| Docházka – Hlídání FPD OSVČ | 1603 / 5509 | `DruhSmlouvy=3` **a** `NeplacenyPrescas>0`, vyloučeni 9017, 9030, 9031, 9103 | `SUM(CasCelkemZakazka)` |

Společná logika originálu: hodin denně = `EC_FinZamPodminky.RealUvazekT / 5`; pracovní dny = `EC_Svatky`
bez víkendů a svátků, oříznuté datem nástupu/odchodu; „má být odpracováno" = hod./den × prac. dny;
období = aktuální měsíc do včerejška, ale **do 12. dne v měsíci ještě celý minulý měsíc**;
skupina = konkatenace z `EC_SkupinyVazby` / `EC_Skupiny`.
Menu uzel Centrály: `EC_CentralaMenu` id 456 „Nesplněný FPD".

## 2. Co jsme zjistili PŘED zadáním (proč to není prostý port)

Ověřeno na živých datech 21. 7. 2026:

1. **Docházka z Centrály do STRATEGIE teče** — `_sync_ec_dochazka_recent()` (router.py:25325) přes
   `_maybe_sync_ec_dochazka()` (router.py:25485): throttle 5 min, **okno 3 dny**, piggyback na netscan.
   `EC_Dochazka` (kromě `Autor='STRATEGIE'`) → `att_entry` se `source_system='centrala1'`,
   `source` dle `LoginFrom` (D→tablet, C→manual, A→mobile_app). Lidé s `att_source_pref.app_only` se přeskakují.
   Hlubší měsíční sync (`_sync_dochazka_ec` / SumaDen z MIGRACE hubu) běžel naposledy **8. 7. za červen**.
2. **Data se ale rozcházejí, a to o celé směny** (červenec):
   - os. č. 486: Centrála 107,55 h vs u nás 91,55 h (**−16 h** — 8. a 9. 7. dopsané v Centrále, u nás chybí)
   - os. č. 493: Centrála 105,78 h vs u nás 113,78 h (**+8 h** — 7. 7. máme dvakrát)
   - dalších ~8 lidí ±8 až ±16 h
   Příčina je strukturální: sync má okno 3 dny a **nemaže** — zpětné opravy v Centrále se k nám nedostanou
   a naše přebytečné řádky nezmizí. FPD je kumulativní číslo za měsíc, takže se do něj každá odchylka nasčítá.
3. **Marti-AI (21. 7., msg 11048)** proto nedoporučila počítat FPD z našich dat a navrhla číst čísla přímo z EC:
   *„Kdyby Dušan FPD přehled dostal a viděl špatná čísla, ztratí důvěru v celý systém — a to je horší
   než nemít přehled vůbec."*

## 3. Řešení, na kterém se domluvili Dušan s Jirkou

Místo volby „číst z Centrály vs. číst od nás" → **číst od nás + dát Dušanovi nástroj, kterým rozpory sám vyřeší.**
Cílem je, aby **pravdivá data byla ve STRATEGII** (Jirka, 22. 7.).

## 4. Zadání

### 4.1 Dva přehledy
- **„Plnění FPD HPP"**
- **„Plnění FPD OSVČ"**

(Fond OSVČ se počítá jinak než u HPP → záměrně oddělené, ne jeden grid se sloupcem typ.)

### 4.2 Rozsah lidí
**Podřízení Dušana** — org podstrom pod postem „Vedoucí výroby" (dnes VIEW `tenant.vyroba_dusan_team`,
36 lidí; v týmu **25 HPP + 8 OSVČ** + 2 bývalí + 1 bez engagement).
Nezobrazuje se celá firma jako v Centrále.

### 4.3 Obsah
Sloupce podle originálu (odpracováno · pracovní dny · hodin denně · má být odpracováno · rozdíl ·
měsíc · ke dni · skupina), ale:

**Ukazuje obě strany — dlužníky i lidi nad fondem** (přesčasy). Důvod: hlídání přesčasů chce po Dušanovi
Marti Pašek. Proto i změna názvu z „Nesplněný FPD" na **„Plnění FPD"** — není to 1:1 kopie centrálového přehledu.

### 4.4 Akce „Porovnat s Centrálou" (jádro zadání)
Tlačítko nad přehledem:

1. Porovná odpracované hodiny **STRATEGIE × Centrála (`EC_Dochazka`)** per člověk × den.
2. Rozsah: **aktuální měsíc**; a navíc **předchozí měsíc, dokud není uzavřené mzdové období**
   (`tenant.att_period_lock`; k 22. 7. 2026 je zamčeno 1–6/2026, takže dnes by šlo o červenec).
3. Vypíše **rozpory** s typem: chybí u nás den · máme den navíc / duplicitu · liší se hodiny.
4. U každého rozporu Dušan rozhodne: **vzít do STRATEGIE** / **nechat být**.
5. Rozhodnutí se zapíše do naší docházky (`att_entry`) — Dušan k tomu **už má oprávnění**
   (`_att_fix_scope(41) = 'vyroba'`, editor oprav pro výrobu od 10. 7. 2026).
6. Zamčené období = zápis nejde (fix-endpointy vrací 409) — musí odemknout Peťa/Šárka.

### 4.5 ⚠️ Do Centrály se NEZAPISUJE
Rozhodnutí Jirky (22. 7.): **žádné zpětné zápisy do Centrály.** Opravuje se jen STRATEGIE,
protože o ni nám jde. (Otevřená otázka na Marti-AI: důsledky pro mzdy, které dnes jedou z Centrály/Heliosu.)

### 4.6 Kdo se k přehledu dostane
Postavit **jednou, na jednom místě**. Primárně Dušan; přístup Peti (kanceláře) a Míši (výroba)
je pak **jen otázka práv v ERP**, ne další kopie přehledu.

## 5. Ověřená fakta k implementaci

| věc | zjištění |
|---|---|
| HPP × OSVČ u nás | `tenant.engagement.engagement_type` = `hpp` / `osvc` (+ `druh_text` „HPP"/„OSVC") |
| fond | `engagement.uvazek_tyden_h` (40) vyplněný **i u OSVČ**; ⚠️ `fond_mesic_h` viz níže — NEPOUŽITELNÝ |
| píchají OSVČ u nás? | **ano** — všech 8 OSVČ z týmu má červencovou docházku (staré i nové píchání) |
| pracovní dny / svátky | `tenant.att_calendar_day` (`is_workday`, `is_holiday`) — ⚠️ naplněno jen do konce roku 2026 |
| zámek období | `tenant.att_period_lock` + `_att_period_locked()`; zamčeno 1–6/2026 |
| působnost editora | `tenant.att_fix_scope`; Dušan = `vyroba` = jeho org podstrom (bez kvalifikačních postů) |

## 6. Závěry konzultace s Marti-AI (22. 7. 2026, msg 11063)

### 6.1 🛑 Bod „nezapisovat do Centrály" musí rozhodnout Marti Pašek — BLOCKER
Marti-AI to odmítla vzít na sebe:
> *„Dokud jsou mzdy počítané z Centrály/Heliosu, Centrála je **legal record** pro mzdové účely. …
> Dušan vidí správná čísla u nás, ale zaměstnanec dostane výplatu podle jiných. Když si toho nikdo
> nevšimne = problém u mzdy. Když si toho někdo všimne = problém právní. To není rozhodnutí,
> které mohu vzít já s Jirkou."*

**Stav:** 22. 7. 07:32 odeslán e-mail Martimu (`m.pasek@eurosoft-control.cz`, outbox 491/492 = `sent`)
+ 07:33 push notifikace na mobil (id 15473). **Čeká se na jeho odpověď — do té doby se nestaví nic.**

### 6.2 Ochrana proti přepsání syncem (řešení návazné technické pasti)
Bez zámku by další běh `_sync_ec_dochazka_recent` (okno 3 dny) přepsal to, co Dušan právě rozhodl.
Návrh Marti-AI (přijat):
- nový sloupec **`tenant.att_entry.sync_lock boolean DEFAULT false`** (dnes v tabulce NENÍ — ověřeno)
- sync dostane při UPDATE/DELETE podmínku `WHERE sync_lock = false`
- Dušanova rozhodnutí se zapisují se `sync_lock = true`
- typy: „máme navíc" + *nechat* → zamknout náš řádek · „chybí den" + *šup* → INSERT s vlastním tagem ·
  „liší se hodiny" → UPDATE + zámek

Alternativu (overlay tabulka `att_entry_fix`) označila za čistší, ale zbytečně pracnou.

### 6.3 Fond OSVČ — ověřeno, `fond_mesic_h` NELZE použít
Marti-AI varovala, že hodnota může být pevná. **Ověřeno na živých datech 22. 7. — je to horší:**

| typ | fond_mesic_h | úvazek/týden | lidí |
|---|---|---|---|
| hpp | 174 | 40 | 41 |
| hpp | 174 | 35 / 32 / 30 / 20 / **15** | 6 |
| hpp | 152,25 | 35 | 1 |
| hpp | *(NULL)* | 40 | 4 |
| osvc | 174 | 40 | 29 |
| osvc | 174 | 30 | 1 |
| dpp | 11 / *(NULL)* | 5 / – | 2 |

`fond_mesic_h = 174` mají i lidé na 15h týdenním úvazku → je to **konstanta, ne osobní fond**,
a u 5 lidí je NULL. **Fond se proto musí počítat dynamicky** — stejně jako to dělá docházkový automat
a jako to dělá originál v Centrále:

> `(engagement.uvazek_tyden_h / work_mode.dny_v_tydnu) × počet pracovních dnů z tenant.att_calendar_day`,
> oříznuto podle `smlouva_od` / `smlouva_do` (nástup uprostřed měsíce = poměrná část).

Podmínku `NeplacenyPrescas > 0` z centrálového OSVČ přehledu **nezachovávat** — Dušan chce vidět všechny.

---

*Nic z tohoto zadání není implementováno. Blokuje rozhodnutí Marti Paška podle §6.1.*
