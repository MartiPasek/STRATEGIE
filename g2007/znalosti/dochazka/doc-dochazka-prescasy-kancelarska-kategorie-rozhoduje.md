# Prescasy a kancelarska kategorie - co rozhoduje o proplaceni a proc ERP a mobil davaji jine cislo

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Přesčasy kancelář — proč ERP a mobil dávají jiné číslo, co rozhoduje o proplacení (`dopichavat_fond`) a co na to nemá vliv (podmínka `pod_neplaceny_prescas_h_den`, sloupec `bez_prescasu`).**

# Přesčasy kancelář — co rozhoduje a proč ERP ≠ mobil

Analyzoval C-28, 1. 9. 2026 na podnět Šárky Novotné. **Žádná změna v provozu.**
Ověřeno na živých datech a v živém kódu (`g2007.python`, funkce v DB, obsah webu).

---

## 1. Proč ERP „Součet hodin" a mobil „Moje hodiny" dávají jiné číslo

Obě čísla jsou správně — odpovídají na jinou otázku.

- **ERP „Součet hodin"** (Opravy docházky, pravé tlačítko) = odpracované hodiny **včetně toho,
  co za člověka do fondu dopsal automat** (typ `fond_doplneni`, `source='automat'` — dny, kdy
  člověk nepíchl a systém mu den dorovnal do fondu). Je to `hodiny_mzdove` z `tenant.att_den_hodiny`.
- **Mobil „Moje hodiny"** = **jen skutečně odpracované hodiny**; automatem dopsané odečítá.
  Podmínka Peti Šafránkové — *ty hodiny nikdo neodpracoval*.

Rozdíl **není chyba, je záměrný**. Kdo je porovnává, musí vědět, že měří jinou věc.

**Doložený příklad (srpen 2026, jeden vedoucí):** ERP 115,04 h · mobil 112,6 h ·
rozdíl 2,48 h = dva zápisy automatu do fondu. Absence 57 h sedí v obou.

---

## 2. Přesčas se nepočítá ani z jednoho z těch dvou čísel

Častý omyl při dotazu *„počítat přesčas ze 115, nebo ze 112,6?"* — **ani z jednoho.**

Mzdy počítají z **FPD** (odpracovaný fond), a to dvěma vzorci podle kategorie
(zdroj `doc-mzdy-svatky-fond-stravenky-prescas`, „velká zeď" od Peti)

- **výroba** — FPD = `hodiny_mzdove` + `hodiny_absence`
- **kancelář** — FPD = `hodiny_mzdove` + `hodiny_absence` − `hodiny_nad_fond`

**Přesčas = FPD − měsíční fond** (pracovní dny z `tenant.firemni_kalendar` bez svátků).

---

## 3. O proplacení přesčasu rozhoduje VÝHRADNĚ docházková kategorie

Konkrétně příznak `tenant.att_kategorie.dopichavat_fond`.

`mzdy_loajalita_rows` v16 (active) si nejdřív načte množinu `skup24` = všichni uživatelé
s kategorií, kde `dopichavat_fond=true AND aktivni=true`, a pak v hlavní smyčce má

```
for cislo, (user_id, daily_h) in emp.items()
    if user_id in skup24
        continue
```

Vyloučení proběhne **ještě před výpočtem** — kdo je v takové kategorii, nedostane do složky 651 nic,
**bez ohledu na cokoli jiného.**

---

## 4. Co na proplacení přesčasu vliv NEMÁ

### podmínka `pod_neplaceny_prescas_h_den` (karta zaměstnance → Podmínky)
Výpočet přesčasů ji **vůbec nečte.** Čtou ji jen obrazovky podmínek (`hr_conditions`,
`hr_conditions_save`, `my_conditions`, `hr_podminky_prehled`, `podminky_skupin_dlazdice`)
a plánování. Ověřeno prohledáním celé `g2007.python`.

⚠ **Past pro personalistiku** — nastavení „neplacený přesčas 0" u člověka v kancelářské kategorii
vypadá jako *„přesčas se mu bude platit celý"*, ale ve skutečnosti **neudělá nic**.

### sloupec `tenant.att_kategorie.bez_prescasu`
**Nečte ho žádný výpočet.** Jediný výskyt v celém systému je popisek na obrazovce
`dochazka-automat.html` (text „(bez přesčasů)" ve výpisu kategorie).
Skutečný přepínač je `dopichavat_fond`. Ověřeno v `g2007.python`, v `g2007.soubor`,
ve funkcích databáze i v jádře.

---

## 5. Kategorie „Volná doba s přesčasy" existuje, ale je vypnutá

Číselník `tenant.att_kategorie` (stav 1. 9. 2026)

| kategorie | `dopichavat_fond` | přesčas se platí | lidí |
|---|---|---|---|
| Volná kancelářská doba (bez přesčasů) | ano | **ne** | 25 |
| Pevná pracovní doba | ne | ano | 33 |
| Volná doba s přesčasy | ano | ne | **0 — vypnutá** |
| Bez docházky (hlídat absenci) | ano | ne | 2 |
| Bez automatu (řeší se ručně) | ne | ano | 0 |

**Pozor na pojmenování** — „Volná doba s přesčasy" má `dopichavat_fond=true`, takže by
podle bodu 3 přesčas **stejně nevyplácela**. Kdyby ji chtěl někdo zapnout jako řešení pro
volnou pracovní dobu s placenými přesčasy, **musí se nejdřív ověřit mzdový výpočet** —
dnešní vyloučení jede podle `dopichavat_fond`, ne podle názvu.

---

## Shrnutí pro provoz

| Otázka | Odpověď |
|---|---|
| Proč se liší ERP a mobil? | Záměr — ERP počítá i hodiny dopsané automatem, mobil ne |
| Z čeho se počítá přesčas? | Z FPD (odpracováno + absence), ne z odpracovaných hodin |
| Dostane člověk přesčas proplacený? | Podle `att_kategorie.dopichavat_fond` — a jedině podle něj |
| Má `pod_neplaceny_prescas_h_den` vliv? | Ne — čtou ji jen obrazovky podmínek |
| Má `bez_prescasu` vliv? | Ne — je to jen popisek na obrazovce |

**Zařazení do kategorie je tedy personální rozhodnutí s přímým dopadem do mzdy**, ne technický detail.
Kdo mění kategorii, mění tím i to, jestli se člověku platí přesčasy.

_Souvisí:_ doc-mzdy-svatky-fond-stravenky-prescas, doc-dochazka-mobil-moje-hodiny-napojeno-1-9-2026

