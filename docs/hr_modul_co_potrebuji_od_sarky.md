# HR modul — co od tebe potřebuji (postupně, po jedné položce)

> Princip: jdeme krok po kroku. Ty navedeš (název tabulky / cesta v Centrále /
> screenshot), já sáhnu do Centrály (DB_EC) read-only a namapuju do karty.
> Centrála zůstává zdrojem pravdy. Odškrtávám, jak postupujeme.

## Fáze 1 — sekce, které už mají data
- [ ] **1. Seznam lidí / karta zaměstnance** — kde je v Centrále karta zaměstnance
  (tabulka nebo cesta v menu) a čím se člověk identifikuje (osobní číslo?).
  → abych uměl vypsat lidi do modulu.
- [ ] **2. Základní údaje** — kde jsou osobní data (jméno, bydliště, kontakt,
  doklady, rodné číslo, pojišťovna, bankovní účet) a která pole reálně používáte.
- [ ] **3. Pracovní údaje** — smlouva, úvazek, mzda, datum nástupu, číslo poměru
  (tušim `EC_FinZamPodminky` + karta — potvrdíš / navedeš).
- [ ] **4. Lékařské prohlídky** — kde se evidují termíny a platnost.
- [ ] **5. Posty / pozice** — kde je zařazení (útvar/středisko/pozice) a nadřízený.
- [ ] **6. Dokumenty** — cestu mám (`\\192.168.30.11\Data\Zamestnanci`); potřebuju
  jen potvrdit, jak jsou pojmenované složky lidí (jméno vs. osobní číslo).

## Fáze 2–3 — až později
- [ ] **7. Benefity** — typy (stravenkový paušál, jazykové kurzy, HO, oblečení…)
  + jestli se evidují v Centrále, nebo je zavedeme nově.
- [ ] **8. Majetek** — kategorie + jestli je v Centrále evidence, nebo nová.
- [ ] **9. Školení / e-learning / směrnice / KPI** — až na ně dojde.

---
### Jak mě navedeš (kterékoli stačí)
- název tabulky v Centrále (klidně jen tušený),
- cesta v menu (Soudeček → přehled → pole),
- nebo screenshot obrazovky z Centrály.
