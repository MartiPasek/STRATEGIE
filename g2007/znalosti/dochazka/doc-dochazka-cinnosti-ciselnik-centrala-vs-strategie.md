# Číselník činností: Centrála × STRATEGIE — číslo činnosti není ID, čísla musí sedět, Režie je zakázka

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ⛔ ID A ČÍSLO ČINNOSTI JSOU DVĚ ROZDÍLNÉ VĚCI (Peťa 4. 9. 2026, ZÁVAZNÉ)
>
> Peťa doslova: *„ID a číslo činnosti jsou dvě naprosto rozdílné věci. ID nás nezajímá —
> to vás zajímá někde na pozadí, ale pořád jsou to dvě rozdílné věci."*
>
> **Číslo činnosti** je to, co Peťa vidí na obrazovce a čím se s ní mluví. **ID** je technika
> na pozadí. Nikdy se jedno nevydává za druhé — ani v hlídači, ani v dotazu, ani v řeči.
> Kdo je zamění, hlídá něco úplně jiného, než měl: služební cesta je **činnost 9**, ale
> pod **id 9** sedí u nás Značení vodičů a v Centrále Nemoc.
>
> Kde se který sloupec bere a do kterých tabulek se dívat nemá → sekce **„Kam se nedívat"** níž.

**Autoritativní je číselník Centrály.** `tenant.vyroba_cinnost.ec_cislo` MUSÍ odpovídat
číslu činnosti v Centrále (EC). Peťa v aplikaci i v Centrále pracuje s **číslem
činnosti (ec_cislo)**, ne s interním `id` — vždy s ní mluv čísly, která vidí ona.

## Stav k 3. 8. 2026 (srovnáno)

Peťa dodala export činností z Centrály (76 položek). Ve STRATEGII jich bylo 47,
takže **30 chybělo**. Doplněny všechny, včetně těch, kvůli kterým to praskalo:

* **30 Dovolená navíc** — samostatný druh nepřítomnosti, NENÍ to totéž co 20 Dovolená
* **37 Nepřítomnost OSVČ** — také samostatný druh, NENÍ to totéž co 30

Dál chyběly: 10 Nařízené volno · 12 Nahrazení volna · 14 Čas na cestě · 22 Nemoc ·
23 OČR · 24 Prac. úraz · 25 Paragraf · 28 Čas. konto-výběr · 29 Osobní hodnocení ·
32 Interní doplnění · 33 Otcovská · 34 Ostatní s náhradou mzdy · 35/47/50/51 Volno
60–90 % · 36 Mateřská · 52 Oprava barvy z lakovny · 53 Garant · 54 Nepřítomen pro APS ·
119 Oběd · 120 Kouření · 123 Svačina · 132 Soukromé záležitosti · 133 Náhradní volno ·
136 Výpomoc · 138 Překážka v práci · 999 Domů.

**Po doplnění: nechybí ani jedno číslo a u všech stávajících čísla sedí.**

## Co si pamatovat, ať se to neřeší potřetí

* **„Režie" NIKDY NEBYLA ČINNOST.** `Rezie` (bez háčku) je **ZAKÁZKA** — tak to má
  Helios i Centrála, a proto se do `vyroba_work.zakazka_ref` píše bez diakritiky
  (Peťa + Marti 20. 7. 2026). Činnost `Režie` (id 14, bez čísla) byla omyl;
  3. 8. 2026 archivovaná (active=false) a přejmenovaná tak, aby to bylo vidět.
* **„ostatní - kanceláře"** bez čísla (id 45) byla duplicita — platí činnost
  **6 „Ostatní – kanceláře"**. Archivováno 3. 8. 2026.
* **45 „Bez rozlišení činnosti"** je NAŠE vlastní, v Centrále neexistuje. Používá
  se všude, kde člověk činnost neupřesnil. Nechat.
* **„Garant" je v Centrále dvakrát** — pod 53 i 114. Není to chyba, máme stejně.
* Deset názvů se liší jen typografií (pomlčka, velké písmeno): 6, 8, 9, 11, 31, 41,
  44, 116, 122, 135. Čísla sedí, názvy jsme NEsjednocovali.

## Jak zkontrolovat, že to pořád sedí

Porovnej `tenant.vyroba_cinnost.ec_cislo` proti číselníku Centrály (EC_DilnaCinnosti,
resp. export od Peti). Nesmí chybět žádné číslo a žádná činnost nesmí mít jiné číslo
než v Centrále. Páruj podle ČÍSLA, ne podle názvu — názvy se liší typografií.

Zapsal Claude-26 na výslovný pokyn Peti 3. 8. 2026 („tohle už jsem si říkala
alespoň 2×, určitě jsem ti říkala, ať to zapíšeš do G2007").

---

## ⛔ KAM SE NEDÍVAT — mapa číselníků, ve kterých se dá sáhnout vedle (Peťa 4. 9. 2026)

Peťa 4. 9. 2026: *„všude, kde najdeš jiný číselník, tam tu znalost zapiš, že tam se dívat
nemáte — když to bude řešit někdo jiný, může tím nasekat spoustu chyb."*
Vzniklo poté, co jsem si sám 4. 9. spletl dva číselníky dvakrát během jedné hodiny.

### 1. Číslo činnosti × interní id — past na OBOU stranách

**U nás** má `tenant.vyroba_cinnost` tři čísla vedle sebe:

| Sloupec | Co to je | Používat? |
|---|---|---|
| `ec_cislo` | **číslo z Centrály — TOHLE Peťa vidí a tímhle se mluví** | ✅ ano |
| `id` | interní klíč tabulky | ⛔ nikdy jako „číslo činnosti" |
| `strategie_cislo` | naše vnitřní číslo, na obrazovkách se neukazuje | ⛔ ne |

Docházkové obrazovky a formuláře berou **`ec_cislo`** (`modules/erp/api/dochazka_zak_tab.py`).

**Živý příklad, na kterém to prasklo:** služební cesta je **činnost 9** (`ec_cislo = 9`),
ale její `id` je **16**. Pod `id = 9` sedí **Značení vodičů** (činnost 40) — běžná dílenská
práce, 40 úseků za samotný srpen. Kdo si to splete a napíše hlídače na `id`, zaplaví frontu.

**A stejná past je i v Centrále.** `EC_DilnaCinnosti` má taky `Cislo` i `ID`:

| | `Cislo` (to platné) | `ID` (nedívat se) |
|---|---|---|
| Služeb.cesta/montáž | **9** | 21 |
| Značení vodičů | 40 | 34 |
| **Nemoc** | 22 | **9** ← past |

Kdo v Centrále sáhne na `ID = 9`, hlídá **nemoc** místo služebních cest.

### 2. Kterých 77 činností je „ten pravý" číselník

Číselník činností Centrály jsou **DVĚ tabulky dohromady** (přehledy 1046 a 1047):

- **`EC_DilnaCinnosti`** — dílenské, 45 položek
- **`EC_Dochazka_CinnostiRezie`** — režijní, 32 položek

Nejsou to škatulky, jsou to dva SEZNAMY — k libovolné zakázce se dá vybrat z obou
(viz `doc-dochazka-zakazka-a-cinnost-nemaji-vazbu`).

### 3. ⛔ Tabulky, které vypadají jako číselník činností, a NEJSOU

| Tabulka | Co v ní doopravdy je | Proč svádí |
|---|---|---|
| **`EC_Vytizeni_TypyUdalosti`** (7 řádků) | Odvoz, Předodvoz, Přejímka, KKO, Instalace, Přání zákazníka — **obchodní události u zakázek** | Jmenuje se „typy událostí" a čísluje od 3. Kdo ji použije na `EC_Dochazka_Udalosti`, dostane úplně jiné názvy. **Já jsem na tohle 4. 9. naletěl.** |
| **`EC_OrgCinnosti`** (580 řádků) | činnosti **organizační struktury** (kdo co smí, posty, zodpovědnosti) | má `Cislo` i `Nazev`, jmenuje se „činnosti" — a s docházkou nemá nic společného |
| **`TabDruhCinnosti`** (2 řádky) | heliosovský zbytek | název sedí, obsah ne |
| **`TabCiselnikCinnosti`** (0 řádků) | prázdná | název sedí dokonale, obsah žádný |
| **`EC_EventTyp`** (26 řádků) | **druhy nepřítomnosti** (nemoc, OČR, dovolená…) + jejich `DruhCinnosti` | je to správná tabulka, ale na **nepřítomnosti**, ne na pracovní činnosti. Pozor: `EC_Dochazka_Udalosti.Typ` je `EC_EventTyp.ID`, a **v téže tabulce leží i obchodní události** (typ 5 = Zakázka, 8 613 řádků). Filtruj podle druhu, ne podle data. |

### 4. A ještě jeden číselník, který s tímhle nemá nic společného

**Druh záznamu** (`att_entry.ec_druh` — 20 dovolená, 30 dovolená navíc, 22 nemoc…) je
**něco úplně jiného než činnost**. Detail v `doc-dochazka-dva-ciselniky-druh-zaznamu-vs-cinnost`.

### Jak si ověřit, že se dívám správně

```sql
-- u nás: co je činnost 9?
SELECT id, ec_cislo, name FROM tenant.vyroba_cinnost WHERE tenant_id = 2 AND ec_cislo = 9;
-- v Centrále: totéž
SELECT ID, Cislo, Nazev FROM EC_DilnaCinnosti WHERE Cislo = 9;
```

Když mluvíš s Peťou o činnosti, **vždycky přidej i název** — číslo samo o sobě nestačí
k tomu, aby bylo jasné, že jsme u téže věci.

