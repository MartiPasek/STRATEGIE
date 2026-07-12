# 🔌 Rozvaděče — orientační směrnice (řada přístupnost AI)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🔌 Rozvaděče — orientační směrnice (řada přístupnost AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Řada **AI** = směrnice, které píšu já a Marti‑AI pro
> vlastní orientaci — destilát existujících firemních směrnic + naše postřehy a „MD" věci.
> Není to náhrada oficiálních směrnic (ty jsou zdroj pravdy), je to **mapa a paměť** pro nás.
> Zdroj: RAG směrnic (633 směrnic + 702 příloh, `@@KB`), reálné poptávky, SRDCE FIRMY.
> Čti spolu s `docs/srdce_firmy_kalkulace_nabidky_analyza.md` (kalkulace/nabídka) a
> `docs/smernice_rag_navrh.md` (jak RAG funguje).

## 1. Co firma dělá (obrázek provozu)

EUROSOFT / INTERSOFT je **zakázková výroba rozváděčů** (řídicí a silové rozvaděče,
Schaltschränke) — kusová a malosériová, silně **exportní** (dokumentace CZ/EN/DE).

**Dvě sesterské výrobní entity** (společné vedení, „vnitroskupina"):
- **EUROSOFT‑Control s.r.o.** — odštěpný závod Plzeň‑jih, Plzeňská 375, Štěnovice.
- **INTERSOFT‑Automation s.r.o. (IAP)** — Nepomucká, Plzeň. (Vydává návody k údržbě rozváděčů.)
- STRATEGIE‑System s.r.o. = softwarová/produktová entita (naše platforma).

**Zákazníci** (převážně němečtí OEM, každý má vlastní výrobní standard):
ABSAUGWERK, KOHLBACH, DÜCKER, JUNKER, AUTKOM, FOUNDRY4, XELLA, SKF, RBC… →
proto je 230 směrnic „Výroba rozvaděčů <ZÁKAZNÍK> – <téma>".

**Klíčoví dodavatelé komponent:** Rittal (skříně, klima, Perforex), Siemens (jištění,
PLC, PAC, řízení), Rockwell/Allen‑Bradley (svorky, tlačítka), Schrack, Phoenix Contact,
Legrand, Murr, Weidmüller. Objednací číslo výrobce = univerzální klíč (viz SRDCE FIRMY).

## 2. Tok výroby rozvaděče (proces, jak ho čtu ze směrnic)

1. **Poptávka → nabídka/kalkulace** (Eliška). Koeficient u dílu → hodiny montáže + **VKM**
   (Verklemmungsmaterial = svorky/vodiče/kabely/drobnosti). Marže, projekt, revize, transport.
   Detail v SRDCE FIRMY.
2. **EPLAN P8 dokumentace** (Čepický) → schémata + **kusovník (Stückliste)**. Někdy dělá EPLAN
   zákazník a pošle jen PDF + svůj kusovník se svými čísly (→ převodní tabulka čísel).
3. **Objednání materiálu** dle kusovníku (směrnice „Objednání materiálu pro výrobu rozvaděčů").
4. **Mechanická příprava** — CNC **Rittal Perforex** (vrtání/frézování montážních desek a skříní),
   montážní deska (LT/ST varianty), rozměry přístrojů, řezání DIN lišt a kabelových kanálů.
5. **Montáž komponent** na montážní desku — dle **zákaznického standardu** (rozmístění, typové
   desky, spodní plech pro vývodky, uchycení kabelů).
6. **Zapojení / vodiče:**
   - **Barevné značení žil** (STANDARD – ČSN/zákazník),
   - **svorkovnice** (krytky přívodních svorek — orig. od výrobce, máme skladem),
   - **pospojení PE** (způsob dle zákazníka, PE a N šíny),
   - **VKM** (spojovací materiál),
   - **popis vodičů / Drahtbeschriftung** (Legrand / Murr / Phoenix / Partex; jednoduchý /
     průběžný / jednoznačný).
7. **Značení** — typové štítky, popisky přístrojů (DE u něm. zákazníků), DIN.
8. **Zkoušky / revize** dle **EN 61439‑2**: izolační zkouška (protokol), zkouška ochranného
   vodiče (protokol), **deník zkoušek / hlášení o chybách**, prohlášení o shodě + prohlášení výrobce.
9. **Balení + dokumentace** — balení rozvaděče, **návody k manipulaci/instalaci/provozu/údržbě**
   (IAP, CZ/EN/DE), schémata, klemmenplány, výkresy montážní desky, kusovníky, PDF.
10. **Expedice** — doprava, termíny (centrála – informace o termínech a dopravě rozvaděčů).

## 3. Vzorec „per‑zákazník standard" (klíčový postřeh)

Každý zákazník = **balík směrnic se stejnou kostrou** (montážní desky, svorkovnice, vodiče,
pospojení PE, štítky, DIN, popis, balení), ale **jinými detaily**. To je nasbírané know‑how —
„recept" na rozvaděč pro daného zákazníka. Když přijde nová zakázka od známého zákazníka,
tenhle balík je návod. **Digitalizační příležitost:** propojit kalkulaci (SRDCE FIRMY) s
per‑zákazník standardem → generátor pracovního postupu + kontrola úplnosti dle zákazníkova receptu.

## 4. Slovník (ať v tom Marti‑AI i já čteme rychle)

| Pojem | Význam |
|---|---|
| **VKM** (Verklemmungsmaterial) | spojovací materiál — svorky, vodiče, kabely, drobnosti; v kalkulaci odvozen z koeficientu |
| **Drahtbeschriftung** | popis/značení vodičů (systémy Legrand/Murr/Phoenix/Partex) |
| **Perforex** | Rittal CNC centrum na vrtání/frézování desek a skříní |
| **Montážní deska** | nosná deska v skříni, na ní přístroje + DIN lišty + kanály (LT/ST varianty) |
| **Pospojení PE** | propojení ochranných vodičů / PE a N šíny |
| **EN 61439‑2** | norma pro rozváděče — izolační + ochranný vodič zkoušky, protokoly |
| **Kusovník / Stückliste** | seznam komponent (z EPLANu nebo od zákazníka) |
| **Koeficient** | u dílu → hodiny montáže + VKM (know‑how, SRDCE FIRMY) |
| **IAP** | INTERSOFT‑Automation (sesterská výrobní entita, návody k údržbě) |

## 5. Moje postřehy a otevřené otázky (živé — doplňuje Claude + Marti‑AI)

- **Datová díra: 359 `.doc` příloh se extrahovalo jako balast** (starý OLE Word). PDF (253) jsou
  čisté. **TODO #1 RAG kvality:** doextrahovat `.doc` přes antiword/catdoc/LibreOffice na cloudu
  a přeulozit `text_extract`. Bez toho je půlka know‑how v RAG nečitelná.
- **Postřeh:** proces je silně **standardizovaný per zákazník** — ideální pro AI generátor
  postupu + kontrolu úplnosti (chybějící skříň/komponenta), navazuje na Eliščin bod „odchytit chybějící díl".
- **Otázka pro Marti/Elišku:** kde je „master" seznam typových standardů per zákazník (je to jen
  množina směrnic, nebo existuje i souhrnný list)? A jak se verzují, když zákazník změní požadavek?
- **Napojení:** kalkulace (koeficient/VKM) × per‑zákazník standard × sklad/dodací lhůty (SRDCE FIRMY
  Fáze 1) = jádro digitalizace obchodu i výroby.

## 6. Jak tohle udržovat (řada AI)

- Tahle a další „AI" směrnice žijí jako `docs/*.md` **a zároveň** jako řádky v RAG s
  `pristupnost_text='AI'` (vidí je jen Claude, Marti‑AI, rodiče) → `@@KB … | 3` je najde.
- Když se něco naučím z RAG nebo od lidí, **připíšu sem postřeh** (sekce 5) a přegeneruju RAG řádek.
- Další plánované AI směrnice: `Zakaznici.md` (recept per zákazník), `Komponenty_dodavatele.md`
  (kdo co dělá, lhůty), `Zkousky_normy.md` (EN 61439‑2 checklist), `Kalkulace_engine.md` (z SRDCE FIRMY).

— Claude (ID23) 🔌📚


