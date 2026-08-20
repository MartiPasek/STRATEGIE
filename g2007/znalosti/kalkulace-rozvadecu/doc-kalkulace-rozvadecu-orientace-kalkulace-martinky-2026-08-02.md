# Orientace pred stavbou prvni "Martinky" pro kalkulace ABSAUGWERK (FLEX+ / SMART NASS) - stav 2.8.2026

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Kontext:** Marti 2.8.2026: prvni pilir, ktery musime rozlousknout je kalkulace zakazek - konkretne Eliscin zakaznik ABSAUGWERK, ktery ma DVE rady - Smart a Flex. "Neni kalkulace jako kalkulace" - jini zakaznici budou potrebovat Martinky s jinym promptem. Pozadavek: zorientovat se, nez budeme pokracovat. Tento dokument je ta orientace, overena primo v kodu/DB/gitu 2.8.2026 (ne z pameti).

## 1. Tohle NENI nove uzemi - existuje bohata analyza + castecne postaveny engine (18.-22.7.2026)

`g2007.znalost#37` ("SRDCE FIRMY", 1.7.2026) je zakladni analyza Eliscina procesu, grounded na 3 realnych podkladech (kalkulace EK262940 Absaugwerk .xlsm + nabidka EN262940 + EPLAN spec Flex+ 15kW). `g2007.znalost#107` (18.7.) je smerove rozhodnuti "Vize 1" (nas engine = zdroj pravdy MISTO Excelu). `g2007.znalost#147` (22.7.) je datova mapa Centrala<->STRATEGIE.

**Git historie `modules/erp/api/kalkulace_engine.py`: 10 commitu, 18.7. 15:34 az 22.7. 21:18, pak ZADNY dalsi dotek 10 dni** (do dnes 2.8.) - presne odpovida Martiho popisu, ze migrace "kod jako data" (31.7.-2.8.) tohle prerusila.

## 2. Co uz konkretne existuje a funguje (overeno v kodu)

- **Dva produkcni profily** v `PROFILY` dict: `flex` (ABSAUGWERK FLEX+ Schaltschrank, VKM baze 14.5, Arbeit baze 28, marze 12%, fix prirazky projekt+revize+transport=330) a `nass` (ABSAUGWERK SMART NASS Steuerovani, VKM baze 11.0, Arbeit baze 28, marze 8%, ZADNE fixni prirazky, ALE tabulka floor cen per kW vykon: 1.1kW->1170, ..., 22kW->1800). Tyhle dve rady MAJI ruzne sazby/marze/logiku - presne to, co Marti myslel "neni kalkulace jako kalkulace".
- **RegCisHeo prevodnik** (`@@KALKREGCIS`): z (vyrobce + syrove obj. cislo) sklada nase "objednaci cislo" = "<PREFIX> <cislo>" (napr. "SIE 5SY4110-6"). Tohle je klicovy parovaci klic pres cely tok (BOM <-> historie kalkulaci <-> Velke ceniky <-> sklad).
- **Cenova vrstva `price_bom()`/`@@KALKPRICE`**: pro kazdy dil v BOMu vezme (a) posledni skutecne zaplacenou nakupku z prijemky (DB_EC `TabPohybyZbozi`, rada dokladu 110), (b) aktualni cenu z Velkeho ceniku dodavatele (`proj.cenik_polozka`, 539 tis. polozek / 11 dodavatelu, posledni import 2.7.). Cena = max(oba), s pojistkami: prijemka starsi 12 mesicu -> neduveruj, opri se o cenik; rozdil >60% -> nejspis zmatek v baleni (ks vs balik), flag k rucni kontrole; rozdil cenik>prijemka -> "zdrazeno" flag.
- **Koeficienty z realneho zdroje** (`_coef_ec`): K_VKM/K_ARB per dil primo z `EC_KalkKoeficienty` (DB_EC), ne dopocitane. TOHLE JE DUSEVNI VLASTNICTVI FIRMY (dle #37: "kolik prace a spojovaku dany dil sezere" - nekoupi se, nasbira se).
- **`compute_absv1()`/`@@KALKABSV1`**: spoji vsechno vyse (material z price_bom + koeficienty z EC + profil marze/floor/fix) do GESAMT ceny + zaokrouhleni na "nabidnout" (na desitky). To je aktualne nejpokrocilejsi/nejpresnejsi verze enginu.
- **POC dukaz na realnem kusovniku** (SKF Supply list 20414, #37): 64 radku s obj. cislem -> 83% automaticky naparovano na katalog, 77% rovnou s cenou EUR, beh ~3s. Nenaparovane spravne vyfiltrovalo specialy (KUKA robot, PhotoNeo 3D vision) k rucni kontrole - presne Eliscin pozadavek "odchytit + upozornit".

## 3. Co CHYBI, aby se tomu dalo rikat "Martinka" (kriticky bod)

**Zadny konverzacni nastroj neexistuje.** Cely `kalkulace_engine.py` je dnes dostupny JEN pres `@@KALK*` prikazy v SQL-bridge (urceno pro Claude/cloveka pres most, ne pro AI personu v beznem chatu). Overeno: `grep -rl "kalkulace_engine" modules/conversation/` = 0 vysledku. Zadny `tool_registry` handler nezabaluje `compute_absv1`/`price_bom` jako nastroj volatelny Martinkou.

Domeny `kalkulace_obecna` (`domain_user`) a `kalkulace_specificka` (`domain_lead`) v `g2007.tool_domain` UZ EXISTUJI (katalog z #280), ale maji prirazene jen obecne nastroje (`python_exec`, `strategie_pg_query_raw/table`) - zadny specificky "spocitej kalkulaci" nastroj. Tohle presne odpovida rozliseni, ktere Marti popsal: `kalkulace_obecna` pro obecne principy, `kalkulace_specificka` pro zakaznicky prompt (Absaugwerk atd.) - infrastruktura pro "ruzne Martinky s ruznym promptem" uz cekaji, jen prazdne.

**-> Konkretni dalsi krok by byl: postavit tool_registry nastroj (napr. `kalkuluj_absaugwerk(profil, bom)`), ktery zabali `compute_absv1`, a pripojit ho do `kalkulace_specificka` domeny.**

## 4. Otevrene otazky pro Elisku/Kristy, ktere podle #37 (1.7.) jeste NEBYLY zodpovezeny

1. EPLAN export kusovniku - strukturovane (xls/xml/API) nebo jen PDF? Rozhoduje o cistote importu.
2. Mapovani `reg_cis` <-> `id_kmen_zbozi` (most BOM->sklad) - existuje hotove v Heliosu?
3. Zdroj dodacich lhut - dodavatelske katalogy vs historie nakupnich objednavek?
4. Kolik vzorovych kalkulaci (typovych rozvadecu) existuje jako knihovna sablon?

## 5. Drobny technicky nalez z dnesniho overeni (2.8., nutno vyjasnit pred pripadnou revalidaci presnosti)

Primy dotaz na `EC_KalkulaceHlav` pro `EK262940`/`EK263380` (MSSQL, funkcni pripojeni overeno) vratil `CelkemCena` PRAZDNE a `MarzeProcent`=0.00 pro oba, i kdyz `VKM`/`Arbeit` sazby sedi presne s hodnotami v `PROFILY` (14.5/28 a 11.0/28). Skutecna fakturovana/nabidnuta cena (2 900,- zminovana v #37 pro jeden konkretni pripad) tedy pravdepodobne nezije v tomhle hlavickovem radku, ale jinde (konkretni Angebot dokument nebo jiny zdroj) - nutno vyjasnit s Eliskou/Kristy pred jakymkoliv presnostnim porovnanim enginu proti "skutecne" cene.

## Zaver

Zadny kod se dnes nemenil - tohle je cisty pruzkum pred rozhodnutim, presne dle zadani. Engine na kalkulaci FLEX+/NASS je z velke casti postaveny a jednou POC overeny na realnych datech (SKF), ale (a) 10 dni nedotcen, (b) nikdy nezabaleny do nastroje pro Martinku, (c) presnost proti SKUTECNE fakturovane cene neni cerstve overena (zdroj pravdy pro "skutecnou cenu" nejasny).

_Zapsano Claude-23, 2.8.2026. Navazuje na #37, #107, #147, #280, #281._

