# 230 — Automaty dokladů a jejich reakce (stavový stroj dokladu)

**Stav:** návrh k diskusi (strukturní kostra, ať se neztratí kontext) · 18. 7. 2026 (pozdě večer) · Claude (C23), na pokyn Marti
**Navazuje na:** [210 — Poschoďový stroj](210-poschodovy-stroj.md) · [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md) · referenční vertikála [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md) · [Kalkulace / ceníky Vize 1](Z_kalkulace_ceniky_vize1.md)
**Pokračování:** zítra — **přijatá poptávka (Anfrage) → založení kalkulace**. Tenhle doklad otevře reálný příklad, na kterém se ukážou další věci k dostavění.

> Tenhle dokument je **kostra**, ne hotová architektura. Zapisuju ho teď, aby se přes noc neztratil kontext toho, na co jsme přišli. Doplní se, jakmile projdeme druhou vertikálu naostro. Držíme Martiho doktrínu #11 (additivně, ne perfektně): **žádný univerzální workflow engine dopředu.**

---

## 1. Odkud to vyšlo — RFQ jako referenční případ

Vydané poptávky (RFQ) jsme rozchodili NAOSTRO na dokladu **EVP260231** (SEW-EURODRIVE). Když jsme to dodělali, Marti pojmenoval to podstatné:

> „Tohle je vzorový případ dokladového workflow. Podobně to funguje i na jiných dokladech. Přijde poptávka. Musí se založit. Musí se začít zpracovávat. Založit kalkulaci. Připravit nabídku. Zjistit dostupnost dílů ve skladu. Ceny… Je na tom mraky práce."

**Klíčový posun:** to, co jsme postavili, není „modul poptávek". Je to **první instance stavového automatu dokladu**. RFQ byla referenční vertikála, která ověřila přesně ty primitivy, co potřebuje **každý** doklad (viz §5).

## 2. Klíčová myšlenka — každý doklad je stavový automat + reakce

Každý doklad (poptávka, nabídka, objednávka, kalkulace…) se dá popsat jako:

- **STAVY** — kde v životě doklad je (nový → zpracovává se → odesláno → realizováno → uzavřeno).
- **PŘECHODY** — co posune doklad z jednoho stavu do druhého (a za jakých podmínek).
- **REAKCE** — `událost (trigger) → akce`. Automat sám reaguje na to, co se stane (přišel e-mail, uplynul čas, přišla nabídka), místo aby člověk pouštěl `@@` příkazy na povel.

RFQ nám dal ty konkrétní reakce **naostro jako `@@` příkazy**. Automat je jen **zobecní a začne je spouštět sám** (trigger místo ručního povelu).

Tohle je přesně **vrstva 1–2 poschoďového stroje** (dok 210): automaty dělají mechaniku, malé role orchestrují, člověk jen kontroluje/potvrzuje/eskaluje.

## 3. Životní cyklus dokladu — stavy

Návrh generického cyklu (RFQ ho naplňuje, ostatní doklady ho budou sdílet nebo mírně variovat):

```
   [NOVÝ] ──založ──▶ [ZPRACOVÁVÁ SE] ──odešli──▶ [ODESLÁNO] ──přijmi odpověď/zpracuj──▶ [REALIZOVÁNO] ──▶ [UZAVŘENO]
      │                    │                          │
      └──────────────── [ZRUŠENO] ◀───────────────────┘   (storno / bez odezvy / zamítnuto)
```

Mapování na RFQ (co už fyzicky existuje na dokladu):
- **NOVÝ** → `EC_GenVydanouPoptavku` založí prázdný doklad (řada 940).
- **ZPRACOVÁVÁ SE** → vyplněná pole (dodavatel, termín, název, kontakt, vazba na kalkulaci).
- **ODESLÁNO** → stavové pole `O` (Odesláno) — nastaví se, když poptávka reálně odejde e-mailem (objeví se ve složce Odeslané). *(kandidát EXT `_Odeslano` — ověřit přesný field)*
- **REALIZOVÁNO** → stavové pole `R` (`TabDokladyZbozi.Realizovano`) — nastaví se, když přijde nabídka a **řádně se zpracuje**. Tím se doklad **uzavře a přestane se hlídat timeout**.
- **UZAVŘENO / ZRUŠENO** → doklad vypadl z aktivního hlídání.

**Zásada:** stavové pole je *pravda o dokladu*, ne jen UI. Hlídač otevřených (§4, timeout) čte právě `Odesláno && !Realizováno`.

## 4. Události → reakce (jádro automatu)

Tabulka `trigger → akce` — tohle je to, co automat dělá sám. RFQ dodal konkrétní implementace; automat je zauzlí na události.

| # | Událost (trigger) | Reakce (akce) | Stav RFQ dnes |
|---|---|---|---|
| A | Vznikne potřeba poptat (nenaceněné díly kalkulace) | Založ doklad, vyplň dodavatele/díly/termín, **založ vazbu na kalkulaci**, připrav e-mail koncept | `@@RFQDOKLAD GEN/FILL` + `@@RFQDRAFT` (ruční) |
| B | Člověk potvrdí a odešle | Odešli e-mail jménem nákupčí, **nastav `O`=Odesláno**, do předmětu párovací znak (č. dokladu + č. kalkulace) | `@@RFQSEND` (předmět má EVP; **doplnit č. kalkulace**) |
| C | Přijde e-mail do schránky | **Napáruj** podle párovacího znaku v předmětu na správný doklad | ruční `@@RFQINBOX` + `@@RFQREACT` (auto-párování TODO) |
| D | Napárovaná zpráva = nabídka | Rozpoznej cenu/platnost/lhůtu, **zapiš nabídku na doklad (EXT)**, ulož `.eml` do adresáře, **nastav `R`=Realizováno** → uzavři | `@@RFQREACT` + `@@RFQFINISH` + `@@RFQMSG` |
| E | Nabídka zpracována | **Propiš vysoutěženou cenu rovnou DO KALKULACE** (`KalkulacePolozky`) + živý 4. cenový zdroj (`vypopt_nabidka`) | TODO (dnes ruční přepis — **hlavní úspora**) |
| F | Uplynula lhůta a `Odesláno && !Realizováno` | **Urguj** dodavatele / upozorni řešitele (monitor timeoutu otevřených) | TODO (monitor) |

Body C–F jsou **reakce, které dnes spouští člověk `@@` příkazem**. Cíl automatu: spouštět je sám na trigger.

## 5. Sdílené primitivy, které RFQ ověřil naostro

Tohle je „kufr", co každý doklad potřebuje — a co už máme funkční z RFQ. Až se to zopakuje na druhé vertikále, vytáhne se to do znovupoužitelné vrstvy:

1. **Založení přes VLASTNÍ Helios proceduru** (ne ruční INSERT) — `EC_Gen*`. Správné číslování + EXT + `CisloZam` dle `SUSER_NAME()`.
2. **Stavová pole** — `O`/`R` (Odesláno/Realizováno) jako pravda o životě dokladu.
3. **Vazby dokladů** — `EC_DokladyVazby` (poptávka ↔ kalkulace ↔ nabídka).
4. **Kontaktní osoby** — přehled 107 (`TabCisKOs` + vztahy + `TabKontakty`), `find_org_contacts`.
5. **E-mail (EWS)** — koncept / odeslání / čtení inboxu / react / celý `.eml`, jménem správné schránky.
6. **Adresář dokumentů** — `D:\Data\<typ>_<x>\<doklad>` (lokální kořen na EC-SERVER2).
7. **Cenové zdroje** — ceníky (`find_price`/RegCisHeo), poslední nákupka (příjemka řada 110), nabídky (`vypopt_nabidka` = 4. zdroj).
8. **MCP write gotcha** — write režim zahazuje result-sety → OUTPUT přes nonce-marker (`st.*`), čti druhým SELECT voláním. Computed sloupce (`_TEXT`, `TerminDodavkyDat`) → piš do zdroje.

## 6. Datový model — co automat potřebuje (návrh)

- **Stavová pole:** `Odesláno` (kandidát EXT `_Odeslano`) + `Realizovano` (header). **Před zápisem ověřit přesné fieldy** na typu dokladu.
- **Vazby:** `EC_DokladyVazby` (`ID_Kam`/`ID_Odkud`) — poptávka↔kalkulace (`SeznamKalkulací`, grid přes `EC_KalkulaceHlav.CisloKalkulace`), nabídka↔poptávka atd.
- **Párovací znak:** číslo dokladu (EVP…) **+ číslo kalkulace (EK…)** v předmětu e-mailu → auto-párování příchozí pošty na doklad (událost C).
- **Marker/OUTPUT:** nonce-keyed `st.*` pro čtení OUTPUT hodnot přes MCP write path.
- **Hlídací dotaz (timeout):** doklady `Odesláno && !Realizováno && (dnes - datum_odeslání) > lhůta`.

Pozor na návaznost s dok 222: přední půlka funnelu (`tenant.vp_poptavka`, `nabidka`, `objednavka`) je **postavená, ale prázdná** — most e-mail→strukturní záznam chybí. Automat dokladu je právě ten most.

## 7. Doktrína — jak to stavět (NE univerzální engine dopředu)

Martiho vlastní pravidlo („nejdřív funkční engine, pak pattern na ostatní", #11 additivně ne perfektně):

1. **Dotáhnout JEDNU kompletní vertikálu naostro** (RFQ ✅ hotová a ověřená).
2. **Sdílené kusy vytahovat do znovupoužitelné vrstvy, AŽ SE ZOPAKUJÍ** — ne dřív.
3. **Generalizovat na další doklady, až dvě vertikály sdílí kód.**

Předčasný „univerzální workflow engine" by nás jen zasekl v refaktoru. Proto: druhá vertikála **přijatá poptávka** poběží taky naostro, a teprve srovnání RFQ × přijatá poptávka ukáže, co je opravdu sdílené.

## 8. Další vertikála — přijatá poptávka (Anfrage) → kalkulace → nabídka (Angebot)

Tohle je **zákaznická strana** (protisměr RFQ). Marti: „přijde poptávka → založit → začít zpracovávat → založit kalkulaci → připravit nabídku → sklad → ceny". Mapuje se přesně na dok 222 §7 (triáž-konzument → kalkulant → nabídkář):

```
Anfrage (zákazník, projects@) ──▶ [přijatá poptávka: vp_poptavka]
        │  (AI triáž: shrnutí, zákazník, jistota, přidělení)
        ▼
   [KALKULACE: ec_kalkulace_hlav / EC_KalkulacePolozky]  ◀── ceny: find_price + poslední nákupka + vypopt_nabidka
        │  (nenaceněné díly → RFQ vertikála §1 = tahle smyčka spotřebovává vydané poptávky!)
        ▼
   [NABÍDKA / Angebot: nabidka]  (draft, NEodesílá — zásada e-mailu)
```

**Skládá se to hezky:** zákaznická poptávka **spotřebovává** naši RFQ smyčku — ceny dílů pro kalkulaci si tahá i přes vydané poptávky u dodavatelů (událost A výše). Takže RFQ není slepá ulička, je to podčást zákaznické vertikály.

**Zítra začínáme tady:** přijatá poptávka + založení kalkulace. To otevře reálný příklad, na kterém se ukážou další věci k dostavění (stejně jako RFQ ukázalo body v §9).

## 9. Otevřené body z RFQ = konkrétní reakce automatu

Pět bodů, které Marti pojmenoval pro ostrý provoz (RFQ doc §11) — a jak sedí do automatu:

1. **Vazba poptávka ↔ kalkulace** (`SeznamKalkulací`, `EC_DokladyVazby`, EK…) → událost **A** (zakládat s dokladem).
2. **Párovací znak v předmětu** (č. dokladu + č. kalkulace) → událost **B** (doplnit č. kalkulace do `@@RFQSEND`).
3. **Hlídání otevřených poptávek (timeout)** → událost **F** (monitor `Odesláno && !Realizováno`).
4. **Stavy `O`/`R`** → §3 (Odesláno při odeslání, Realizováno při zpracování nabídky → uzavře + vypne timeout).
5. **Propis ceny do kalkulace** → událost **E** (dnes ruční přepis = hlavní úspora).

## 10. Otevřené otázky k rozhodnutí (zítra / průběžně)

- Přesné stavové fieldy `Odesláno`/`Realizováno` na jednotlivých typech dokladů (ověřit `sys.columns` per typ).
- Kde žije „automat" fyzicky — reakce jako data (tabulka přechodů/reakcí) vs. kód per vertikála? *(nejspíš nejdřív kód, tabulka až po druhé vertikále — §7).*
- Auto-párování příchozí pošty (událost C): párovací znak v předmětu vs. thread_id/message_id (dok 222 `vp_poptavka` má oba sloupce).
- Lhůty timeoutů — per dodavatel / per typ / globální default?
- Napojení `vypopt_nabidka` do `compute()` (událost E) — po konzultaci s Eliškou (její workflow).

---

## Odkazy

- Referenční vertikála: [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md) (`@@RFQ*`, moduly `rfq_draft.py` + `rfq_doklad.py`).
- Ceny do kalkulace: [Kalkulace / ceníky Vize 1](Z_kalkulace_ceniky_vize1.md) (`find_price`, RegCisHeo, poslední nákupka z příjemky).
- Životní cyklus zakázky / funnel: [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md) (přední půlka `vp_poptavka` prázdná = most chybí).
- Architektura: [210 — Poschoďový stroj](210-poschodovy-stroj.md) (automaty → role → orchestrace → člověk).

*Kostra zapsána, aby se neztratil kontext. Doplní se po vertikále „přijatá poptávka". Zapečetit do znalostního modulu až po review (návrh, ne hotové). — Claude C23, 18. 7. 2026.*
