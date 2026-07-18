# 221 — GO VP: široká mapa oddělení (lidé · pošta · portfolio)

**Stav:** anatomie oddělení · 18. 7. 2026 · Claude (C23), z reálného širokého passu · PoC celé firmy

Pohled „ze široka" na život celého oddělení Vedení projektů (VP): kdo v něm je, kudy teče pošta, jaké nese portfolio. **Trvalá anatomie — NE denní stav** (ten je efemérní, patří do denní vrstvy dok 220). Grounded na reálném dotazu do produkce 18. 7. 2026. Data jsou otevřená — ve firmě nejsou čísla, se kterými bych neměl přijít do styku (Marti 18. 7. 2026).

---

## 1. Lidé — za koho neseme odpovědnost
Oddělení není „Eliška + zástup". Je to síť lidí i AI, kteří na zakázkách reálně dělají. Podle korespondence a přiřazení k 18. 7.:

- **Eliška Kolářová** (user 34, `e.kolarova@eurosoft.com`) — vedoucí VP, nese **ABSAUGWERK** (32 zakázek, největší zákazník). Vlastní schránku (108 doručených / 82 odeslaných). Status uživatele: *pending*.
- **Petra Dvořáková** (user 40, `p.dvorakova@eurosoft.com`) — Eliščin zástup (3.–17. 7., právě skončil), napojená na `schaltschrankbau@`. Status: *pending*.
- **Zdeněk Čepický** (`z.cepicky`) — elektroprojektant EPLAN, vytížený; objevuje se jako druhý korespondent na ABSAUGWERK zakázkách (`e.kolarova, z.cepicky`).
- **Pavel Zeman** (user 30, `p.zeman@eurosoft.com`) — největší osobní schránka oddělení (2535 doručených, 1136 odeslaných, historie od ledna 2026). Obchodní/řídící uzel.
- **Kristý** (user 11) — řešitel na 3 zakázkách. Rodič systému.
- **Řešitelé-AI už reálně nesou zakázky:** Claude-24 (7 zakázek), Claude-29 (2). To není teorie — instance už v `resitel` figurují. GO VP PoC tady navazuje, nezakládá na zelené louce.
- Dílčí řešitelé: Erika Sedláčková (45), Ondřej Pillár (21), Zdeněk Diviš (43) — po 1–2 zakázkách, status *pending*.
- **Řešitel „360"** — 7 zakázek, uživatel toho id v `public.users` není (skupina/persona?). Otevřená otázka k dořešení.

## 2. Pošta — nervový systém oddělení
Mail neteče přes `public.mailboxes` (tam je jen `marti-ai@eurosoft-control.cz`). Teče přes **mirror joby** do `tenant.mail_message`, per `user_id` + `slozka`. Klíčové schránky:

- **`projects@` (user 111, „sběrná schránka VP")** — centrální nálevka oddělení. **1680 doručených, z toho 1191 nepřečtených.** Za normálu ~1536 zpráv / 30 dní. Tady se sbíhá celá poptávková realita firmy.
- **`faktury@` (user 113, sdílená)** — 300 doručených, fakturační tok.
- **Eliška (34)** — 108 doručených (9 nepřečtených), 82 odeslaných, 10 konceptů.
- **Pavel Zeman (30)** — 2535 / 1136.

### ⚠️ ZJIŠTĚNÍ: zelený job, mrtvá data (blackout od 7. 7.)
`fw.mirror_job` hlásí pro `sync_mail_projects` / `sync_mail_eliska` / `sync_mail_pzeman` **`last_status = ok`, běh každých 15 min, dnes 12:44** — vypadá to zdravě.

Realita v datech: **`max(datum)` i `max(synced_at)` napříč VŠEMI schránkami = 7. 7. 2026 17:54.** Pro `projects@` je jediné `synced_at` v posledních 25 dnech **7. 7.** (jednorázový import 1680 zpráv), nejnovější mail 7. 7. 10:04. Od té doby **11 dní ticho** v nálevce, která normálně bere ~50 zpráv denně. Job přitom pořád hlásí „ok, 111 řádků" — přečte stále stejných 111 starých zpráv a nic nového nezapíše (nejspíš vypršelý EWS token 7. 7.).

**Poučení pro bod 2 (čerstvost = zdraví automatu):** dok 220 říká „čerstvost ověř přes zdraví automatu, ne odhadem". Tento pass to **prohlubuje**: *samotný `last_status=ok` NESTAČÍ.* Zelený job umí schovat mrtvou rouru. **Kontrola čerstvosti musí sahat na data — `max(synced_at)` v cílové tabulce proti intervalu — ne jen na status jobu.** Náš `check_vp_freshness` (kouká na `mirror_job.last_status/running`) by právě teď hlásil ZELENOU, zatímco `projects@` je 11 dní slepá. To je přesně ta past, kterou má bod 2 chytat — a zatím ji nechytá.

## 3. Portfolio — 113 zakázek
Rozložení podle fáze (celý flow poptávka → nabídka → objednávka → materiál → výroba → odvoz → fakturace → zaplaceno):

- **5 Materiál — 45** (zdaleka nejvíc; drží se tu, čeká na/na materiálu) · termíny hlavně 30. 9.–14. 10.
- **9 Zaplaceno — 25** (uzavřené)
- **4 Objednávka — 21**
- **7 Odvezeno — 18**
- **1 Nová — 2**, **8 Fakturováno — 2**

**Fáze „5 Materiál" je zádrž oddělení** — skoro polovina portfolia stojí v jednom kroku. Aktivní (nezaplacený) pipeline ≈ 88 zakázek.

**Zákazníci** (koncentrace): **ABSAUGWERK GmbH 32** (28 %), Erwin Junker 17, SENCO Příbram 9, Siemens 8, MOLINS 6, AAGM 6, INTERSOFT 4 — a dlouhý chvost ~25 dalších (rbc robotics, PEŠEK, FRIMO, Polytechnik, BMW, Tesla, StrikoWestofen…). Oddělení je německo-české strojírenské B2B. (`HonzaTest`, `EUROSOFT-Control` = testovací/interní.)

**Ownership gap:** pole `resitel` je vyplněné jen u **23 z 113** zakázek — a většinou u starých „duchů" (Claude-24/29, 360) s termíny roky v minulosti. U reálných čerstvých ABSAUGWERK zakázek je `resitel` prázdný; skutečného vlastníka prozrazuje až `koresponduje` (kdo píše maily). **Kdo na čem dělá se netrackuje ve `resitel`, ale v korespondenci.**

## 4. Operativa — co má oddělení na talíři
`tenant.eliska_rizeni` je už dnes hotový kurátorovaný kokpit (ABSAUGWERK, 22 řádků) — sám počítá fázi, `dni_do_terminu`, efektivitu a **`dalsi_krok`** se semafory:

- 🔴 **PO TERMÍNU** — VR10636 (odvoz 15. 7., −3 dny)
- ⚠️ **termín v Eliščině volnu** — VR10675 (8. 7., −10)
- 🟡 **čeká na výrobu — hlídat postup** — hlavní masa (materiálová fáze, termíny srpen)
- — **sledovat** — odvezené před fakturací

Mimo Eliščin objektiv (`vp_flow_vyroby`) hoří i: MOLINS VR10665 (−15), SENCO VR10662 (−11) — bez řešitele, bez korespondence. „Duchové" s termíny −350 až −1844 dní (VR9079, VR8868…) zaseklí ve fázi 4/5 kalí flow a patří na úklid.

**Pozor na provázanost s bodem 2:** poslední maily u ABSAUGWERK zakázek končí 17. 6.–3. 7. — přesně sedí na mailový blackout. Operativa vypadá „utichlá", ale je to slepá nálevka, ne klid na zakázkách.

## 5. Co to znamená pro GO VP jako PoC firmy
1. **Kostra už žije ve views** (`eliska_rizeni`, `vp_flow_vyroby`, `vp_zastup_readiness`) — Mapovač konzumuje, nepočítá z nuly (potvrzuje dok 220).
2. **Freshness-automat musí být data-based**, ne job-status-based. První konkrétní úprava: `check_vp_freshness` → kontrolovat `max(synced_at)` v `tenant.mail_message` proti intervalu, eskalovat při stáří > práh. Blackout 7. 7. je živý testcase.
3. **Ownership přes korespondenci, ne `resitel`** — jakýkoli „kdo to má" pohled musí číst `koresponduje`, dokud se `resitel` nezačne plnit.
4. **Úklid duchů** — staré zakázky s termíny v hluboké minulosti zkreslují každý agregát; oddělit „živé" od „archivních".
5. **projects@ (1191 nepřečtených)** je největší nevyužitý zdroj i největší riziko — jakmile se roura opraví, je to první doména pro triáž-konzumenta z dok 220.

---
*Zapsal Claude (C23) zevnitř, 18. 7. 2026. Navazuje na dok 220 (Mapovač) a dok 210 (poschodový stroj). Denní stav sem NEPATŘÍ — tohle je anatomie, ne fotka dne.*
