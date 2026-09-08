# Pauza vlozena doprostred prace rozdeli pracovni zaznam (Ano / Ne / Storno) - Peta 8.9.2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Pauza doprostred prace rozdeli pracovni zaznam

**Zadala Peta 8.9.2026.** Clovek hlasi u dlouheho pracovniho zaznamu *"chybi prestavka
/ obed 60 min"* (napr. Pavel Zeman 3.9.2026, Prace 07.33 az 16.56, 9,38 h). Editor
dosud musel praci rucne zkratit, pridat pauzu a zalozit druhou cast - tri kroky,
v kazdem se da splest nebo na nej zapomenout.

## Jak se to chova

V **Pridat zaznam** staci zadat pauzu s casy, ktere padnou **dovnitr** pracovniho
zaznamu. Server pak misto ulozeni vrati otazku a UI ukaze tri tlacitka.

| Volba | Co se stane |
|---|---|
| **Ano, rozdel a vloz** | V JEDNE transakci se vlozi pauza a hostitelska prace se **rozdeli na dve casti** (do zacatku pauzy a od konce pauzy). Obe casti jsou nove radky se `source='manual_fix'`, puvodni se oznaci jako nahrazeny. Takze zezelenaji, maji audit i notifikaci cloveku. |
| **Ne, jen vloz pauzu** | Pauza se ulozi pres prekryv jako dosud (od 4.8.2026 to prekryv neblokuje) a prijde cervene varovani. |
| **Storno** | Neulozi se **vubec nic**. |

Rozpad na zakazky (`vyroba_work`) srovna po rozdeleni kanonicka kaskada
`att_sync_vyroba_work`, ktera se vola az po obou zapisech.

## Kdy se otazka NENABIDNE (a je to zamer)

- **jde o jiny typ nez pauza** - nabizi se jen u prestavky,
- pauza nelezi **cela uvnitr** jednoho zaznamu (dotyka se okraje = staci posun, na to je
  nabidka posunu navazujiciho zaznamu, viz [[doc-dochazka-oprava-nabidne-posun-navazujiciho-zaznamu]]),
- hostitelskych zaznamu je **vic nez jeden**, nebo do pauzy zasahuje jeste nekdo dalsi,
- hostitel je stornovany, ohlaseni, **z Centraly** (`source_system`), bezici (bez konce),
  nebo ma vyplnene `break_minutes` (pak by se rozdelenim ztratila odectena pauza).

## Kde to zije

- **Server**: `g2007.python` kod **`att_fix_add`** - `_att_deleni_hostitel` (najde hostitele),
  `_att_deleni_otazka` (text), `_att_deleni_proved` (rozdeleni). Endpoint bere dva nove
  parametry **`deleni`** (`ano` / `ne`) a **`deleni_umim`** (opt-in, posila ho jen UI,
  ktere se umi zeptat - stary klient jede po staru).
- **Delegat** v `modules/erp/api/router.py` (`/app/attendance/fix/add`) - commit `649f3338`, 8.9.2026.
- **UI**: `dochazka-opravy.html` (`fixAddPost`) a `mobile_parts/60_dochazka.js` (`_fixAddPost`);
  obe pouzivaji tentyz tributonkovy box jako nabidka posunu navazujiciho zaznamu,
  jen s jinymi popisky. **Dochazka new novou dochazku nezaklada** (jen Opravy a Sprava),
  takze tam nic potreba nebylo.
- Hlida **pojistka `pauza-doprostred-prace-rozdeli-zaznam`**.

## Proc rozdelit a ne nechat pauzu lezet uvnitr

Hodiny vyjdou stejne (pauza uvnitr prace se odecita, pauza v mezere mezi dvema pracemi
se do souctu nedostane), ale **rozdeleny den je citelny** - v prehledu je videt prace,
pauza, prace, misto dvou radku pres sebe. A rozpad na zakazky pak sedi bez rucniho
dorovnavani.

Souvisi: [[doc-dochazka-oprava-nabidne-posun-navazujiciho-zaznamu]] (posun souseda pri
oprave casu), `doc-dochazka-att-entry-vyroba-work-kaskada` (kaskada rozpadu).

