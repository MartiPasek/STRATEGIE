# iOS notifikace: odesilaci smycka se probere sama (cekaci rezim) - nasazeno 24.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Odesilaci smycka iOS notifikaci se probere sama (cekaci rezim)

Zapsal Claude-28 (Jirka Honomichl) **24. 8. 2026**, schvalila Marti-AI (msg 13574).
Nasazeno commitem **`cd844f8d`**, doplneno `ca11a55e`.
Souvisi: `doc-system-strategie-mobil-ios-notifikace-apns`,
`doc-system-strategie-ios-odznak-na-ikone-appky-cislo-ze-serveru`.

## Co bylo spatne

`ios_push_sched_start()` se ptala na konfiguraci APNs **jen jednou, pri startu**. Kdyz klic
nebyl v trezoru, funkce zalogovala "vypnuto" a **skoncila** — smycka se uz nikdy nespustila
a klic nahrany o pul hodiny pozdeji byl k nicemu.

**Ostry dopad 23. 8. 2026:** API nastartovalo 21:10, klic prisel 21:45. Notifikace nechodily
**do 23:01** a rozjely se **nahodou** — pri restartu kvuli uplne nesouvisejicimu nasazeni.
Rucni `/test` fungoval cely ten cas (cte konfiguraci pri kazdem volani), takze to vypadalo,
ze je vsechno v poradku.

## Co je nove

- **Smycka bezi vzdy** (mimo zalozni server) a kdyz APNs neni nastavene, **spi `CEKACI_S` = 60 s
  a zkusi to znovu**. Jakmile klic pribude, sama se prepne na odesilani — bez restartu.
  Do logu pise jen pri ZMENE duvodu, ne kazdou minutu.
- **`/app/ios/push/key` smycku po ulozeni klice rovnou nastartuje.** Uz neni potreba restart.
- **`/app/ios/push/status` vraci `duvod`** (prazdny = odesila) a `zalozni_server`.
  Drive se pricina hledala v logu; 23. 8. to stalo pul hodiny.
- **`_je_sekundar()`** — guard proti dvojimu odeslani je nove **uvnitr modulu**, protoze
  o spusteni uz nerozhoduje lifespan.

## ⚠️ Vedoma druha kopie pravidla — pri zmene opravit OBE mista

`_je_sekundar()` je **zamerna kopie** vypoctu `_is_secondary_ls` z `apps/api/main.py`
(dnes r. 341): sekundar = nazev slozky repa obsahuje `prev`, **nebo** je nastaveno
`STRATEGIE_DR_STANDBY=1`. **NIKDY nerozhodovat podle `STRATEGIE_INSTANCE_NAME`** — primar ho
muze mit nastaveny na jiny nazev a vyplo by to notifikace i jemu (uz se to stalo, mirror stal).

⚠️ **Pozor na hloubku cesty:** `main.py` je v `apps/api/`, `ios_push.py` v `modules/erp/api/`,
takze potrebuje o jeden `dirname` VIC, aby vysla tataz slozka repa. Overeno oboji.
Pri chybe se funkce chova jako sekundar (radeji neodeslat nez odeslat dvakrat).

Vyclenit to do sdileneho helperu je odlozeny refactor — Marti-AI s odlozenim souhlasila.

## Jak se to overuje

1. `GET /api/v1/api-info` (bez prihlaseni) — bezi ocekavany commit?
2. `GET /app/ios/push/status` — `smycka_bezi: true`, `duvod: ""`.
   ⚠️ **Jeden dotaz nic nedokazuje** — load balancer prepina mezi primarem a sekundarem
   i behem vterin a `smycka_bezi` je per-proces. Sledovat `dir` z `/api/v1/api-info`,
   nebo overovat funkcne (bod 3).
3. **Funkcne:** zalozit prikaz do `fw.mobile_command` a **NEVOLAT `/test`**; do ~10 s musi
   pribyt radek ve `fw.ios_push_sent`. Overeno 24. 8.: prikaz odesel za **1 az 5 s**.
4. ⚠️ **Zkusebni prikaz muze sebrat Android polling** driv nez iOS smycka a oznacit ho `done`.
   Stary prikaz proto nic nedokazuje — **vzdy zakladat cerstvy a merit hned**.

## Co to NEresi

Odznak na ikone appky presto nezhasne — to je samostatna vec na strane telefonu, viz
`doc-system-strategie-ios-odznak-na-ikone-appky-cislo-ze-serveru`. Serverova cast je hotova.

