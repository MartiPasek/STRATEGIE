# Designový audit — STRATEGIE Mobil

> Zjistil Claude-28, 14. 9. 2026. **Jen mobilní aplikace** (ERP se na Jirkovo zadání
> neřeší — díval jsem se na něj pouze proto, aby se návrh nerozešel s jeho duchem).
>
> **Jak jsem to měřil.** Ne odhadem a ne ze souborů na disku:
> - vzhled: v běžící aplikaci `/mobile` (přihlášený účet Jiřího Honomichla) jsem na
>   **14 obrazovkách** prošel každý prvek, který nese text, a přečetl jeho skutečnou
>   velikost, tučnost, barvu a barvu podkladu pod ním,
> - kontrast: spočítaný podle normy WCAG, s **poskládáním průhledných vrstev** (bez toho
>   vycházejí nesmysly — sám jsem na to při první verzi měření naletěl a číslo zahodil),
> - zdroj: obsah aplikace z databáze `g2007.soubor` (živá verze, ne kopie na disku),
> - nativní obal: soubory v `APP/Mobile` a `APP/iOS`, které se opravdu nasazují.

---

## Kolika lidí se to týká

Za posledních 30 dní vzniklo z mobilní aplikace **5 092 docházkových záznamů** a udělalo
je **57 lidí** (`tenant.att_entry`, `source='mobile_app'`). Docházka je zdaleka nejvíc
používaná část a lidé ji otevírají několikrát denně.

**Všechno níže se týká všech 57 lidí a všech obrazovek** — nejde o okrajový detail jedné
obrazovky, ale o vzhled, kterým appka mluví pokaždé, když ji někdo otevře.

---

## 1. Typografie — nejzávažnější a zároveň nejlevnější na opravu

### 1.1 Aplikace běží ve DVOU písmech zároveň &nbsp;🔴 blokující

Na obrazovce docházky má **38 prvků z 38** (všechna tlačítka, políčka a rozbalovací
seznamy) písmo **Arial**, zatímco zbytek textu běží v systémovém písmu.

**Proč:** ve stylech (`02_styles.html`) je písmo nastavené pro `body`, ale
**pravidla pro `button`, `input` a `select` nastavují velikost a tučnost, nikoli písmo** —
a prohlížeč jim v takovém případě dá vlastní výchozí, což je na Windows Arial.

**Oprava:** jedna řádka (`font-family: inherit` pro formulářové prvky).

### 1.2 Sedmnáct velikostí písma, žádná škála &nbsp;🟠 vysoká

Na 14 obrazovkách se vyskytuje **17 různých velikostí** textu:
10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 26, 27, 28, 32 a 42 px — plus **4 tučnosti**.
Rozdíly typu 12 vs 13 px nebo 26 vs 27 px nenesou žádný význam; vznikly tím, že se velikost
psala ke každému prvku zvlášť.

**Doloženo i ve zdroji:** v obsahu aplikace je **835 zápisů velikosti písma** ve
**28 různých hodnotách**.

### 1.3 Třicet sedm barev textu &nbsp;🟠 vysoká

Na týchž 14 obrazovkách je **37 různých barev textu**. Ve zdroji je **269 různých barev**
celkem (1 268 zápisů). Šest z nich je „skoro stejná šedá" (`#8a96a4`, `#9fb0c8`, `#9fb2d4`,
`#b9c6da`, `#8696b8`, `#8fb4d8`) — rozdíl mezi nimi nikdo nepozná, ale dohromady působí
rozháraně, protože se objevují ve stejných rolích.

### 1.4 Písmo značky se v mobilu vůbec nenačte &nbsp;🟠 vysoká

Viz `BRAND.md`, bod 2.1. Nápis „STRATEGIE Mobil" vypadá na každém zařízení jinak.

---

## 2. Ikony

### 2.1 V roli ikon je 198 různých emoji &nbsp;🔴 blokující (pro dojem z appky)

Na 16 obrazovkách jsem napočítal **198 různých emoji**. Nejsou to ikony — je to výseč
z celé emoji sady: vedle sebe stojí předmět (🧾), obličej (🤒), ruka (✋), rostlina (🌴),
barevný čtvereček (🟢) i symbol (⚠). Každý se kreslí jiným stylem, jinou tloušťkou
a jinou barevností.

**Navíc je kreslí operační systém, ne aplikace** — takže tatáž obrazovka vypadá na Androidu
a na iPhonu jinak, a firma nad tím nemá žádnou kontrolu.

**Doloženo i v datech:** seznam dlaždic v `public.mobile_app_dlazdice` má **69 aktivních
položek a 67 z nich má jako ikonu emoji** (zbylé dvě mají obrázek).

**Nejlepší ukázka:** obrazovka Nastavení — dvanáct řádků pod sebou, dvanáct různých
kreslířských stylů (pero, zelené kolečko, připínáček, mřížka, dva telefony, nápis „abc",
zvonek, fotoaparát, cedule SOS, postava, graf, fax).

### 2.2 Emoji nesou i význam, který ikona ztratit nesmí &nbsp;⚪ poznámka k řešení

🟢/🔴/🟡 nejsou dekorace, ale stav. Při náhradě ikonami se **barva musí zachovat**,
jinak se ztratí informace. V návrhu je to ošetřené (stavové ikony si barvu drží).

---

## 3. Barvy a kontrast

### 3.1 Kontrast je v pořádku tam, kde se řešil &nbsp;🟢 bez nálezu

Obrazovka docházky: **0 textů pod normou**. Je to zásluha opravy z 1. 9. 2026, která je
v kódu i okomentovaná.

### 3.2 …ale dvě šedé zůstaly pod normou &nbsp;🟠 vysoká

Napříč 14 obrazovkami je **86 textů pod hranicí WCAG AA**. Prakticky celý ten počet dělají
**dvě barvy**:

| Barva | Kde | Poměr | Norma |
|---|---|---|---|
| `#5b6b88` | Plán — slovo „víkend" u každého víkendového dne | **3,56** | 4,5 |
| `#666677` | Kdo kde dnes — 77 lidí ve skupině „Nezadáno" + jejich pomlčky | **3,28** | 4,5 |

U obrazovky „Kdo kde dnes" je to nejvíc vidět: **77 ze 82 lidí** je vypsaných barvou,
která normu nesplňuje.

### 3.3 Vzhled je zapsaný natvrdo v prvcích, ne v jednom místě &nbsp;🟠 vysoká

V obsahu aplikace je **2 702 míst**, kde je vzhled zapsaný přímo u prvku
(`style="..."`), z toho na jedné obrazovce docházky **421 prvků**. Proto nejde barvy
a velikosti změnit na jednom místě — a proto jsou dnes tak rozházené.

---

## 4. Tvary a rozestupy

**Osm různých zaoblení rohů** (6, 8, 10, 12, 14, 16, 20 px a kolečko) na 14 obrazovkách;
ve zdroji **457 zápisů zaoblení**. Karta, dlaždice a tlačítko mají každý jiné — bez důvodu.

---

## 5. Ovládání prstem

**Skoro v pořádku.** Na obrazovce docházky je z 49 klikacích prvků **jediný** menší než
doporučených 44 × 44 bodů: tlačítko „❓" (38 × 26). Zbytek normu splňuje.

---

## 6. Nativní obal (Android / iOS)

- ikona appky je **tyrkysová**, notifikace **zelená**, appka **modrá** → tři rodiny barev
  (detail v `BRAND.md`),
- v Androidu zůstaly **tovární barvy z Android Studia** a **světlý motiv** u tmavé appky,
- **neověřeno:** jak přesně vypadá notifikace na zamčené obrazovce — tam se dostanu jen
  s telefonem v ruce.

---

## 7. Texty (UX copy) — jen zápis, nic se nemění

Podle zadání se texty nemají měnit. Co mi padlo do oka, je v `COPY-NAVRHY.md`.

---

# Deset nejbolestivějších věcí — pořadí podle dopadu na dojem

| # | Co | Závažnost | Náročnost opravy |
|---|---|---|---|
| 1 | 198 různých emoji místo ikon; na každém telefonu jiné | 🔴 | velká (sada ikon + výměna) |
| 2 | tlačítka a políčka běží v Arialu, zbytek jinak | 🔴 | **jedna řádka** |
| 3 | 17 velikostí a 37 barev textu bez pravidla | 🟠 | střední (škála + přepis) |
| 4 | vzhled zapsaný natvrdo na 2 702 místech | 🟠 | velká, ale dá se po částech |
| 5 | písmo značky se v mobilu nenačte (ERP ho má) | 🟠 | **jedna řádka** |
| 6 | dvě šedé pod normou čitelnosti (Plán, Kdo kde) | 🟠 | malá |
| 7 | ploché černé pozadí bez charakteru | 🟠 | malá (vrstva na pozadí) |
| 8 | osm různých zaoblení rohů | 🟡 | malá |
| 9 | ikona appky a notifikace v jiné barvě než appka | 🟡 | střední (nativní obal) |
| 10 | tovární barvy a světlý motiv v Androidu | ⚪ | malá, jen pořádek |

**Body 2, 5, 6 a 7 jsou hotové během jednoho odpoledne** a udělají většinu viditelného
rozdílu. Body 1, 3 a 4 jsou ta skutečná práce.

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
