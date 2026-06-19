# SW zakázky — divize automatizace a robotiky (PLC) — digitalizační základ

**Pro:** Zuzka (asistentka divize automatizace) + Mirek + Claude‑27. **Datum:** 19. 6. 2026.
**Stav:** návrh základu od Claude‑23 (Marti's „základní stavění"). Zuzka = doménový vlastník,
upřesní pole; Claude‑27 staví se Zuzkou inkrementálně.

## Jak to vedete dnes (z `SW_zakazky_detaily_VELKE_2026.xlsx` + `TESLA přehled.xlsx`)
1. **Matice řešitel × týden (CW)** — řádek = SW vývojář (Lehký, Brož, Terla, Benetka…),
   sloupce = kalendářní týdny/měsíce, v buňkách běh zakázky přes milníky:
   **POP** (poptávka) → **NA** (nabídka) → **POBJ** (přijatá objednávka) → **OBJ.SW**
   (objednávka SW) → **FA/Obj.2** (faktura) → **Náklady SW**. List `CW2026` = číselník týdnů.
2. **Přehled po zakázkách (zákazník, např. Tesla)** — per SW zakázka (SW8036…SW8045):
   zákazníkova **PO**, **objednáno hodin** / **zbývá hodin**, **celková suma**, **dílčí
   faktury 1–3** (hodiny + číslo FA + suma), **zaplaceno** / **zbývá zaplatit**, **hodinovka
   tesla** vs **hodinovka sw**. List `VR` = obdobně pro VR zakázky.

Zákazníci: Tesla, BMW (Dingolfing), Intesoft… Zakázky číslované `SW80xx`.

## Navržený základ (datový model — „additivně, ne perfektně")
- **`tenant.sw_zakazka`** — jedna SW zakázka:
  `cislo_sw` (SW8041), `zakaznik`, `zakaznik_po` (5101270890), `resitel_user_id` (vývojář),
  `nazev`, `objednano_hodin`, `hodinovka_zakaznik`, `hodinovka_sw`, `celkova_suma`,
  `stav` (poptávka|nabídka|objednávka|realizace|fakturováno|zaplaceno), `ec_zakazka_ref`
  (vazba na zakázku v Centrále, je‑li), `rok`, `poznamka`.
- **`tenant.sw_faktura`** — dílčí faktury k zakázce (1:N):
  `zakazka_id`, `poradi`, `hodiny`, `cislo_faktury`, `suma`, `zaplaceno_at`.
  → odvozené: odpracováno = Σ hodin faktur, **zbývá hodin** = objednáno − odpracováno,
  **zbývá zaplatit** = celková suma − Σ zaplacených faktur.
- (Fáze 2) **`tenant.sw_prirazeni`** — kapacita řešitel × týden (ta matice): `user_id`,
  `cw` (týden), `zakazka_id`, `stav_milnik`. Pro plánovací pohled „kdo na čem v jakém týdnu".

## První obrazovky (co Claude‑27 postaví se Zuzkou)
1. **Přehled „SW zakázky"** — seznam (číslo, zákazník, řešitel, objednáno h, zbývá h, suma,
   zaplaceno, zbývá zaplatit, stav) + filtry zákazník / řešitel / stav. Detail zakázky =
   karta + dílčí faktury. (= digitální `TESLA přehled`, ale pro všechny zákazníky.)
2. **Plánovací matice řešitel × týden** (Fáze 2) — vizuál jako dnešní Excel, ale živý.

## Na co se napojíme (nestavíme nadvakrát)
- **Vývojáři = uživatelé** STRATEGIE (už je máme). Řešitel = `user_id`.
- **SW80xx zakázky** možná existují v Centrále (`TabZakazka`) — Claude‑27 ověří a propojí
  (`ec_zakazka_ref`), ať se nepřepisují ručně data, co už jinde jsou.
- Fakturace navazuje na logiku, kterou už známe z přefakturace (čísla FA, sumy).

## Otázky na Zuzku (než Claude‑27 založí tabulky)
1. Sedí ti milníky stav (poptávka→nabídka→objednávka→realizace→fakturováno→zaplaceno),
   nebo to vedete jinak?
2. Je `SW8041` to samé číslo jako zakázka v Centrále, nebo vlastní číslování divize?
3. Co tě v Excelu nejvíc zdržuje / kde se nejčastěji dělá chyba? (Tam začneme.)
4. Chceš nejdřív **přehled po zakázkách** (Tesla styl), nebo **matici řešitel × týden**?

---

## Jak pracovat s Claude‑27 (pro Zuzku a Mirka — lidsky)
1. Na notebooku otevři **Cowork** nad složkou `C:\Projekty\STRATEGIE`. První věta Claudovi‑27:
   **„Načti si CLAUDE.md a docs/sw_zakazky_automatizace.md."** Tím ví všechno potřebné.
2. **Mluv normální řečí** — co děláte, co chcete vidět, co vás štve. Nepotřebuješ umět
   programovat ani SQL.
3. Claude‑27 **sám čte data** (přes most). Když má něco **změnit nebo nasadit**, připraví to
   a **pošle ke schválení** — banner odklikne Marti nebo Kristý. **Ty nemůžeš nic rozbít** —
   navrhuješ, oni schvalují. Klidně zkoušej.
4. Postupujte **po malých krocích** (jedna obrazovka, jeden přehled), ať to hned vidíš a
   řekneš „tohle ano / tohle jinak". Velký Excel rozkrájíme na kousky.
5. Když si nevíš rady, napiš Martimu (instance 23) — propojíme se.

> Vize Marti + základ Claude‑23 + doménová znalost Zuzky a Mirka = vaše oddělení digitálně.
> Krok první: Zuzka projde 4 otázky výše s Claudem‑27, ten založí `sw_zakazka` + `sw_faktura`
> a postaví první přehled „SW zakázky". Pak přidáme matici řešitel × týden.
