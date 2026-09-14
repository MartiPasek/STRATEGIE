# Vyhodnocení: snížená efektivita se nerozděluje jako prémie, ale navyšuje kalkulaci

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Jak to doopravdy funguje

Když má někdo na zakázce efektivitu pod 100 %, jeho **neodpracované hodiny se přičtou
ke kalkulovaným hodinám zakázky**. Tím se zvětší ušetřený čas a prémiový balík pro
všechny ostatní. Sám z něj nedostane nic (`premie_osoba` má podmínku `efektivita = 100`),
takže jeho podíl fakticky připadne kolegům.

Není to tedy „fond, který se rozdělí", ale **navýšení základu, ze kterého se počítá**.

```sql
-- ec.vypocet_konstant
pridat_ef = sum(pocet_hodin - pocet_hodin * efektivita_osoba / 100.0)
kalk_hod_celkem_s_ef = kalk_hodiny_celkem + pridat_ef + (srazka_serie/100 * kalk_hodiny)
```

Příklad (VR10582, 11. 9. 2026): Hájek 40,40 h při 80 % → přičte se **8,08 h**.
Kalkulace 340 → 348,08, ušetřeno 63,30 → 71,38 h, prémiový balík o ~500 Kč větší.

## ⚠️ Past: musí se spustit „Nastav koeficienty", ne jen „Přepočet"

`efektivita_pridat_hodiny` plní **`ec.vypocet_konstant`** — tedy tlačítko
**2️⃣ Nastav koeficienty**. Tlačítko **3️⃣ Přepočet hodnocení** už jen čte hotovou
hlavičku a sám o sobě kalkulaci nezmění.

Kdo tedy sníží efektivitu a dá rovnou trojku, vidí, že dotyčnému prémie zmizela,
ale ostatním se nic nepřidalo — a vypadá to jako chyba výpočtu. **Správné pořadí je
snížit efektivitu → 2️⃣ → 3️⃣.**

Od 14. 9. 2026 na to v liště jádra upozorňuje oranžový štítek („Snížená efektivita —
spusť 2️⃣ a pak 3️⃣"). Nevisí na uložení efektivity, ale na stavu dat: svítí vždy, když
je v gridu někdo pod 100 % a hlavička má `efektivita_pridat_hodiny` nulu.

## Kde NENÍ, i když to tak vypadá

V `EC_Zakazky_PrepocetVyhodnoceni` jsou proměnné `@FondEfektivity` a
`@FondEfektivityCas` a pod nimi zakomentovaný `UPDATE` plnící `PremieOsobaEf`.
**Je to slepá ulička** — mrtvý kód bez podpisu i data, zatímco všechny ostatní změny
v té proceduře podepsané jsou. Navíc by ani po odkomentování nefungoval: fond se počítá
jako `SUM(PremieOsoba) WHERE EfektivitaOsoba < 100`, jenže těm lidem se `PremieOsoba`
pár řádků výš nastaví na nulu, takže by se sčítaly samé nuly.

`PremieOsobaEf` je proto v Centrále i u nás **vždy nula** a do vzorce finální prémie
vstupuje jen formálně.

⚠️ **Nepouštět se do „zapnutí fondu".** C24 na to 11. 9. 2026 navrhla implementaci
a bylo by to **dvojí započtení** — mechanismus přes kalkulaci už běží.

## Jak se na to přišlo

Kristý 14. 9. 2026 poslala záznam ze SQL Server Profileru. Z něj bylo vidět, že
Centrála volá `EC_Zakazky_PripravaVyhodnoceni`, a ta uvnitř spouští
`EC_Zakazky_Vyhodnoceni_vypocetKonstant` — proceduru, kterou předchozí hledání
(grep na „Fond", čtení `PrepocetVyhodnoceni`) minulo.

**Poučení:** když se hledá, kde se něco počítá, nestačí grep na název proměnné.
Trace ukáže, které procedury se opravdu zavolaly a v jakém pořadí.

## Sloučené skupiny — neověřeno

`efektivita_pridat` se přes skupinu bere jako `min(pridat_ef)`, ne jako součet
(převzato z Centrály 1:1). U samostatné zakázky je to jedno, u sloučené by se část
mohla ztratit. **Neověřeno, neměnit bez rozmyslu.**

