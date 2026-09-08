# 🏦 Banka — průvodce účtováním a párováním plateb

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🏦 Banka — průvodce účtováním a párováním plateb

**Pro:** Petra Šafránková (účetní) · **Konzultace:** s instancí 26 (Petřin Claude) osobně
**Verze:** 23. 6. 2026 · **Vlastník modulu:** Petra (přístup: Petra / vedení / skupina Účetnictví)

Tento dokument je učební podklad. Není to jen návod na tlačítka — vysvětluje i **proč**, aby
dávalo smysl, co systém dělá. Instance 26 ho s tebou projde krok po kroku a odpoví na dotazy.

---

## 1. Co vůbec znamená „účtovat banku" (základy)

Banka nám každý den pošle **výpis** — seznam plateb, které přišly (příjmy) a odešly (výdaje).
S každou platbou musíme udělat dvě věci:

1. **Spárovat** ji — určit, **čeho se týká**: které faktury, kterého zákazníka/dodavatele,
   které zakázky, jakého poplatku nebo daně. (Např. „přišlo 82 740 Kč → je to úhrada
   faktury od KROMEXIM za zakázku VR10641".)
2. **Zaúčtovat** ji — zapsat ji do **účetního deníku** na správné **účty**.

### Účet, MD a DAL (podvojné účetnictví v kostce)
Každý účetní zápis má **dvě strany**: **MD (Má dáti)** a **DAL (Dal)**. Peníze vždy
„odněkud někam" — proto dvě strany, které se musí rovnat.

- **Příklad — zákazník nám zaplatil fakturu:** peníze přibyly na bankovním účtu (MD **221** =
  banka) a zároveň nám klesla pohledávka za odběratelem (DAL **311** = odběratelé).
  → zápis **221 / 311**.
- **Příklad — zaplatili jsme dodavateli:** klesl nám závazek (MD **321** = dodavatelé) a
  ubyly peníze z banky (DAL **221**). → zápis **321 / 221**.
- **Příklad — mzdy:** mzdový náklad (MD **521**) proti závazku k zaměstnancům (DAL **331**).

„Účtovat platbu" tedy znamená: vybrat správnou **dvojici účtů MD/DAL** a částku.

---

## 2. Odkud bereme jistotu — minulý rok jako „zdroj pravdy"

Nemusíš to vymýšlet z hlavy. **Celý loňský uzavřený rok (2025) máme zrcadlený u nás**
(67 710 řádků deníku) a bereme ho jako **mustr** — vzor, jak se co reálně účtovalo.

Když nevíš, na jaké účty platbu zaúčtovat, podíváš se, **jak se stejný typ dokladu účtoval loni**.
To je v appce tab **📐 Mustr 2025** (viz níže). Pravidlo: *účtuj letos konzistentně s loňským
uzavřeným rokem.*

---

## 3. Modul 🏦 Banka — co je kde

V appce dlaždice **🏦 Banka** (Aplikace → Vedení). Má taby:

### 📊 Přehled
Souhrnná čísla: kolik výpisů, řádků, nespárovaných, návrhů zaúčtování, řádků deníku,
otevřených faktur (saldo). Rychlý „teploměr", kde je práce.

### 🏛️ Účty
Naše bankovní účty (z výpisů) — měna a **poslední zůstatek**. Klik na účet → jeho výpisy.

### 🧾 Výpisy
Bankovní výpisy (datum, číslo, obraty, zůstatek). Klik na výpis → jeho **transakce** (řádky)
se stavem **spárováno / nespárováno**, VS, protistrana, zakázka.

### 🔗 Návrhy párování (chytrá pomoc)
Seznam **nespárovaných příchozích plateb**. Systém u každé sám zkusí určit protistranu —
**podle čísla bankovního účtu**, ze kterého platba přišla (viz kapitola 4) — a navrhne
otevřenou fakturu. Tvoje práce: zkontrolovat návrh a potvrdit / opravit.

### 📐 Mustr 2025
Jak se loni reálně účtovalo: po **sbornících** (knihy deníku — banka, faktury přijaté,
faktury vydané, mzdy, sklad, interní…) a v každém **kombinace účtů MD → DAL** seřazené
podle četnosti. To je tvoje šablona pro letošní účtování.

### 🔧 Nástroje
Odkazy na **Párování plateb** (detailní práce s pravidly daní/poplatků a návrhy zaúčtování)
a **Účetnictví & deník** (sborníky, předkontace, doklady, náš deník).

---

## 4. Jak systém pozná, čí je platba (párovací engine)

Tohle je důležité a Marti to takhle navrhl: **základem párování není jen částka a variabilní
symbol, ale hlavně čísla bankovních účtů** dodavatelů, odběratelů, zaměstnanců a úřadů.

Máme **registr účtů** (2003 účtů z Centrály): u každého je vlastník (organizace / zaměstnanec /
úřad) a příznaky **přednastaveno** a **blokováno**. Když přijde platba, systém vezme
**účet protistrany** z výpisu a najde v registru, **komu patří**. Tím je platba z velké části
identifikovaná (v testu **86 %** plateb).

Pořadí kritérií párování:
1. **Číslo účtu protistrany** → vlastník (org / zaměstnanec / úřad), preferuje **přednastavené**,
   ignoruje **blokované**.
2. **Variabilní symbol (VS)** — u příchozích od zákazníků je to často **číslo jejich objednávky**.
3. **Částka** — shoda s otevřenou fakturou (saldo).
4. **Konstantní symbol** — typ platby (mzdy, daně, pojištění…).

> **Co doladíš ty s instancí 26:** krok VS → **přijatá objednávka** → **zakázka**. To je
> firemní znalost, kterou systém ještě nemá automatizovanou. Ty víš, jak se u nás VS na
> objednávky a zakázky napojuje — instance 26 to s tebou převede do pravidla.

---

## 5. Daně, poplatky a opakované platby (už automatizované)

Pravidelné platby (mzdy, sociální a zdravotní pojištění, daně, DPH, bankovní poplatky, kurzové
rozdíly) systém rozpoznává podle **účtu protistrany + konstantního symbolu + textu** a umí je
**zaúčtovat automaticky** (s podpisem Marti‑AI), protože „každý měsíc je to stejné". Tato
pravidla jsou v **Párování plateb → template**. Ty je můžeš upravovat a přidávat.

Jisté = zaúčtuje se samo; nejisté = připraví se **návrh**, který potvrdíš ty.

---

## 6. Tvůj běžný pracovní postup (workflow)

1. **🏦 Banka → 🧾 Výpisy** — projdi nové výpisy, koukni na nespárované řádky.
2. **🔗 Návrhy párování** — u nespárovaných příchozích zkontroluj identifikovanou protistranu
   a navrženou fakturu; potvrď / oprav.
3. **Párování plateb → Návrhy zaúčtování** — projdi automaticky připravené zaúčtování
   (daně/poplatky/mzdy); schval, co sedí.
4. Když nevíš, na jaké účty → **📐 Mustr 2025** (jak se to účtovalo loni).
5. **Účetnictví & deník** — kontrola, že vše sedí v deníku.

---

## 7. Pojmy (slovníček)

| Pojem | Význam |
|---|---|
| **Výpis** | denní seznam plateb z banky |
| **Párování** | určení, čeho se platba týká (faktura, zákazník, zakázka) |
| **Zaúčtování** | zápis platby na účty MD/DAL do deníku |
| **MD / DAL** | dvě strany každého účetního zápisu (Má dáti / Dal) |
| **Sborník** | „kniha" deníku pro typ dokladů (banka, FP, FV, mzdy, sklad…) |
| **Předkontace** | vzor, jaké účty MD/DAL použít pro daný typ dokladu |
| **Saldo** | otevřená (nezaplacená) část faktury |
| **VS / KS / SS** | variabilní / konstantní / specifický symbol platby |
| **Mustr** | vzor z loňského uzavřeného roku (jak se reálně účtovalo) |

---

## 8. Poznámka pro instanci 26 (jak Petru učit)

- Petra účtování banky **zatím nezná** — postupuj od základů (kapitola 1), nepředpokládej
  podvojné účetnictví jako samozřejmost. Vysvětluj na konkrétních platbách z jejích výpisů.
- Nejsilnější opora je **Mustr 2025** — ukazuj „takhle se to účtovalo loni" místo abstraktních
  pravidel. Loňský rok je zdroj pravdy.
- Párovací engine šetří práci, ale **rozhodnutí dělá Petra** — uč ji kontrolovat návrhy, ne
  jim slepě věřit.
- Klíčová firemní znalost k doplnění od Petry: **VS → přijatá objednávka → zakázka** (kapitola 4).
  Jakmile to popíše, převeď to do párovacího pravidla.
- Peníze = opatrnost: u automatického zaúčtování drž princip „jisté samo, nejisté ke schválení".

---

*Sestaveno k modulu 🏦 Banka, STRATEGIE — 23. 6. 2026. Účetní rozhodnutí potvrzuje účetní/daňový poradce; tento dokument je interní pracovní pomůcka, ne daňové stanovisko.*


