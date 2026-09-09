# Rozdělení lidí: kontrola docházky × schvalování volna — shrnutí

> Peťa 22. 7. 2026. Přehled toho, jak to je dnes a jak to má být. **Nic nenasazeno.**

## Zásadní zjištění: dnes to běží na DVOU různých dělení

Kontrola docházky a schvalování volna dnes **nesdílejí stejné skupiny** — každá
agenda má vlastní, a ani jedna nesedí na personální skupiny. To je přesně to
roztříštění, které řeší návrh stromu.

### Kontrola docházky — dnes (`tenant.att_fix_scope`)

Kdo koho vidí a smí opravit. Členství se počítá z **org podstromu pod Dušanem**
(natvrdo v kódu) — proto vypadává Duspivová.

| působnost | kdo | koho řeší |
|---|---|---|
| kancelář | **Peťa** | všichni mimo Dušanův podstrom |
| výroba | **Dušan + Michaela** | Dušanův org podstrom |
| vše | **Jiří Honomichl** | vidí na všechny (dohled, chyby se mu nenotifikují) |

### Schvalování volna — dnes (`tenant.att_approver_group`, Jirka 21. 7.)

Úplně jiné skupiny — čtyři, definované přes **org posty**:

| skupina | schvaluje | zástup |
|---|---|---|
| výroba | **Dušan Havlát** | Marek Honal |
| nákupčí | **Peťa Šafránková** | — |
| projekty | **Jiří Veverka** | — |
| ostatní (fallback) | **Šárka Novotná** | — |

→ Dvě agendy, dvě různá dělení, žádné nesedí na `staff_group`. Sjednotíme.

## Jak to má být — jeden strom, u každé skupiny obě agendy zvlášť

Jako Centrála (přehled 7626): u každé skupiny **samostatný odpovědný pro docházku
a samostatný pro volno**. Můžou, ale nemusí, být stejní lidé.

```
KANCELÁŘE        Vedení · Nákup · Finance · Obchod · HR · IT
VÝROBA           Výroba · Zkušebna · PLC · VP · E-plan
```

### Kontrola docházky — DOHODNUTO ✅

| skupina | kontrola docházky |
|---|---|
| KANCELÁŘE | **Peťa + Michelle** |
| └ IT | **Kristýna** (výjimka) |
| VÝROBA | **Dušan + Michaela** |
| fallback | **Peťa** |
| osobní výjimka | Marti → **Peťa** |
| dohled nad celkem | **Jiří Honomichl** (ponechané „vše") |

### Schvalování volna — DOHODNUTO ✅ (Peťa 22. 7.)

| skupina | schvaluje volno |
|---|---|
| KANCELÁŘE (Vedení, Nákup, Finance, Obchod, HR) | **Peťa** — všem kancelářským |
| └ IT | **Kristýna** (výjimka) |
| VÝROBA | **Dušan** (zástup Marek Honal, jako dnes) |
| └ VP (Vedoucí projektů) | **Jiří Veverka** (výjimka pod výrobou) |
| fallback | **Peťa** (předěleguje) |
| osobní výjimka | Marti → **Marti sám** (schvaluje si volno sám) |

Rozdíl proti kontrole docházky u Martiho: **docházku** mu řeší Peťa, ale **volno si
schvaluje sám**.

## Fallback = Peťa (obě agendy)

Peťa 22. 7.: *„fallback pošli mě, já předeleguju — platí pro oboje."* Kdo propadne
mimo skupinu i výjimku, přijde Peťě a ona přiřadí dál. Platí pro docházku i volno.

## Klíčový princip (platí pro obě agendy)

Odpovědnost **dědí** shora: u skupiny bez vlastního nastavení se jde na kořen, pak
fallback. U konkrétního člověka jde odpovědného **ručně přepsat** (osobní výjimka).
Jeden mechanismus, jen sloupec `agenda` rozlišuje docházku od volna.

## Toto je VÝCHOZÍ tabulka pro všechny — i pro personalistku

Peťa 22. 7.: *„to celé má být výchozí tabulka pro všechny, i pro personalistku."*
Tzn. `att_odpovednost` je **jediný zdroj pravdy** o tom, kdo za koho zodpovídá —
nejen pro docházku a volno, ale i pro personální agendu. Ne aby si každý modul
držel vlastní seznam. Proto se to **zapisuje do G2007** jako závazný model
(oblast `dochazka`, viz `Z_dochazka_odpovednost_model.md`).
