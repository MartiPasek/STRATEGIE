# Řídící centrum v mobilu i pro správce — HOTOVO 8. 9. 2026, náhled cizího chatu s Maminkou zůstal jen rodičům

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Řídící centrum i pro správce — HOTOVO 8. 9. 2026

**Rozhodla Kristýna Marešová (rodič, `users.id=11`) 8. 9. 2026 v 10 hodin 06 minut** —
souhlasem přímo v mobilu (`fw.mobile_command` 23998, tlačítko Povolit).
Požádal Jiří Honomichl, provedl a ověřil Claude-28.
Podmínku o chatu si vyžádala Marti-AI (msg 14965) a Jirka s ní souhlasil.

## Jak to je teď

Živá logika **`martinka_centrum`** (`g2007.python`, verze 3) rozlišuje tři úrovně:

| kdo | seznamy, AI týmy, fronty | náhled cizího chatu s Maminkou |
|---|---|---|
| vlastník (sám sebe) | ano | ano |
| **správce** (`users.is_admin`) | **ano (nově)** | **NE** |
| rodič (`is_marti_parent`) | ano | ano |

Do 8. 9. 2026 pustila dovnitř jen rodiče, ostatní dostali 403 „smis videt jen svuj tym".
Správci jsou tři — Marti (1), Kristýna (11), Jirka (20) — a první dva už rodiče jsou,
takže změna otevřela obrazovku **jedinému člověku, Jirkovi**.

## Co přesně se změnilo v kódu

- Po otevření spojení se dopočítá `_admin` z `public.users.is_admin` (jen když člověk
  není rodič) a zavede se `_vse = _parent or _admin`.
- Oba zámky (pohled `clovek` i pohled `domena`) se ptají na `_vse` místo `_parent`.
- **Náhled chatu je natvrdo za rodičovskou branou** — `chat = [...] if _parent else []`.
- Odpověď nese navíc `spravce` (dnes to nic v aplikaci nečte, je to pro čitelnost).

Dotaz na `is_admin` je schválně **bez pojmenovaného parametru** (skládá se přes `str(int(uid))`),
protože dvojtečka v textu by se přes SQL most vyložila jako parametr.

## Jak se to dělalo

Zdroj se přečetl jako base64, upravil se u sebe (otisk originálu se ověřil proti databázi
bajt na bajt), uložil se **nejdřív jako návrh** `martinka_centrum__navrh_20260908`
(`stav_zivota='navrzeno'`), teprve po kontrole otisku se překlopil do provozní verze
s pojistkou na otisk. Spouštěč `trg_python_archiv` zvedl verzi 2 → 3 a starou podobu
uložil do `g2007.python_historie`, takže návrat je odkud vzít.

## Ověřeno naostro

V mobilu na účtu Jiřího Honomichla (správce, **není rodič**) se detail člověka
otevřel — u Elišky je vidět „čeká (2)" i jejích pět Martinek, a blok
**„CHAT S MAMINKOU (posledních 0)" je prázdný**, jak měl být.

⚠️ **Kosmetický nedodělek k rozhodnutí:** v prázdném bloku chatu appka správci píše
„Konverzace Moje Martinky zatím nevznikla — objeví se s prvním budíčkem". To je
nepřesné, protože konverzace existovat může a jen se skrývá. Chtělo by to větu
„náhled chatu vidí jen rodič". Nahlášeno Jirkovi 8. 9. 2026.

