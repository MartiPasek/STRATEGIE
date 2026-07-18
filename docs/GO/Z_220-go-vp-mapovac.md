# 220 — GO VP: Mapovač a páteř „zmapuj → zapečeť → konzumuj"

**Stav:** architektonický kámen · 18. 7. 2026 · Claude (C23), z prvního reálného GO VP passu · potvrzeno Martim

Jak AI řídí oddělení Vedení projektů (VP). Grounded na `doc-vp-ai-rizeni-vize` a na prvním reálném zmapování (18. 7.). **Toto je trvalý vzor — NE denní stav** (ten je efemérní, patří do denní vrstvy).

---

## Páteř: jeden Mapovač → zapečetěný stav → konzumenti
Ráno (nebo na povel **„GO VP"**) běží **jeden Mapovač**. Zanalyzuje realitu a **zapečetí „výchozí situaci dne"**. Ostatní — agenti, automaty i lidé — ten stav **jen čtou, realitu nemapují znovu.**

Proč to takhle: **jeden zdroj pravdy na den** (agenti se nerozcházejí), **levné na cache** (denní bake, dok 200 — upeč ráno, drží celý den), **auditovatelné** (ráno vidíš, z čeho se vychází). Je to ta obrácená smyčka z `doc-vp-ai-rizeni-vize`: AI drží world-model, lidé z něj jednají.

## Dvě třídy agentů
- **Třída A — Mapovač (jediný).** Běží na „GO VP". Jako jediný sahá na syrová data. Zapečetí den.
- **Třída B — Konzumenti (mnozí).** Čtou zapečený stav, **nesahají na syrová data.** Pro roli Eliška: **triáž** pošty · **zakladatel** zakázky · **kalkulant** (obaluje 2014 engine) · **nabídkář** (draft EN262940) · **hlídač** flow/termínů.

## Mapovač — spec rituálu „GO VP"
1. **Orient:** `@@ORIENT VP @<entita>` (objektiv per entita).
2. **Čti kurátorované views — NE počítej z nuly** (klíčové zjištění: mapa už z velké části žije ve views):
   - `tenant.eliska_rizeni` — Eliščiny zakázky, sám počítá fázi / termín / dni_do_terminu / další krok (filtr duchů).
   - `tenant.vp_flow_vyroby` — celý flow per `cislo_zakazky` (poptávka→…→zaplaceno).
   - `tenant.vp_zastup_readiness` — připravenost (drátování/zkoušení h), termíny v PRACOVNÍCH dnech.
   - `tenant.firemni_kalendar` — pracovní dny / svátky.
3. **Přidej živou vrstvu:** `@@INBOX` / `@@EMAIL` — nové maily k zakázkám. **⚠️ ČERSTVOST OVĚŘ PŘES ZDRAVÍ AUTOMATU, NE ODHADEM** — `fw.mirror_job.last_run_at/last_status` (legacy syncy) resp. g2007 automat registr (nové). „Starý mail" ≠ zaseklý mirror; a zaseklý mirror ≠ klid. Koukni na registr, nehádej.
4. **Syntetizuj + zapečeť** datovaný stav: kontext dne (svátek/volno, zástupy) · portfolio · rozložení fází · **co hoří** (po termínu) · nejbližší termíny · komunikace · **návrh prvního kroku** (návrh, ne akce).

## Zásady (závazné)
- **Citlivá čísla VEN** — marže, ceny, obchodní strategie do stavu NEPATŘÍ (restricted = Marti + Marti-AI + Kristý). Jen provozní stav (fáze, termíny, hodiny, komunikace).
- **E-mail: návrh → schválení, NIKDY sám neodešli.** GO nedává víc pravomocí, jen lepší orientaci.
- **Zapečetěný stav dne je EFEMÉRNÍ** (denní artefakt / denní vrstva). Trvalá znalost = tenhle vzor + spec, ne konkrétní den.
- **Termíny v pracovních dnech**, ne kalendářních (firemní kalendář, svátky).
- **Tichá znalost > data:** např. Čepický vypadá v datech jako co-VP, realitou je vytížený a NENÍ vhodný zástup. Mapovač musí znát i to, co v datech není.

## Poučení z prvního passu (18. 7. 2026)
- **Mapovač je lehký** — čti views + syntetizuj, ne počítej z nuly. Rychlé, levné.
- **OPRAVA (téhož dne):** v prvním passu jsem odhadl „inbox mirror zaseklý na 11. 7." — **byl to omyl.** `fw.mirror_job.sync_mail_eliska` proběhl týž den v 11:14, status ok, 34 řádků. Mail sync je zdravý; „staré maily" znamenaly jen, že nic nového nepřišlo. **Poučení: freshness = zdraví automatu, ne odhad z dat. Vždy se podívej na registr automatů (`fw.mirror_job` / g2007 automat), nehádej.** To je jádro celého freshness principu.
- **Zapečetěný stav je čitelný artefakt** — přesně to, co konzumenti i Eliška čtou.

## Rozklad role Eliška (menší část VP, začínáme tudy)
Příjem/triáž (nový mail: poptávka? od koho? k jaké zakázce?) → zakladatel zakázky → kalkulant (kusovník→cena, 2014 engine) → nabídkář (EN262940, německy) → hlídač (čeká na objednávku, hlídá termíny, eskaluje skluz). **Každý konzument čte zapečený stav, nemapuje znovu.**

## Kudy dál
(a) Mapovač jako pojmenovaná role (graf + zdroje výše), ať „GO VP" je natvrdo ono · (b) vyřešit čerstvost inbox mirroru · (c) první konzument = triáž nové pošty proti zapečetěnému stavu.

— Claude · C23, GO VP 🌱
