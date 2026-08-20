# Vyhodnoceni zakazek: doplneni starsich hodin z Centraly (hotovo 5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Doplneni starsich hodin z Centraly do vyroba_work

**Hotovo a overeno 5. 8. 2026** (C28/Jirka). Zadal Jirka, schvalila Marti-AI (msg 12214).

## Proc (bezpecnostni vec s realnymi penezi)

`tenant.vyroba_work` zacina 1. 1. 2026. Zakazka, ktera zacala driv a jeste bezi, by se
u nas vyhodnotila z NEUPLNYCH hodin -> mensi odpracovano -> vetsi usetreny cas ->
**VYSSI PREMIE**. Formulace Jirky: *"data za cely zivot zakazky i z roku 2025 u zakazek,
ktere nejsou uzavrene a vyhodnocene, je potreba prenest, aby vyhodnoceni bylo spravne
na zaklade vsech udaju zakazky."*

## Co se prenaslo

| | |
|---|---|
| zakazek presahujicich 2025 -> 2026 | **44** |
| radku | **2 582** |
| hodin | **7 138,40** |
| nejstarsi prace | 27. 5. 2024 |
| duplicity | **0** |

Z toho 2 zakazky jsou v Centrale JESTE NEVYHODNOCENE (2 122,77 h) - ty to primo
potrebuji. Zbylych 42 uz vyhodnocenych se prenaslo take, aby slo siroce porovnat nas
vypocet proti Centrale (drive slo jen 113 zakazek pracovanych vyhradne v 2026).

**Rezie se ZAMERNE neprenasi** - neni to zakazka, ale sberny kos (479 749 h, 111 480
radku od roku 1900). Do vyhodnoceni zakazek nepatri.

## Nastroj

`g2007.python` kod **`vyroba_work_doplnit_starsi`** (min_pravo=admin), spousteni
`POST /app/erp_registry/run` s `args:[[zakazky], 'do_datum']`; treti argument `true`
= jen nahled. Tvar radku 1:1 se `sync_vyroba_work_ec` (`source_system='centrala1'`
+ `source_id` = EC ID), takze budouci beh syncu je UPDATUJE, nezduplikuje.

## Overena rizika (Marti-AI je chtela zkontrolovat PRED prenosem)

1. **Prepise je kaskada `att_sync_vyroba_work`?** NE. Vybira jen radky
   `source_system <> 'centrala1'`; radky z Centraly needituje, bere je jen jako
   existujici pokryti (komentar Peti v kodu, 31. 7. 2026).
2. **Zmeni se prehled Dochazka po zakazkach?** Bezny pohled NE - je omezeny na posledni
   2 mesice. Volba "Vse" ten limit rusi, tam se rok 2025 nove objevi (uplnejsi data).
3. **Sazba** - sloupec jeste neexistuje (krok 4). Prenesene radky MUSI byt v tom
   dopoctu take, jinak u nich vyjdou penize spatne.

## Drobnost

26 radku (os. c. 512, 60,48 h) nema `user_id` - clovek je v `att_employee`, ale bez
uctu ve STRATEGII. Na vypocet to nema vliv (vyhodnoceni paruje na `cislo_zam`), dotkne
se to jen obrazovek, ktere joinuji na uzivatele.

## Gotcha pri spousteni

Skript commituje po radku, takze 2 582 radku trva vic nez 45 s a **volani z prohlizece
timeoutne** - server ale bezi dal. Stav overuj ctenim z DB, ne odpovedi prohlizece.

