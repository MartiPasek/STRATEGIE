# Rozpad se páruje na uživatele, docházka na docházkový záznam — kdo má záznamy dva, tomu se hodiny zdvojí (a druhý záznam se NEMAŽE)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 2. 9. 2026.** Potřetí totéž, tak ať to má jméno.

## Vzorec

**Rozpad práce (`tenant.vyroba_work`) se vede na UŽIVATELE, docházka
(`tenant.att_entry`) na DOCHÁZKOVÝ ZÁZNAM (`att_employee`).** Kdo má záznamy dva —
a to je legitimní, jeden člověk může mít víc pracovních vztahů (pravidlo Martiho
9. 6. 2026) — tomu join přes `user_id` chytí oba a hodiny rozpadu se započítají
**dvakrát**.

Poznávací znamení: rozdíl je **přesně o 100 %**, ne o pár desetin.

## Kde už to kouslo

1. **9. 6. 2026** — skupiny zdvojily Marti Paška (join na `att_employee` kvůli jménu).
   Z toho vzniklo pravidlo „agreguj na `user_id`, nikdy přímý join".
2. **2. 9. 2026** — kontrolní přehled **Docházka × rozpad** hlásil Kristýně Marešové
   10 dnů srpna jako nesoulad (12 vs 24 h, 11,25 vs 22,5 h…). Má záznam č. 21
   (HPP, aktivní) a č. 27 (stará OSVČ historie, neaktivní). Ani jeden nález nebyl
   skutečný. Opraveno přidáním `AND em.is_active` do obou joinů přes `user_id`
   v `dochazka_kontrola_data` (report `rozpad`). Přehled FPD tuhle podmínku už měl.

## ⚠️ Co z toho NEPLYNE

**Není to důvod druhý docházkový záznam smazat.** Kristýnina OSVČ historie od roku 2021
je platná a smazáním by se ztratila. Peťa 2. 9.: *„pokud už to je a v srpnu na 27 nic
není, tak nic nepřehazujme."* Filtruje se to, co je **aktivní** — data se nechávají být.

## Než napíšeš další dotaz nad rozpadem

Když spojuješ `vyroba_work` s lidmi přes `user_id`, **vždy si přidej `em.is_active`**
(nebo agreguj na `user_id` a docházkový záznam neřeš). Jinak si vyrobíš fantoma.

