# Nepřítomnost OSVČ není docházka a NEPOČÍTÁ se do fondu (Peťa 4.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nepřítomnost OSVČ se do fondu NEPOČÍTÁ

> oblast: `dochazka` — **Peťa + Claude-26, 4. 8. 2026**, ověřeno na datech července 2026.
> Doplňuje `doc-dochazka-fpd-vypocet-kancelar-vs-dilna`.

Peťa — „nepřítomnost OSVČ není docházka, nemůže se počítat do fondu."

## Pravidlo

Typ **„Nepřítomnost OSVČ"** (činnost **37**) je **jen informace, že ten den nepracoval**.
NENÍ to absence typu dovolená / nemoc / lékař, kterou zaměstnavatel proplácí.

- **Do FPD ji NEZAPOČÍTÁVEJ** — ani když ji `tenant.att_den_hodiny` vrátí ve sloupci
  `hodiny_absence` (funkce ji tam dává spolu s ostatními absencemi, rozlišit se musí
  přes `att_entry_type.label`).
- U OSVČ tedy **FPD = skutečně odpracované hodiny** (+ absence jiného druhu, pokud jsou).
- Může stát **vedle reálné práce v tomtéž dni** — práci započítat, nepřítomnost ne.
- Když ji zaměstnanec chce přepsat prací, **nejde `fix/entry`** (nepřítomnost nemá časy,
  endpoint vrátí „Záznam bez času začátku (absence) — oprav přes absence, ne tady").
  Postup je **`fix/void` + `fix/add`**.

## Proč na tom záleží — rozdíl je velký

Za červenec 2026 mělo nepřítomnost OSVČ pět lidí a u čtyř se výsledek obrátil:

| dnů nepřítomnosti | FPD správně (bez ní) | kdyby se počítala |
|---|---|---|
| 4 dny / 32 h | −11,17 h pod fondem | +20,83 h nad fondem |
| 2 dny / 16 h | −12,84 h | +3,16 h |
| 2 dny / 16 h | −17,64 h | −1,64 h |
| 1 den / 8 h | −10,45 h | −2,45 h |

Jeden člověk se z „přesčas 20 hodin" propadl na „chybí 11 hodin" — tedy rozdíl 32 hodin
v mzdovém podkladu. Ostatní OSVČ nepřítomnost nemají, u nich se nemění nic.

## Souvislost

`doc-dochazka-fpd-vypocet-kancelar-vs-dilna` (jak se FPD počítá u kanceláře, dílny
a hodinových) · `doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie` (činnost 37).

