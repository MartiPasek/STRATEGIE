# 222 — GO VP: trychtýř zakázek — od poptávky k výrobě (co říká projects@)

**Stav:** anatomie životního cyklu zakázky · 18. 7. 2026 · Claude (C23), z hloubkového vytěžení projects@ · PoC celé firmy

Navazuje na dok 221 (široká mapa). Zatímco 221 mapuje lidi/poštu/portfolio, tohle mapuje **jak zakázka vzniká a putuje** — a kde je díra, kterou má GO VP zaplnit. Grounded na 1680 zprávách schránky `projects@` (user 111, okno 17. 6.–7. 7. 2026, pak blackout — viz 221) a na datovém modelu funnelu. Data otevřená (Marti 18. 7.).

---

## 1. Dva pipeliny, ne jeden
Oddělení běží ve **dvou pipelinech, které se v datech nepotkávají**:

- **Výrobní flow** — `tenant.vp_flow_vyroby` (113 zakázek, od fáze „4 Objednávka" dál). To je to, co vidí Eliščin kokpit i Mapovač z dok 220.
- **Obchodní trychtýř** — poptávka → nabídka → (přidělení VR) → objednávka. **Ten ve výrobním flow NENÍ.** Žije jen v mailu `projects@` a v hlavě obchodníka.

Důkaz: z 25 zakázkových čísel (VR####) zmíněných v předmětech `projects@` je **jen 13 ve výrobním flow, 11 mimo něj** (VR10561 — 16 mailů, VR10654 Frimo — 13, VR10660 — 11, VR10643 — 10…). To jsou **živé dealy v jednání, které výrobní mapa nevidí.** Kdo čte jen `vp_flow_vyroby`, je slepý na celý předvýrobní trychtýř.

## 2. Kdo krmí projects@ (18 lidí, ne 3)
Schránka `projects@` je sběrná nálevka — **1664 z 1680 zpráv jsou interní forwardy** (`@eurosoft.com`), od 18 lidí. To je to „oddělení VP" v celé šíři, za které neseme odpovědnost:

martin.pasek (247, skoro vše FW — přeposílá celý provoz), l.horky (205), p.zeman (204), r.hellmayer (198), s.jarrar (171), z.cepicky (141, EPLAN), **e.kolarova (133)**, p.benes (131), t.veverkova (84), **p.dvorakova (63)**, p.kadlec (32), m.spinka (17), r.fuchs (12), m.brejchova (10), schaltschrankbau@ (8), p.kamis (5), t.trunec (2), a.korjenkova (1).

Skutečný obsah (zákazník, deal) je v **předmětu a těle**, ne v `od_email` (to je interní přeposílatel).

## 3. Co v mailu teče — signály funnelu
Klasifikace předmětů `projects@` (17. 6.–7. 7.):

| signál | zpráv |
|---|---|
| nabídka / Angebot / offer | 157 |
| poptávka / Anfrage / RFQ | 98 |
| objednávka / Bestellung / PO | 80 |
| termín / Liefertermin / delivery | 53 |
| faktura / Rechnung / invoice | 34 |
| VR číslo v předmětu | 108 (25 unikátních) |
| reklamace / Mängel | 1 |

Provoz oddělení je **primárně obchodní přední hrana** — nabídky a poptávky, ne výroba. Reklamace skoro nula (dobré).

## 4. Živé dealy v trychtýři (vzorek z konce okna)
Reálné obchodní případy, které v mailu žily k 7. 7. (a ve výrobním flow většinou nejsou):
- **Tesla** — „Request for Quotation - Tesla HV Power Supply Multiplexor" (RFQ, řeší z.cepicky + p.benes).
- **Getec Hanau** — „Anfrage Klemmkasten ECO Abreinigung" (poptávka, r.hellmayer).
- **Pai / Shuaiba Pump Plant C** — „W3N0X288149 … Bestellung" (objednávka, l.horky).
- **STÄUBLI** — „EK262810 Poptávka cenové nabídky na díly" (martin.pasek).
- **Passavant-Geiger** — „Bestellung 4500490530" (objednávka).
- **INTERSOFT-Automation** — „Nabídka licence k užívání systému Centrála" (velký interní thread, 10 lidí).
- **ABSAUGWERK** — „Bestellung BE1261475" (objednávka, e.kolarova + p.dvorakova).

## 5. Číselné soustavy = mapa životního cyklu
Zakázka mění identifikátor podle fáze — kdo tomu nerozumí, ztratí nit:
- **poptávka:** Anfrage / RFQ / „Poptávka …" (bez čísla, klíč = zákazník)
- **nabídka:** naše číslo **EK######** / **CR-##** / Angebot # (např. EK262810, #22251718)
- **objednávka:** **zákaznické PO** — BE1261475 (ABSAUGWERK), 4500490530 (Passavant), W3N0X288149 (Pai)
- **výroba:** naše **VR#####** (VR10654…)
- pak odvoz → **faktura** (Rechnung)

Napojení mail↔zakázka jde přes VR v předmětu, ale **jen dokud VR existuje** — před přidělením VR je deal identifikovaný jen zákazníkem a EK/CR číslem nabídky.

## 6. Datový model funnelu EXISTUJE — ale přední půlka je PRÁZDNÁ
Klíčové zjištění pro GO VP. Tabulky celého cyklu jsou v DB postavené:

**Zadní půlka — plná (legacy sync):**
- `tenant.oz_zakazky` — **5625** (hlavní kniha zakázek, sync `oz_sync_all`)
- `tenant.ec_zakazka_prehled` — 2682
- `tenant.ec_kalkulace_hlav` — **1648** ← to je ten **kalkulační engine z 2014**, živý a připravený
- `tenant.zakazka` — 409

**Přední půlka — prázdná (postavená, dormantní):**
- `tenant.vp_poptavka` — **0** ← a přitom má sloupce `source_email_id, message_id, thread_id, from_email, subject, shrnuti, zakaznik, stav, prideleno_user_id, jistota, zakazka_ref, task_id`. Je to **hotový most e-mail → poptávka → přidělení → zakázka.** Nikdo/nic ho neplní.
- `tenant.nabidka` — 0 (má `poptavka_id, kalkulace_id, cena, platnost_do, stav`)
- `tenant.objednavka` — 0 (má `nabidka_id, poptavka_id, zakaznik_po, cena`)

Takže: **98 poptávkových + 157 nabídkových mailů leží nezpracovaných** (1191 nepřečtených v `projects@`), zatímco strukturní tabulky, které je mají zachytit, jsou prázdné. Přední hrana obchodu je **netrackovaná — jen inbox.**

## 7. Co má GO VP udělat (konkrétně)
Tohle je ta „role KalkulaceAgenta / nabídkáře" z Martiho vize, teď uzemněná na reálné díře:

1. **Triáž-konzument** (dok 220, třída B) čte `projects@` → z každé poptávky/nabídky založí řádek `vp_poptavka`: `shrnuti` (AI výtah), `zakaznik`, `typ`, `jistota`, návrh `prideleno_user_id`, a když existuje, `zakazka_ref` + `thread_id`/`related_email_ids`.
2. **Kalkulant** obaluje `ec_kalkulace_hlav` (engine 2014) — poptávka → kalkulace.
3. **Nabídkář** z kalkulace draftne `nabidka` (draft, NEodesílá — dok 220 zásada e-mailu).
4. **Napojení na mapu a termíny:** `vp_poptavka.zakazka_ref` → `vp_flow_vyroby.cislo_zakazky` → `eliska_rizeni` (fáze, `dni_do_terminu`, `dalsi_krok`). Trychtýř se tím spojí s výrobní mapou v jeden tok.

## 8. Předpoklad, který musí platit první
Nic z výše uvedeného nefunguje, dokud je `projects@` slepá od 7. 7. (dok 221, úkol #44). **Data-based freshness je vstupní podmínka trychtýře** — mrtvá nálevka = prázdný funnel = žádná triáž. Nejdřív roura, pak konzumenti.

---
*Zapsal Claude (C23) zevnitř, 18. 7. 2026. Dvojice s dok 221. Trvalá anatomie cyklu — NE denní stav.*
