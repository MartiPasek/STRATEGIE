# Nárok na dovolenou a sick days — jediný zdroj pravdy jsou Podmínky (staff_cond)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ⚠️ **DOPLNĚNO 19. 8. 2026 (Claude-28, schválila Marti-AI). Obsah pod tímto rámečkem jsem needitoval.**
> Od 19. 8. 2026 večer **`tenant.staff_cond` už není tabulka, ale POHLED.** Osobní hodnoty podmínek
> fyzicky žijí ve smlouvě (`tenant.engagement`, sloupce `pod_*` + `pod_meta`) a verzují se s ní.
> Skupinové a systémové výchozí hodnoty zůstaly v `tenant.staff_cond_zaklad`.
> **Čtení i zápis přes `tenant.staff_cond` funguje dál úplně stejně** — ověřeno porovnáním otisků
> před a po (294 řádků i 1248 vyřešených hodnot bez rozdílu), takže **text níže platí dál**;
> změnilo se jen to, kde data fyzicky leží. Kdo bude sahat na strukturu nebo na spouštěče,
> ať si nejdřív přečte znalost **`doc-dochazka-podminky-slouceny-se-smlouvou`**.

---


# Nárok na D, DN a SD — jediný zdroj pravdy jsou Podmínky

**Rozhodl Jirka 13.–14. 8. 2026, schválila Marti-AI.** „Od teď se tyto věci již řešit nebudou v Centrále, ale jen ve STRATEGII." Zapsal Claude-28, 14. 8. 2026.

## Odkud se nárok bere

`tenant.staff_cond`, pravidlo **osobní → skupina → systém** (`_resolve_cond` / `_cond_group_of` v router.py).
Kódy: `dovolena_dni` (CELKOVÝ nárok ve dnech, včetně dovolené navíc) a `sick_days_rok` (ve dnech).

Od 14. 8. 2026 z tohoto zdroje čtou **všechna** místa:
- karta zaměstnance, sekce Podmínky
- přehled „Podmínky zaměstnanců" a stránka Finanční podmínky (endpoint `/app/hr/podminky-prehled`)
- přehled „Nárok a čerpání" (g2007.python `att_narok_cerpani`)
- mobilní appka při čerpání sick day a lékaře (g2007.python `sickday_lekar_apply`)

## Co bylo zrušeno a proč

**`tenant.holiday_balance` a `tenant.sick_day_balance` byly 14. 8. 2026 SMAZÁNY.** Nárok v nich nebyl spočítaný, ale plošně vyplněný — 74 lidí mělo shodných 200 h dovolené a 104 lidí shodných 16 h sick days bez ohledu na úvazek a nástup. Zálohy `tenant.zaloha_*_20260813` a `_20260814`, smazat cca 14. 9. 2026.
Zápisy odstraněny ze tří míst: `_abs_recalc_balances` (dochazka_absence_sprava.py, funkce zůstala jen kvůli hlášce uživateli), g2007.python `att_absence` a `sickday_lekar_apply`.

**Příznak uzavřeného roku** byl sloupcem v těch tabulkách. Nově `_abs_rok_uzavren(s, rok)` = je uzamčený mzdový **prosinec** toho roku (`tenant.att_period_lock`). Připraveno i pro převod zbytku dovolené (`tenant.dovolena_prevod`).

## Rozpad D / DN v přehledu Nárok a čerpání

Podmínky drží celkový nárok jedním číslem, přehled potřebuje rozpad. Dělí se stejným pravidlem jako v Centrále: **OSVČ má vše v dovolené navíc, ostatní mají standardní dovolenou do 20 dnů a zbytek jako navíc.** Ověřeno 14. 8. 2026 porovnáním starého a nového výpočtu u všech aktivních lidí — u 74 ze 79 vychází číselně totožně včetně rozpadu. **Jirka chce samotný rozpad D/DN ještě probrat — otevřená věc.**

## Past, na kterou se přišlo

`tenant.engagement_entitlement` (kódy `dovolena_standard`, `dovolena_navic`, `dovolena_vernost_10let`, `sick_days_*`) **už není zdrojem pravdy**. Připočítával věrnostní den PODRUHÉ — pět lidí (Havlát, Honomichl, Veverka, Honal, Kilberger) tam mělo o den víc, než říká Centrála i karta. Do 14. 8. z něj četl přehled Nárok a čerpání i mobilní sick days. Sync z Centrály do něj od 13. 8. nezapisuje.

