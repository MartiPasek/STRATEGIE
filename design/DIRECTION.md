# Návrh vzhledu — STRATEGIE Mobil

> Claude-28, 14. 9. 2026. Zadání od Jirky Honomichla: **vylepšit v duchu toho, co systém
> už má** — ne vymyslet novou tvář. Modrý nápis zůstane modrý; smí se změnit odstín,
> velikost, řez nebo provedení, ne identita.

---

## Co platí v obou variantách

### Písmo

**DM Sans** — jedna rodina na celou aplikaci. Není to nová volba: **ERP v něm už běží**
a mobil ho má předepsaný v nápisu (jen se nikdy nenačte). Doplněním se obojí potká.

| Role | Velikost | Řez | Na co |
|---|---|---|---|
| popisek sekce | 11 px | 600–700, rozpal 0,09 em | „DOCHÁZKA", „NEMOC A LÉKAŘ" |
| vedlejší text | 12,5 px | 400 | podtitulky, vysvětlivky |
| běžný text | 14,5 px | 400 | odstavce |
| řádek seznamu | 15,5 px | 500 | název položky |
| zvýrazněný řádek | 17 px | 600 | důležitá hodnota |
| nadpis obrazovky | 21 px | 700 | „Moje absence" |
| velké číslo | 28 px | 700 | údaje v přehledech |

Sedm stupňů místo sedmnácti. **Číslice mají stejnou šířku** (tabular) — hodiny a částky
při přepočtu neposkakují.

**A jedna řádka, která opraví nejvíc:** tlačítka, políčka a rozbalovací seznamy dostanou
`font-family: inherit`. Dnes běží v Arialu, protože jim nikdo písmo nenastavil.

### Barvy — čtyři role místo 37 odstínů

| Role | K čemu |
|---|---|
| **hlavní text** | to, co se čte |
| **vedlejší text** | doplněk k hlavnímu |
| **tlumený text** | popisky, jednotky, vysvětlivky |
| **barva významu** | modrá = odkaz a výběr · zelená = běží/hotovo · jantarová = pozor · červená = chyba/zrušeno |

Modrá, zelená, jantarová i červená **zůstávají v rolích, které už mají** — nic se
nepřebarvuje na jiný význam.

### Ikony

Vlastní sada **90 tahových ikon**: mřížka 24 × 24, tloušťka tahu 1,75, zaoblené konce,
**bez vlastní barvy** — barvu dědí po textu, takže vždy sedí k řádku, ve kterém stojí.
Nahrazuje 198 emoji (namapováno je 209 zápisů emoji na těch 90 ikon).

**Stavové barvy zůstávají:** 🟢 zelená, 🔴 červená, 🟡 jantarová si barvu drží,
protože nesou informaci, ne dekoraci.

*(Ikony jsou nakreslené od základu pro tenhle návrh — nepoužívá se žádná knihovna,
takže není co řešit s licencí.)*

### Zaoblení a rozestupy

Tři stupně zaoblení místo osmi: **8 / 12 / 16 px** (varianta A), **10 / 14 / 18 px** (B).

### Pohyb

Animace jen tam, kde něco sděluje: stisk tlačítka (drobné zmenšení) a pulzující rámeček
u neschválené docházky, který v aplikaci **už je a zůstává**. Nic nového nepřibývá.

---

## Pozadí — mramorování místo ploché černé

Vrstva leží **pod obsahem**, neroluje s ním a skládá se ze tří věcí:

1. **světlo shora** — měkký kruh v modré, nejsilnější nad horní hranou obrazovky,
2. **druhý, slabší nádech fialové** od pravého horního rohu,
3. **jemné žilkování** (mramorování) v modrošedé, velké měřítko, aby se vzor na výšku
   telefonu ani na šířku desktopu **viditelně neopakoval**.

**Nesoutěží s obsahem:** nejsilnější je nahoře a v prázdných místech; pod hustým seznamem
ho překryjí karty. Žádný text tedy neleží na nejsvětlejším místě textury.

**Výkon:** je to jedna vykreslená vrstva čistě z CSS — **žádný obrázek, build neroste
ani o bajt**, a protože se neroluje, nemá co zdržovat posouvání seznamu.
*(Neověřeno: chování na starším Androidu — chce to změřit na skutečném slabším telefonu,
až bude návrh schválený. Ústupová varianta je připravená: při zapnutém „omezit pohyb"
se textura vypne a zůstane plochá barva.)*

---

## Varianta A — „Ocel"

**Povaha:** klid, přesnost, blízkost ERP. Appka, kterou má člověk otevřenou celý den.

- podklad chladný grafit, mramorování **sotva znatelné**
- modrá **přesně ta stávající** `#4f8ef7`, jinak jen šedá škála — žádná druhá barva navíc
- karty: plochá výplň + **vlasová linka**, žádné stíny (na tmavém podkladu je linka
  čitelnější než rozmazaný stín)
- **jedna hlavní akce na obrazovku:** START zůstává plný zelený, ostatní zelená tlačítka
  vedle něj jsou jen obtažená — přestanou se s ním přetahovat o pozornost
- popisky sekcí tiché šedé, nadpisy sevřené

## Varianta B — „Modré světlo"

**Povaha:** teplejší, výraznější. Appka, kterou člověk otevře občas a musí se hned chytit.

- podklad tmavě modrý, shora dopadá **zřetelné modrofialové světlo**, mramorování je
  v prázdných místech vidět
- modrá o odstín světlejší (`#5b95f8`) + **fialová jako druhý hlas** — tedy přesně ta
  dvojice, kterou má nápis STRATEGIE
- karty vystouplé: horní světlá hrana + měkký stín
- hlavní tlačítka v přechodu **modrá → fialová** (logo přeneseno do ovládání)
- popisky sekcí modré, o stupeň větší rozpal

---

## Kontrola proti klišé

Prošel jsem návrh proti otázce „došel bych k tomuhle u jakékoli jiné aplikace?":

| Obvyklý automatismus | Jak je ošetřený |
|---|---|
| tmavě šedá + jeden neonový akcent | akcent není neon — je to **existující** firemní modrá, a nese ji i ERP |
| všechno nasekané do stejných karet se stejným stínem | ve variantě A **nejsou stíny vůbec**; hloubka je linka a odstín |
| přechod jako dekorace | přechod je **jen** v logu a (ve variantě B) v hlavním tlačítku — nikde jinde |
| proložené VERZÁLKY nad každým nadpisem | verzálky jsou **jen** popisky sekcí, které v aplikaci už dnes jsou |
| šipka „→" za textem tlačítka | není použita |
| strojopisné písmo pro malé údaje | není použito; místo toho stejně široké číslice v běžném písmu |

**Co je na tomhle návrhu vlastní:** nosným gestem je **světlo dopadající shora na tmavý
grafit** — vychází z toho, že appka se používá v dílně a ve skladu, kde se na displej dívá
člověk shora dolů, a z barev, které firma už má. Všechno ostatní je záměrně tiché.

**Nadčasovost:** vyhýbám se tomu, co zestárne — žádné sklo a rozostření, žádné neony,
žádné přehnané zaoblení. Tahové ikony, jedno písmo a tichý podklad vypadaly dobře před
deseti lety a budou i za deset.

---

## Co tenhle návrh záměrně NEŘEŠÍ

- **rozložení obrazovek** — zůstává do posledního prvku stejné,
- **texty** — beze změny, návrhy jsou zvlášť v `COPY-NAVRHY.md`,
- **ERP** — na Jirkovo zadání mimo záběr,
- **ikonu aplikace a barvu notifikací** — je to nativní obal, samostatný krok po schválení,
- **světlý režim** — aplikace ho nemá a nebyl zadán.

---

# ✅ ROZHODNUTO — 14. 9. 2026

**Rozhodl Jiří Honomichl:** jde se **variantou B („Modré světlo")**, ale
**ikony a ikony dlaždic zůstávají původní** (emoji).

Co z návrhu tedy platí: písmo DM Sans, sedmistupňová škála velikostí, čtyři role barvy,
modré popisky sekcí, mramorovaný podklad se světlem shora, vystouplé karty,
hlavní tlačítka v přechodu modrá→fialová, tři stupně zaoblení.

Co z návrhu **odpadá**: výměna emoji za tahovou sadu. Sada 90 ikon zůstává nakreslená
v `reskin/icons.js` a podoba s ní je nafocená v `preview/*-B-s-novymi-ikonami.png`,
kdyby se k tomu někdy vrátil.

> ⚠️ **Nález z auditu tím nezmizel, jen se k němu rozhodlo jinak:** 198 různých emoji
> kreslí operační systém, takže tytéž obrazovky vypadají na Androidu a na iPhonu jinak
> a firma nad tím nemá kontrolu. **Není to chyba — je to vědomé rozhodnutí Jirky Honomichla
> ze 14. 9. 2026.** Zapsáno proto, aby to za tři měsíce nikdo „neopravoval" bez ptaní.

---

# 🚀 NASAZENO — 14. 9. 2026, 09:03

Zapsal Claude-28 do `apps/api/static/mobile_parts/02_styles.html` (blok na konci
souboru), plus `00_head.html` (načtení písma) a dvě cílené opravy barvy textu.
Publikováno do `apps/api/static_db/mobile.html`, ověřeno naživo: 127 obrazovek,
všechny texty v jednom písmu.

## Co se ukázalo až naostro (a co z toho plyne pro příště)

1. **Písmo se předepsalo, ale nenačítalo.** Blok stylů uměl DM Sans předepsat,
   jenže stránka ho odnikud nestahovala — chyběl odkaz v hlavičce. Dokud se
   nedoplnil do `00_head.html`, kreslila se aplikace dál systémovým písmem.
   *Poučení: předepsat písmo a načíst písmo jsou dvě různé věci; kontroluj
   měřením šířky textu, ne tím, co hlásí prohlížeč jako „font-family".*

2. **Podklad ležel pod neprůhledným pozadím stránky a nikdo ho neviděl.**
   Vrstva s mramorováním je pod obsahem (`z-index:-1`), ale `body` mělo vlastní
   neprůhlednou barvu, která ji překryla. Barvu proto nese `html` a `body` je
   průhledné. *Poučení: „vrstva se vykresluje" se musí ověřit tím, že se do ní
   dá křiklavá barva — ne tím, že se pravidlo tváří správně.*

3. **Dvě obrazovky si kreslí vlastní plochu přes celou výšku** (Domů a Firma),
   takže na nich společný podklad nebyl vidět a Firma měla jiný odstín než
   zbytek. Obě jsou nově průhledné.

4. **Vypínání textury při systémovém „omezit pohyb" bylo špatně.** Textura se
   nehýbe, takže ji není proč vypínat — a Jirka to má zapnuté, takže by nové
   pozadí nikdy neviděl. Pravidlo odstraněno.

5. **Síla textury se musela ladit naostro.** První pokus byl neviditelný (viz
   bod 2), druhý po opravě příliš silný (text na světlých místech ztrácel
   čitelnost). Výsledek: žilkování na 0,34, a hlavně **maska, která texturu
   směrem dolů zeslabuje na čtvrtinu** — nahoře charakter, pod hustým obsahem klid.

6. **Šipky „›" v seznamech** vyšly po nasazení na 4,38 (norma 4,5) — vlastní
   regrese, srovnáno na tlumenou šedou.
