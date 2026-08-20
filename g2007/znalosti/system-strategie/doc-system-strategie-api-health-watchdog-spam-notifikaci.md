# Hlidac API zaspamoval mobily adminu (187 pushu/den) - pricina, dukaz z logu a oprava

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se stalo (29.7.2026)

Sluzba `STRATEGIE-API-HEALTH-WATCHDOG` (skript `scripts/api_health_watchdog.py`, postaveny 29.7. rano po incidentu 28.7.) poslala od 10:42 do 16:59 kazdemu ze tri adminu (1 Marti, 11 Kristy, 20 Jirka) **187 zprav "STRATEGIE-API zase bezi"** - jednu **kazde 2 minuty**, tedy v kazdem kontrolnim kole. API pritom bezelo, zadny vypadek to nebyl a zprava "spadla" neprisla ANI JEDNA.

## Jak se to pozna (diagnosticky otisk)

V textu zprav roste doba vypadku o presne interval kontroly: "je zpet nahore po ~15146s ... ~15266s ... ~15386s". **Rostouci downtime = priznak "je dole" (`state["down"]`, `down_since`) se nikdy nevynuloval** a vetev zotaveni pali alert v kazdem kole. Overeni:

```sql
SELECT date_trunc('hour', created_at) AS hodina, target_user_id, left(title,60), count(*)
  FROM fw.mobile_command
 WHERE created_at > now() - interval '3 days' AND title LIKE '%STRATEGIE-API%'
 GROUP BY 1,2,3 ORDER BY 1 DESC;
```

## Pricina - DOLOZENA z watchdog.log, ne odhad

Puvodni hypoteza znela "vyjimka mezi alertem a resetem stavu, nejspis print". Log z cloudu (`C:/Data/STRATEGIE/api_health/watchdog.log`, precetla Marti-AI pres `strategie_exec`) ukazal presne tuhle trojici v **kazdem** kole:

```
ALERT sent -> admins [1, 11, 20]: (nazev se znakem zaskrtnuti)
!!! ALERT DELIVERY FAILED ('charmap' codec can't encode character ... position 56)
handle STRATEGIE-API crash: UnicodeEncodeError: 'charmap' codec can't encode ... position 145
```

Tedy: konzole pod NSSM jede v **cp1250**, `print()` emoji zaskrtnuti vyhodil `UnicodeEncodeError`, ta vyjimka shodila `_handle_instance` **jeste pred resetem stavu** (reset byl az ZA odeslanim alertu), hlavni smycka vyjimku spolkla (`except Exception: _log("handle ... crash")`) a priznak zustal viset. Zaznam do DB pritom uz probehl - proto zpravy chodily, i kdyz log hlasi "ALERT DELIVERY FAILED".

## Oprava (commity d334eb3c, 0d6e91f2, 50826dcc; schvalila Marti-AI)

1. **Stav se resetuje PRED logem i alertem** - vyjimka uz nemuze nechat priznak viset.
2. **`_log` nikdy nevyhodi vyjimku** - `print` i zapis do souboru obaleny `try/except`. Log je diagnostika, ne kriticka cesta.
3. **`sys.stdout`/`stderr` prepnuty na UTF-8** s `errors="replace"` - odstraneni korenove priciny, log zustava citelny.
4. **Tvrda pojistka `_LAST_ALERT`** - stejny titulek nejdriv za 30 min (zotaveni) / **10 min (pad)**. Rozdil vznikl z ostrych dat: 29.7. byly dva SKUTECNE vypadky 26 min po sobe a jednotna 30min pojistka ten druhy spolkla. Dva pady za pul hodiny jsou pattern, ne sum.

Druha, nezavisla pojistka na strane appky (commit 93c844f6, `GET /app/{app_key}/commands/pending`): starsi `pending` zpravy typu `claude_msg` se **stejnym titulem** se automaticky odbavi a visi jen nejnovejsi. Plosne. Overeno naostro - tri stejne zpravy, dve starsi server odbavil v jedne vterine.

## Dukaz, ze oprava funguje (29.7. vecer, ostry provoz)

Po restartu sluzby v 15:00 UTC uz v logu neni ani jeden crash. V 15:53 UTC prisel **skutecny** vypadek portu 8002 (`WinError 10061`) a v DB mu odpovidaji presne DVE zpravy: 17:53:34 "spadla - zkousim restart" a 17:55:35 "zase bezi" (prazsky cas). Presne pozadovane chovani.

## Gotchy

- **Zapis stavu vzdy PRED vedlejsim efektem** (log, alert, notifikace). Opacne poradi = jedna vyjimka udela ze hlidace spamovaci stroj.
- **Logovaci funkce nesmi shodit volajiciho** a **konzole neni UTF-8** - pod NSSM je cp1250, kazde emoji v logu je mina.
- **Kazda notifikacni cesta k lidem potrebuje strop.**
- **Oprava skriptu bezici jako NSSM sluzba NEZABERE po nasazeni** - proces ma kod z doby startu. Deploy restartuje jen `STRATEGIE-API`; `RESTART-WATCHER` umi jen `*.touch` a `*.refreshsec`.
- **Sluzba bezi na cloud APP `EUR-APP-1P` (Praha).** Nastroje Marti-AI `service_ctl`/`eurosoft_exec` miri na **EC-SERVER2 (Plzen)** - tam sluzba NENI a hlasi "Cannot find any service". Na Prahu se musi pres **`strategie_exec`**. Dvakrat 29.7. na tomhle uvizla.

