# NEMPRI25 (ošetřovné) — proč ČSSZ zamítá podání a jak se to hlídá

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# NEMPRI25 (ošetřovné, OSE) — proč ČSSZ zamítá podání a jak se to hlídá

**Oblast:** mzdy · **Zapsal:** Claude-24 (Kristý), 20. 7. 2026
**Kontext:** e-Podání NEMPRI25 = Příloha k žádosti o dávku nemocenského pojištění.
Generátor `modules/erp/api/mzdy_nempri.py`, dvě UI cesty na stránce `/davky`.

## Dvě cesty ke stejnému XML — a jen jedna byla kompletní

| Cesta | Zdroj dat | Stav do 20. 7. 2026 |
|---|---|---|
| **Přílohy z Heliosu** (`/app/davka/helios-generuj`) | `TabMzPrilohaDnp` + `TabMzPrilohaDNPRO` | kompletní, ověřeno u validátoru ČSSZ |
| **Ruční záchyt podání** (`/app/davka/generuj-xml`) | `tenant.davka_podani` | **vždy zamítnuto ČSSZ** |

Ruční záchyt vznikl pro případy, které ještě nejsou v Heliosu. Jenže
`_nempri25_ose_xml` v `router.py` posílal `"rozhodneObdobi": None` natvrdo a
uložené `cislo_uctu` vůbec nečetl. Kombinace = tři jisté chyby od ČSSZ:

- **kód 2** — *„Rozhodné období je povinná položka"* (chybí 12 měsíců příjmů)
- **kód 2** — *„Pro druh dávky OSE a akci vznik je položka platební spojení povinná"*
- **kód 311** — *„Neplatné RČ nebo RČ neodpovídá datu narození"*

Chyby 1 a 2 byly **systémové** — padlo by na nich každé podání z ručního záchytu,
ne jen jedno konkrétní.

## Jak je to vyřešené (commity `2d3e552d`, `7713f277`)

1. **Rozhodné období se dotahuje z Heliosu podle čísla rozhodnutí.**
   `mzdy_nempri.load_rozhodne_obdobi(cislo_rozhodnuti, firma, rc_zamestnance)`
   najde přílohu DNP (hledá v UCTO_EC i UCTO_ES — číslo rozhodnutí je napříč
   firmami unikátní) a vytáhne `TabMzPrilohaDNPRO`. Rozhodné období nikde jinde
   v našich datech není, ručně se do podání nezadává.
2. **Platební spojení** = `davka_podani.cislo_uctu` přes `_parse_ucet`
   (formát `[předčíslí-]účet/kód banky`); záloha = účet zaměstnance z Heliosu
   (`TabMzdaNaUcetView`).
3. **Předletová kontrola `zkontroluj_podani(p)`** běží před `build_nempri` na
   obou cestách. Když něco chybí, XML se **nevygeneruje** a UI ukáže seznam
   konkrétních problémů. Vadné podání se tak nedostane ani do datovky
   (ošetřeno i v `@@ISDS SENDNEMPRI`).

## ⚠️ Gotchy, které stály čas

- **RČ musí být dělitelné 11** (10místná, po r. 1954) a prvních 6 číslic musí
  být platné datum. `rc_problem()` vrací důvod, ne jen true/false — hláška
  „není dělitelné 11" je pro účetní použitelnější než kód 311 od ČSSZ.
  **Zástupné hodnoty typu `RRMMDD/0000` u dětí projdou naším formulářem, ale
  ČSSZ je odmítne.** Bez skutečného RČ ošetřované osoby podání nemá smysl posílat.
- **Párování podle čísla rozhodnutí NESTAČÍ.** Do ručního záchytu se číslo
  dostane překlepem nebo kopií z jiného podání — a pak se natáhne rozhodné
  období **cizího zaměstnance**, tedy jeho příjmy odejdou na ČSSZ pod jiným
  jménem. Proto `load_rozhodne_obdobi` porovnává i RČ zaměstnance z
  `TabCisZam` a při neshodě data odmítne (`nesouhlas_osoby`) a nahlásí, komu
  číslo patří. Reálně nastalo hned u prvního testovacího podání.
- **Struktura NEMPRI25 je na pořadí elementů citlivá** — skládá se v
  `build_nempri` v pevném pořadí; logická pravidla OSE (co se plní jen pro
  vznik / trvání / ukončení) jsou odladěná proti produkčnímu validátoru,
  needitovat od boku.
- **Ověřovat u ČSSZ jde zadarmo a bez podpisu** —
  `epodani_validace.validate_xml_string(xml, test=True)` proti
  `t-epodani.cssz.cz`. Levnější než zjišťovat chybu až z odmítnutého podání.
- **Rychlý test bez UI:** `@@NEMPRI <id podání>` přes most vrátí buď XML,
  nebo rovnou seznam problémů.

## Co z toho plyne pro provoz

Ruční záchyt **není** náhrada mzdové přílohy — je to předstupeň. Dokud mzdová
účetní přílohu DNP v Heliosu nepořídí, rozhodné období neexistuje a podání
nelze odeslat. UI to teď říká rovnou, včetně doporučení použít kartu
„Přílohy z Heliosu".


