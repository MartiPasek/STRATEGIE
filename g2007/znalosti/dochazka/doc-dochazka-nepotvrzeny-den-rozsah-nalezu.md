# Nepotvrzený den: nález jen u dnů z appky a jen dokud jde potvrdit (14 dní) — jinak visel navždy (1.–2. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 1.–2. 9. 2026.** Dvě omezení, která nález „nepotvrzený den"
dřív neznal — a proto nálezy visely lidem navždy.

## Co si potvrzení dne vůbec může nárokovat

Den si potvrzuje **člověk sám v mobilní appce**. Systém neumí den potvrdit za někoho
jiného — `att_confirm_day` i `att_unconfirmed` berou zaměstnance **z přihlášení**, ne
z parametru, a v Opravách docházky žádná taková akce není. Ověřeno čtením zdrojů
2. 9. 2026. Z toho plynou dvě pravidla:

### 1. Nález vzniká jen u dne, který přišel z APPKY (1. 9. 2026)

Peťa: *„pokud se to tam někomu dostane jinak než z mobilu, není logické, aby to chtělo
potvrzení."* Kdo appku nemá, nemá jak. Nález proto vznikne, jen když má den aspoň jeden
přítomnostní záznam se `source='mobile_app'`. Úklid odbavil už založené — **31 nálezů**:
Vojtěch Purkar 19 (docházka z importu), brigádník Saxana 10 a Světlana Herejtová 2
(ruční zápis, Jirka).

### 2. Nález se odbaví sám, jakmile den vypadne z okna (2. 9. 2026)

Appka nabízí k potvrzení **jen 14 dní zpět**. Co je starší, člověk v mobilu už nevidí —
Peťa 2. 9.: *„v mobilu už oni žádnou možnost potvrzení nevidí."* Nález přitom visel dál
a neměl jak zaniknout. Nově se po vypadnutí z okna odbaví sám. K 2. 9. 2026 to je
**13 nálezů**: Kilberger 14. 8., Marešová 9. a 29. 7., Pillár, Bernardová, Beneš 2×,
Svoboda, Veverka, Nosek, Brudnová, Hájek, Jakešová.

## Proč to není obcházení kontroly

Potvrzení dne **nemá vliv na mzdy ani na uzávěrku** — ověřeno 31. 8. 2026, žádná mzdová
funkce ho nečte. Je to doklad, že člověk svůj den viděl a souhlasí s ním. Nález, který
nemá kdo uzavřít, není kontrola, jen šum ve frontě.

## Co tím NENÍ vyřešeno

**Vedoucí nemá jak den odklepnout za člověka, kterého zkontroloval.** Peťa 2. 9. to
chtěla u Honala, Pornera a Kilbergera po Dušanově kontrole — a nešlo to. Kdyby to mít
mělo, chce to nový parametr v `att_confirm_day` (potvrzuje editor za zaměstnance,
`confirmed_by_user_id` na to sloupec už má) plus akci v Opravách.

## Souvislosti

- `doc-dochazka-prazdny-den-doplnen-nalez-jednou-na-den` — sesterská past téhož druhu
- `doc-dochazka-priznak-bez-dochazky-v-podminkach` — kdo se nekontroluje vůbec

