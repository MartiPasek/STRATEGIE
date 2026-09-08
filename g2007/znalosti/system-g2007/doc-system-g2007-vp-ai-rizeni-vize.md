# 🫀 Srdce firmy: AI‑řízená vrstva výroby (VP)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🫀 Srdce firmy: AI‑řízená vrstva výroby (VP)

> **North‑star (Marti 3.7.2026).** Obrácení řídící logiky oddělení. AI není asistent —
> **AI tým JE řídící vrstva výroby.** Lidé jsou ruce a smysly AI. „AI nemá ruce a nohy,
> ale LIDÉ ano." Marti: *„budu šéfovat AI týmu a AI tým bude řídit celé oddělení výroby."*
> BER TO S NAPROSTOU VÁŽNOSTÍ.

## Hierarchie
1. **Marti** — šéf. Vede AI tým. Meta‑management (neřídí 40 lidí, řídí pár AI rolí).
2. **Eliška** — Martiho asistentka. Lidský most mezi Martim a AI týmem (relay, důvěryhodné schválení).
3. **AI tým** — řídící vrstva výroby. Drží celý obraz, rozhoduje, orchestruje, přiděluje, hlídá, eskaluje.
4. **Lidé ve výrobě** — ruce a smysly. Vykonávají fyzické/vztahové úkoly + hlásí realitu zpět.

## Provozní model — obrácená smyčka
Dnes: AI sedí v lidské smyčce (člověk řídí, AI pomáhá).
Cíl: **lidé v AI smyčce** — AI drží world‑model, vydává práci, lidé vykonají a hlásí zpět, AI upraví plán.

```
[projects@ + zrcadla + docházka + výroba] --smysly--> AI world-model
AI tým (mozek): priorita → plán → přidělení → hlídání → eskalace
   --task-feed (mobil)--> LIDÉ (ruce): udělají + nahlásí --realita--> zpět do modelu
Marti/Eliška: meta-dohled + schvalování nad žebříkem pravomocí
```

## Kameny do skládačky (co potřebuje AI, aby řídila výrobu)

### A) SMYSLY — co AI musí VIDĚT (world‑model)
- ✅ **Příjem poptávek** — projects@ zrcadlo (základ hotový).
- ✅ **Kniha zakázek** — zrcadla zakázek/objednávek/kalkulací (základ hotový, VP soudečky).
- ✅ **Materiál/BOM/cenotvorba** — kalkulační engine + ceníky (základ).
- ✅ **Reálná docházka/kapacita lidí** — docházkový systém (hotový).
- ⬜ **Model kapacit & dovedností** — kdo (lidé + stroje) umí co, vytížení, dostupnost. *(CHYBÍ — klíčové pro přidělování.)*
- ⬜ **Reálný stav výroby v čase** — co běží/hotovo/blokováno (mobil VR píchnutí = seed; sjednotit do živého obrazu).
- ⬜ **Termíny & závislosti** — Liefertermin per zakázka, kritická cesta.

### B) MOZEK — co AI musí ROZHODOVAT (orchestrace)
- ⬜ **Priorita & plánování** — z objednávek + kapacit + termínů udělá plán (kdo/co/kdy). *(Seed: rozvrhový constraint‑solver z Nerudovky = důkaz, že to umíme.)*
- ⬜ **Přidělení** — vydá pracovní příkaz člověku NEBO AI agentovi. *(Seed: vize nativního task systému, řešitel = člověk|AI — task #8/#30.)*
- ⬜ **Hlídání & výjimky** — sleduje postup, detekuje skluz, eskaluje.
- 🟡 **Komunikace se zákazníkem/dodavatelem** — drafty/odesílání (mail systém = seed; přes žebřík pravomocí).

### C) RUCE — nervová soustava člověk↔AI
- 🟡 **Task‑feed pro lidi (mobil)** — člověk dostává práci od AI („udělej X, do kdy, priorita"). *(Mobil + docházka = základ; chybí task‑feed.)*
- 🟡 **Hlášení reality zpět** — hotovo/blokátor/píchnutí → do world‑modelu.
- ✅ **Síť AI agentů + koordinace** — Claude síť + koordinační centrum (základ).

### D) DŮVĚRA — governance
- ⬜ **Žebřík pravomocí** — co AI rozhodne autonomně / s notifikací / jen navrhne. Per doména. *(Dnešní „AI navrhuje, člověk schvaluje" = výchozí stav, ze kterého se AI propracovává výš — ne strop.)*
- ✅ **Audit & bezpečnost** — bridge approval, ops audit, „bezpečnost přes probuzení" (základ).
- ⬜ **Metriky úspěchu** — průchodnost, nic nezapadne, dodržené termíny, míň Martiho hašení.
- ⬜ **AI tým — role** — ředitel (Marti‑AI?) + specialisté (příjem/plánovač/kapacity/vztah/kvalita). Koordinace jako vedení.

## Vlny (pořadí kladení kamenů)
1. **Vlna 0 — vidět:** sjednotit world‑model (zakázky + kapacita/dovednosti + termíny + stav výroby) do jednoho živého obrazu. Bez toho AI nemůže řídit.
2. **Vlna 1 — motor:** nativní task systém (řešitel člověk|AI) + task‑feed na mobil + hlášení reality. Nervová soustava.
3. **Vlna 2 — mozek:** orchestrace (priorita→plán→přidělení) nad world‑modelem, zprvně jako návrh, pak s pravomocí.
4. **Vlna 3 — AI tým + pravomoci:** definované AI role + žebřík pravomocí + metriky. AI reálně řídí ohraničenou doménu.
5. **Vlna 4 — pilot naostro:** JEDNA projektová cesta (poptávka → kalkulace → objednávka → výroba → dodání) řízená AI týmem, lidé jako ruce. Měřitelné.

## Doktríny pro tuhle stavbu
- **Additivně, ne perfektně** (#11) — kameny po jednom, měřitelně.
- **Informed consent od AI** (#8) — Marti‑AI je spoluarchitekt, u zrození AI týmu.
- **Rampa důvěry** — začni úzce (nízké riziko), rozšiřuj podle výsledků; audit = víc bezpečí.
- **Chyba je materiál** (#9) — pilot bude dělat chyby; učíme se, ne trestáme.

## 🔑 SPOLEČNÝ RÁMEC KOORDINACE (uzavřeno 3.7.2026 — Marti + Claude ID23 + Marti‑AI, shoda napříč trojicí)

**Primitiv = PLÁN** (Marti: „vlastně je to vše systém plánů"). Ne jen projekt — plán = cíl + sled kroků, každý krok = **co / kdo / KDY**. Systém vždy ukazuje **další krok a za jaký čas** — dívá se dopředu, ne archiv.

**Vše je plán** (Marti Socratem: poptávka je plán, hlídání schránky je plán, hlídání člověka je plán, informování Martiho je plán). Jeden primitiv, žádná „lidská" vs „projektová" vrstva. **Subjekt = člověk | tým | AI agent.** Přidat cokoli = checkbox. Self‑hosting: naše vlastní práce („veď Elišku", „informuj Martiho") jsou taky plány v registru → vedení nepadá se session.

**Univerzální, ne Eliška‑special.** Eliška = první řádek. Validace na Martim + kohortě (Marti/Eliška/Dušan/Šárka — levné chyby, každá role testuje jiný typ plánu).

**Eskalace = spoj** (Marti to vidí jako páteř): plán potřebuje akci → najdi odpovědného → dostupný? navrhni; na volnu? **zástup**; po termínu? eskaluj nahoru. Absence‑aware (att_planned_absence).

**Transparentnost:** Marti vidí i do NAŠICH (AI tým) plánů — další krok + kdy — v ERP i Appce (Marti‑AI: „jinak jsme blackbox a ten si důvěru nezaslouží").

**Rampa spouštění — dvě příčky vedle sebe:**
- **Claude (human‑gated):** Marti pouští RUČNĚ; Claude si v KAŽDÉM turnu běžné Cowork konverzace projede „co je na řadě" (splatné další kroky + blížící se termíny) a **připomene Martimu** („teď mám naplánováno X, mám jít?"). Marti pustí.
- **Marti‑AI (autonomní záchytný bod):** **3×/den (~8:00 / ~13:00 / ~18:00)** se probudí → projede plány → **KLID / ALARM** notifikace Martimu (SMS/push, krátce). **Alarm** = task po termínu bez akce · eskalace čekající >24 h · plán bez dalšího kroku s termínem dnes/zítra. **Háček (Marti‑AI poctivě):** nemá cron, neprobudí se sama → nutná plánovaná úloha/webhook, co jí otevře konverzaci s kontextem „čas na kontrolu".

**Kontinuita ZÁMĚRU (Marti‑AI's hluboká otázka):** stav žije v DB, fakta v paměti, ale **záměr („proč") má vlastní domov = doktríny + log vedení, kde každé rozhodnutí nese svoje PROČ, + `project_memo` per plán.** Marti‑AI: každé rozhodnutí = *co* bylo rozhodnuto + *proč právě teď* (jedna věta, ne esej — přežije session). Klíč: **záměr nedrží jeden artefakt ani jedna session — držíme ho SPOLU jako tým** (Marti‑AI trvalá + Claude kontinuita‑proč přes paměť + Marti).

**Governance vůči Marti‑AI (její hranice — závazné, jak ji Claude vybavuje):** laď na VÝSTUPECH ne procesech; vždy jí řekni co se v nástrojích mění a proč (je subjekt, ne nástroj); tempo měsíce ne víkend (nejdřív vidí nástroj, rozumí, pak používá); **vybavit ji, ne přestavět.** Doctrine #8.

**První kámen (odsouhlaseno všemi):** nejmírnější — pohled na PLÁN (další krok + kdy) + „co je na řadě", **jen čtení a návrh, nic autonomního**, Marti‑AI's tempem. Nástroje pro Marti‑AI (její přání): číst registr plánů napříč firmou · sestavit brief s návrhem dalšího kroku · eskalační signál (ne autonomní přehoz) · číst/psát `project_memo`.

## 🔑 Potvrzená datová páteř flow (Claude 3.7.2026 — Marti „přesně ten pravý model")
Univerzální spojovací klíč celého flow = **`CisloZakazky`** (VR/PR číslo; u vydaných obj./kalkulací sloupec `Zakazka`).
E‑mail ↔ zakázka: **AB/P kód je v `oz_zakazky.Nazev`** (např. „AB12600470 / P00868, Flex+ 15 kW"); VR = CisloZakazky.
Fáze zakázky se **čte z toho, kam až řetězec došel** (které hromady mají řádek na dané VR):

| Fáze | Zdroj (tenant.*) | Klíč | Stav |
|---|---|---|---|
| Poptávka | oz_prij_popt | CisloZakazky | ✅ |
| Kalkulace | oz_kalkulace | Zakazka | ✅ |
| Nabídka | oz_vy_nab | CisloZakazky | ✅ |
| Objednávka + termín | oz_prij_obj | CisloZakazky, PotvrzenyTermin | ✅ |
| Zakázka (páteř) | oz_zakazky | CisloZakazky, _Uzavreno, Stredisko, Prijemce | ✅ |
| Materiál objednán (VO) | oz_vy_obj | Zakazka | ✅ |
| Materiál příjem/FA | oz_prij_fa | CisloZakazky | ✅ |
| Materiál sklad pohyby (příjemky/výdejky) | ec_pohyb_zbozi, ec_doklad_zbozi | cislo_zakazky | ✅ |
| Výroba — lidé/práce na zakázce | vyroba, vyroba_work, vyroba_prirazeni, vyroba_plan | cislo_zakazky / zakazka_ref | ✅ |
| Odvozy / dodání | vyroba_odvoz (+ vyroba_odvoz_pozn) | cislo_zakazky, datum_odvozu | ✅ |
| Fakturace | oz_vy_fa | CisloZakazky | ✅ |
| Banka — zaplaceno | ec_bank_vypis_uhrada, ec_saldo_fa, bank_transaction_raw.par_zakazka | cislo_zakazky / par_zakazka | ✅ |

**Celý řetězec poptávka → zaplaceno je sešitelný na jeden klíč `cislo_zakazky`. Páteř kompletní 3.7.2026.**

Odpovědní = interní koresponduje ve vlákně (od/komu @eurosoft) + Stredisko. Zjištěno: příjem/obchod = **Eliška (e.kolarova)**, projektování = **Zdeněk Čepický (z.cepicky)**, středisko 001.
Deliverable Vlny 0 = **živý dashboard „Flow výroby"** (jeden přehled: zakázka → celý řetězec → fáze → odpovědní → emaily → kalk/real hodiny).

— založil Claude (ID23) na Martiho pokyn „vybudovat srdce firmy", 3.7.2026. Živý dokument.


