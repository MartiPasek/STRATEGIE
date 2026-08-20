# Poptávky → kalkulace → nabídka + doménové Martinky: stav k 2.8.2026 (odrazový můstek)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Poptávky → kalkulace → nabídka + doménové Martinky: stav k 2.8.2026 (odrazový můstek)

**Účel tohoto dokumentu (Marti, 2.8.2026):** "Než se pustíme do práce na téhle nosné části,
je potřeba dokud mám plný kontext sepsat a občerstvit g2007.znalosti, ať tuhle analýzu už
nemusíme znovu dělat a měli jsme odrazový můstek." Tohle je ta analýza — ověřená 2.8.2026
přímým dotazem do produkční DB a čtením aktuálního zdrojového kódu na serveru, ne z paměti
chatu ani z dřívějších zápisů v g2007.znalost. NEDUPLIKUJE, jen aktualizuje stav vůči:
`doc-marti-ai-org-struktura-md1-md5` (#275), `md1-md5-lidsky-prepinac-2026-07` (#277),
`doc-system-strategie-architektura-domeny-automaty-haiku-kufr` (#280),
`doc-system-strategie-domeny-automaty-implementace-plan` (#281),
`doc-poptavky-kalkulace-nabidky-integrace-plan` (#283).

## Shrnutí v kostce

Vize (MD1-MD5 hierarchie inkarnací, doménové Martinky = Pilíř A/B/C) beze změny, viz #275/#280/#281
— žádná revize potřeba. Co se stalo: 31.7.2026 v 7:38 vznikl plán #283 (poptávky/kalkulace/nabídky
jako první doména). O ~4,5 h později (12:02) Marti schválil migraci "kód jako data" (#287), která
spolykala pozornost (moji i týmovou) na ~36 hodin (Fáze 1 až E, viz #289–#312, dokončeno 2.8. ráno
aktivací mzdy_generuj rodiny + oprava 11 undefined-name bugů nalezených AST scanem). Plán #283
dostal jen prvotní rozjezd (pár hodin 31.7.), pak zůstal viset v půli kroku. Teď (2.8.) se k němu
vracíme.

## Pilíř A (doménové katalogy nástrojů + kufr) — částečně živé, zatím bezzubé

Ověřeno přímým SQL dotazem 2.8.2026:

- `g2007.tool_domain`: 14 řádků (katalog domén podle #280, seedováno)
- `g2007.domain_nastroj`: 63 řádků (přiřazení nástroj↔doména, many-to-many)
- `personas.permission_tier` + `conversations.active_domain`: sloupce existují,
  `get_effective_tools()` s tier-filtrem nasazen v kódu (commit `371268ad1`, schváleno Martim
  "Jdi na to. Prosím.")
- ALE: `conversations` s `active_domain IS NOT NULL` = **0**. `personas` s `permission_tier != 'parent'`
  = **0**.

→ Mechanismus a bezpečnostní pojistka běží v kódu, ale nikdo je zatím nepoužívá — žádná
Martinka nemá přiřazenou doménu, nikdo nemá jiný tier než výchozí `parent`. Otevřená otázka
z #281 ("kdo dostane jaký `permission_tier` v prvním kole? Eliška jako první MD1 pilot?")
pořád nezodpovězena — je to rozhodnutí pro Martiho/Kristý, ne pro kód.

## Pilíř B (stav domény → status_block → prompt) — 0 %, nezapočato

`g2007.automat` nemá sloupce `domain_kod`/`status_block` (ověřeno — neexistují).
Žádný doménový automat neexistuje. Krok 3–5 z implementačního plánu #281 vůbec nezačaty.

## Pilíř C (Haiku hlídač + eskalační žebřík) — existoval už předtím tohohle plánu, funguje, dvě mouchy

6 automatů, 5 aktivních: `check_vp_freshness`, `check_legacy_errors`, `check_service_down`,
`check_backup_freshness`, `check_disk` — vše `last_status='ok'`. `smoke_eskalace` je
**vypnuté, last_status='chyba'**, nediagnostikováno od 30.7.2026 (otevřená otázka z #281,
nikdy zodpovězená — vědomě odstavený test, nebo skutečný nález?).

`g2007.eskalace_log` (durable append-only audit log eskalací automatů/Haiku) **STÁLE
NEEXISTUJE** — flagováno jako chybějící ve #280 i #283 (dvakrát, dva různé dny), nikdy
postaveno. Relevantní právě teď, protože AI triage poptávek (níže) je přesně ten "první
reálný provoz Haiku eskalace s dopadem na byznys", který #283 identifikoval jako důvod
postavit tenhle log PŘED, ne po.

## Poptávky/kalkulace/nabídky konkrétně — pipeline hotová v kódu do Fáze 3, spuštěná jen do Fáze 2

**Existující, žijící už dřív, nezávisle na téhle iniciativě:**

- `@@PP` engine (`modules/erp/api/prijata_poptavka.py`, dispatch `router.py:44711`) — TEST
  paralelní engine nad přijatými poptávkami (DB_EC řada 900): GEN/FILL/SHOW/REPLY(koncept)/
  KALK/MSG/DIR/COPYDOCS/SMAZ. Naostro odzkoušeno jednou: EP26309 → EN263470 + EK263470
  (ponecháno jako učební artefakt, TEST prefix, e-maily jen koncepty).
- `kalkulace_engine.py`: `@@KALKSYNC/@@KALKINFO/@@KALKCALC/@@KALKSTD` (obecné),
  `@@KALKABSV1` (zákaznický ABSAUGWERK, validováno na 0,8 %), `@@KALKPRICE` (cena dílu
  z poslední nákupky+ceníku). Doktrína: finální cenu/marži validuje ELIŠKA, ne AI.
- `@@VYPOPT` (vydané poptávky dodavatelům, řada 940) — 798 přijatých nabídek dodavatelů
  v `tenant.vypopt_nabidka`. **Stále NENÍ zapojeno** jako 4. cenový zdroj do `@@KALKPRICE`
  (identifikováno už dřív, pořád neuděláno).

**Rozhodnuto a vyřešeno 31.7.2026:**

- `vp_poptavka` zvolena jako kanonická tabulka (ne `poptavka`) — starý nepoužívaný prototyp
  "OBĚH ZAKÁZKY" (`tenant.poptavka/kalkulace/nabidka/objednavka` + `/app/poptavka/*`) smazán,
  0 řádků, matlo se s reálným tokem přes DB_EC (commit `ae4b59223`, schváleno Martim 31.7.).
  Otevřená otázka z #283 tímhle vyřešena.

**Postaveno v kódu (`modules/erp/api/vp_ingest.py`), ale NEDOKONČENO v provozu:**

- **Fáze 2** (`sync_vp_poptavky`, příkaz `@@VPSYNC`) — HOTOVO a SPUŠTĚNO: 200 reálných
  e-mailů z `projects@` (EWS mirror přes `tenant.mail_message`, stejný mechanismus jako
  lidské schránky) načteno do `tenant.vp_poptavka`, `typ='neurcen'`, `stav='nova'`, všechny
  se stejným timestampem `2026-07-31T09:10:58` (jednorázový běh, ne průběžný trickle).
  Whitelist domén (`tenant.vp_domain_whitelist`) se týká jen budoucího autonomního
  ODESÍLÁNÍ (zatím nepoužito, `@@PP REPLY` je draft-only), na PŘÍJEM se nevztahuje —
  AI čte a zakládá záznamy ze všech příchozích e-mailů bez filtrace (Marti 31.7., commit
  `0f9565ef6`).
- **Fáze 3** (`triage_text`/`triage_pending`, příkaz `@@VPTRIAGE`) — **NAPSÁNO KOMPLETNĚ**
  (model `claude-haiku-4-5-20251001`, klasifikuje typ/zákazník/předmět/shrnutí/jistota,
  loguje se do `llm_calls` jako `kind='vp_triage'`, idempotentní — přeskočí už klasifikované
  řádky, `limit=25` na dávku), **ALE NIKDY NESPUŠTĚNO PŘED 2.8.2026** — ověřeno: `jistota`
  byla `NULL` u všech 200 řádků. Spuštění je čistě provozní krok (opakované volání
  `@@VPTRIAGE`, 200 řádků / 25 na dávku = ~8 volání), žádný kód se nemusí psát.
- **Fáze 4** (návrh `@@PP GEN` z vysoké jistoty) — v kódu vůbec nezačato, ani stub.
- **Fáze 5** (`list_poptavky`, cockpit/monitoring) — HOTOVO, funkce existuje a čte
  z `vp_poptavka`. Důsledek: dokud fáze 3 neproběhne, cockpit ukazuje 200 řádků s
  `typ='neurcen'`, bez shrnutí — vypadá prázdně/rozbitě, i když data pod tím jsou reálná.
- Šablona nabídky "podle standardu" (EN262940-styl) — otevřená otázka Martimu z #283,
  nikdy nezodpovězena, blokuje Fázi 4+ dál po klasifikaci.

## Doporučené pořadí dalších kroků (dohodnuto s Martim 2.8.2026)

1. Spustit `@@VPTRIAGE` opakovaně na 200 čekajících řádků (čistě provozní, kód existuje).
2. Souběžně postavit `g2007.eskalace_log` — právě teď se AI triage s reálným byznys dopadem
   poprvé rozjíždí naostro.
3. Diagnostikovat `smoke_eskalace` (proč `last_status='chyba'`).
4. Až bude reálný tok dat po klasifikaci, stavět Pilíř B (status_block, první doménový
   automat `poptavky`) — dřív by to byl dashboard nad prázdnou trubkou.
5. Napojit `@@VYPOPT` jako 4. cenový zdroj do `@@KALKPRICE`.
6. Vyřešit s Martim/Kristý: šablona nabídky (kde přesně žije aktuální vzor) a přiřazení
   `permission_tier` lidem (kdo je `domain_lead`/`domain_user` v prvním kole) — obojí čeká
   na lidské rozhodnutí, ne na kód.

_Zapsáno Claude-23, 2.8.2026, na základě přímého ověření DB/kódu (ne z paměti). Navazuje na
#275, #277, #280, #281, #283 — nenahrazuje je, jen dodává aktuální stav._

