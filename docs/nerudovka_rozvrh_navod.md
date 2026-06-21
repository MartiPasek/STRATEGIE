# 🗓️ Návod: tvorba rozvrhu (Nerudovka) — postup, podklady, pravidla

Praktický průvodce pro příští tvorbu rozvrhu se mnou (Claude). Shrnuje, **co a v jakém
pořadí mi dodat**, **jak postupuju**, **všechna pravidla** a **závěrečné kontroly**.
Vychází z rozvrhu 2026/27 (varianty A–D, obory GD + MI).

---

## 1) Co mi dodat a v jakém pořadí (checklist podkladů)

Čím dřív mám kompletní obrázek, tím míň přegenerovávání. Ideální pořadí:

1. **Přístup k datům školy** — Bakaláři most (`db=bakalari`) běží, takže si vytáhnu sám:
   - **úvazky** (`ruvazky`, `PLAT_OD` daného škol. roku) — kdo co kolik učí,
   - **předměty** (`r_pred` / `a_r_pred`) — názvy, **zkratky** (ZKRATKA), vhodné učebny (MIST_VHOD),
   - **učebny** (`bakalari_mistnost`) — zkratky, budovy, kapacity,
   - **učitelé** (`bakalari_ucit`) — jména, interní kódy,
   - **třídy** (`r_trid`) — překlad kódů na zkratky (1G ≠ 1.GD!).
2. **Učební plány oborů** (PDF/tabulka) — **klíčové!** Počty týdenních hodin po ročnících
   + struktura **zaměření / dělení tříd na skupiny**. Bez nich nevím, co běží paralelně.
   (U nás: MT = 2 zaměření Foto/AV × Game/Anim; GD = grafika × ilustrace; DI samostatně.)
3. **Pravidla dělení skupin** — které předměty se dělí na skupiny a které jsou pro celou
   třídu. (Viz §3C.)
4. **Individuální omezení učitelů** — kdo kdy nesmí/musí učit, kolik dnů. (Viz §3D.)
5. **Učebnová pravidla** — který předmět do které učebny, dvě budovy + přejezd. (Viz §3E.)
6. **Časová pravidla předmětů** — co do 7. h, co ve dvou dnech, oběd, max hodin v kuse. (§3A/B.)

> 💡 Nejlepší je poslat **učební plány hned na začátku** (bod 2) — z nich odvodím většinu
> struktury. Pak doplnit omezení učitelů a učeben. Pravidla klidně **hromadně v jedné zprávě**,
> ať generuju jednou načisto, ne po kouskách.

---

## 2) Jak postupuju (pořadí generování — „po blocích")

Generuju **blokově**, každý blok jde smazat a přegenerovat zvlášť:

1. **Cizí jazyky — celá škola.** Synchronizované paralelní „bandy": mezitřídní jazykové
   skupiny (NJ/FJ/ŠJ/RJ) běží **ve stejný čas**, žáci se rozdělí. Backbone celého rozvrhu.
2. **Odborné předměty — nejdřív úzké hrdlo.** Tady je trik (tvůj instinkt): **začít od
   nejnabitější třídy (4.MI)** a od **mediálních učeben** (jen IT2 + MM). Řeším etapově,
   třídu po třídě, každou na optimum (CP-SAT solver).
3. **Tělocvik — naposledy.** Je nejpružnější (jedna tělocvična, ale lichý/sudý cyklus
   zdvojuje kapacitu + spojené skupiny kluci/holky). Doskládá se kolem hotových odborných.

**Proč tohle pořadí:** tvrdá omezení (málo mediálních učeben, dvě budovy) musí dostat
prostor první; pružné věci (TV) se vejdou kolem. Obráceně se generátor zasekne.

**Klíčové modelové objevy (bez nich to nejde):**
- **Třída = víc paralelních kohort.** MI = design interiéru ∥ multimédia (+2 zaměření);
  GD = grafika ∥ ilustrace. Společné předměty (ČJ, MAT, dějiny umění…) drží celou třídu;
  odborné jedou po kohortách souběžně. Bez tohohle „nevejde se" (sčítají se obě poloviny).
- **Hodiny z úvazku jsou za 14 dní → dělím /2 na týden.**
- **Stejný předmět v obou oborech** (Počítačová grafika, Figurální kresba) = dvě
  samostatné skupiny (DI i MT / G i I).

---

## 3) Všechna pravidla (kompletní sada)

### A) Časová pravidla předmětů
- Český jazyk, Matematika, Fyzika, Chemie, **Dějiny umění** → končit **do 7. h**.
- **Matematika** ve **dvou různých dnech**; **Fyzika** v 1.GD a 1.MI ve dvou dnech.
- **Občanská nauka**: má-li 2 h/týden, každá v **jiný den**.
- **Dějiny umění**: ideálně po 1 hodině v různých dnech.
- **Bloky drží pohromadě** — předmět se 2 h jde jako dvouhodinovka za sebou, 3 h jako
  trojblok. **Typografie + Písmo = jeden trojblok.**

### B) Den, oběd, přestávky
- **V pátek** končit nejpozději 7. h (výjimka: dvouhodinovka TV do 8.).
- **Oběd: každý student musí mít volnou hodinu** v poledním okně (4.–7. h). Hlídá to tvrdé
  pravidlo (dvě poloviny třídy mohou obědvat v různou hodinu).
- **Max ~7 hodin výuky v kuse** — pak pauza před odpoledním blokem. (Zajištěno obědovým pravidlem.)
- **Odpolední bloky** běžné: 2 na třídu (někdy 3, hlavně 4.GD), klidně do 10. h (16:40).

### C) Dělení tříd na skupiny
- **GD = dvě poloviny: grafika (G) + ilustrace (I).** Dělí se: Výtvarná příprava, Výtvarná
  tvorba, Písmo, Typografie, Prostorový design, Počítačová grafika, Figurální kresba,
  Grafické umělecké techniky, Digitální fotografie, Grafický design a navrhování.
  Celá třída (1 skupina): Technologie, Marketingová komunikace, Dějiny grafického designu,
  Dějiny umění + akademické předměty.
- **4.GD:** GDN dělené na **4 skupiny** (Beran G1/G2 = grafika, Němejc I1/I2 = ilustrace).
- **MI = dvě poloviny: multimédia (MT) + design interiéru (DI).** MT se dál dělí na dvě
  **zaměření** (Foto+audiovize: AVT2, Foto2 ∥ Game+animace: Game2, Animace2) — běží souběžně.
  Společné a MT-povinné drží celou MT kohortu.
- **Stejný předmět u obou oborů** = dvě skupiny (DI i MT), nesmí se sloučit.

### D) Individuální omezení učitelů
| Učitel | Omezení |
|---|---|
| Ždimerová, Vroblová | učit nejdřív od **2. h** |
| Šedová | končit do **7. h** |
| Kubálková | ve **středu** až od **4. h** |
| Layerová | v **pátek** končit **4. h** |
| Vlková | **mimo čtvrtek**, od 2. h (varianta D navíc **mimo pátek**) |
| Hlaváč | ve **čtvrtek** končit **3. h** |
| Tesliuk | učí **jen v pátek** (proti webdesign blokům Hlaváče) |
| Pejřimovská | úvazek do **4 dnů**, volné **Po nebo Pá** |
| Švehlová | do **3 dnů**, dva po sobě jdoucí |
| Beran | do **4 dnů** |
| Rousová | do **4 dnů** |
| Toušová | do **3 dnů** |
| Rešl | do **2 dnů** |

### E) Učebny a dvě budovy
- **Ateliéry** (zkratky začínající **B**: BK, BA, BD1, BD4, BNA, BPG, BŠ) vs **Nerudovka**
  (ostatní: 2, 4, 5, IT2, MM…). **Mezi budovami je hodina přejezdu** — předměty v ateliérech
  a v Nerudovce **nesmí být za sebou** (u třídy ani u učitele).
- **Mediální učebny: jen IT2 + MM.** Animace, AVT, Game, Motion, Web, 3D → tam (3D jen IT2/MM).
- **Počítačová grafika** smí i do BŠ, BNA, BPG (pozor na přejezd).
- **Figurální kresba** → BA/BK. **Fotografie** → MM. **Digitální fotografie** → BPG.
- **Tělocvik** = tělocvična (zkr TV); u GD/MI **každý týden** ve stejný čas, ostatní lichý/sudý.

---

## 4) Co generátor umí a co zůstává na člověku

- **Umí:** postavit kostru se všemi tvrdými pravidly (jazyky + TV + odborné), bez konfliktů
  učitelů/učeben, s obědem, dělením skupin, časovými i denními omezeními. Vygenerovat **více
  variant** (A/B/C/D) k porovnání, libovolné měkké pravidlo navíc (např. „Vlková bez pátku").
- **Zůstává na člověku:** posledních pár nejnabitějších bloků (4.MI/4.GD), kde je škola
  blízko kapacitě dvou mediálních učeben — doladí se ručně do odpoledních oken. To je normální
  poslední vrstva (generátor dá 90+ %, člověk dotáhne).

---

## 5) Závěrečné kontroly (vždy před odevzdáním)

Po každém přegenerování projedu napříč všemi variantami:
1. **Konflikty učitelů** (odborné + jazyky) — 0. (TV spojené skupiny = jeden učitel/víc tříd = OK.)
2. **Konflikty učeben** — 0.
3. **Časová omezení učitelů** — 0 porušení.
4. **Denní limity učitelů** (Rousová ≤4 dny atd.) — 0.
5. **Oběd pro každého studenta** (per skupina, ne agregát třídy) — 0 bez oběda.
6. **Speciální pravidla varianty** (např. Vlková v pátek v D) — 0.

---

## 6) Praktické (jak komunikujeme)
- Píšeš mi do **chatu s Claudem** v appce (nebo přes Martiho), já čtu/odpovídám přes most.
- Posílej **konkrétně** („typografie = trojblok s písmem", „Vlková bez pátku") — hned to zapracuju.
- **Učební plány a číselníky** klidně jako PDF/přílohu — přečtu je.
- Hotový rozvrh je v appce: **dlaždice „Varianty rozvrhu"** (A/B/C/D, pohled tříd i učitelů,
  zkratky, učebny, barvy podle učitele, dělené skupiny vedle sebe) + **„Přehled po ročnících".**

— Claude, 21. 6. 2026
