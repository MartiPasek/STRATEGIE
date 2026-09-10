# Mzdy smí měnit jen mzdová účetní (Peťa + Michelle), rodiče ne

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


Peťa 9. 9. 2026: „aby nikdo kromě nás nemohl změnit výplaty ani rodiče" a
„aby nikomu nešli změnit / přegenerovat atd."

## Kdo smí
`_MZDY_UCETNI = (17, 18)` — Michelle Šafránková (17), Petra Šafránková (18).
Tatáž dvojice jako `_MZDY_ZAMEK_VYJIMKA`. **Rodičovský bypass tu NEPLATÍ** —
je to jediné místo v systému, kde rodič (`is_marti_parent`) neprojde. Vědomé
rozhodnutí Peti, mzdy jsou teritorium mzdových účetních.

## Jak to bylo do 9. 9. 2026
Branou bylo `_is_cockpit` = rodič NEBO scoped approver NEBO skupina Finance/HR.
Reálně **devět lidí**: Marti Pašek (1), Kristýna Marešová (11), Michelle (17),
Peťa (18), Šárka Novotná (13), Jiří Honomichl (20), Marta Šafaříková (108),
Petra Fajmonová (107), Tomáš Hrbek (109). Peťa o tom nevěděla.

## Dvě vrstvy — nepleť si je
1. **Schvalování zápisu přes most** — `_is_mzdy_write(sql)` v `router.py`
   pozná zápis do mzdových tabulek (PG `wage_*`/`mzdy_*`/`payslip_*`, Helios
   `TabZamMzd`/`TabMz*`/`TabZamVyp`/`TabPredzp`, procedury `hp_Mz*`,
   `EC_Mzdy*`). `claude_write_decision` (g2007.python) to kontroluje **před**
   routováním approvera → schválí jen uid 18, ani rodič.
2. **Tlačítka v aplikaci** — `_mzdy_smi(uid)` / `_mzdy_zakaz(co)` v `router.py`.
   Použité v: `mzdy_generuj` (g2007.python, vlastní whitelist v těle),
   `POST /app/mzdy/zamek`, `POST /app/ucto/mzdy-akce` (Path A, umí smazat
   `TabMzSloz`+`TabPredzp`).

## @@RUCNI je zavřená
Zkratka `@@RUCNI` v `/diag-sql` zapisovala do `tenant.mzdy_rucni_slozka` rovnou,
**bez schvalovacího banneru** — obcházela vrstvu 1. Od 9. 9. 2026 vrací chybu
s hotovým SQL. Ruční složka se zakládá běžným UPDATE/INSERT, který projde
bannerem.

## Hlídač změn
`tenant.mzdy_zmena_log` + spouště `trg_mzdy_zmena_*` (funkce
`tenant.mzdy_zmena_zapis()`) nad `wage_movement`, `wage_component`,
`mzdy_rucni_slozka`, `mzdy_zamek` — logují celý řádek před a po, kdo a kdy.
Denní job `mzdy_zmeny_hlidac` (g2007.python + `fw.mirror_job`) z logu pošle
Petě mail; sáhnutí na `mzdy_zamek` = alarm v předmětu. `payslip_sheet` /
`payslip_item` schválně mimo — přepisují se při každém generování.

## Co zavřené NENÍ (vědomě)
- `POST /app/pripl/workflow` — příplatky/srážky navrhují vedoucí, schvaluje
  držitel postu `wage_approver`. Zúžení by zabilo i návrhy.
- `POST /app/benefity/hr` — HO/OBL limity, dnes rodič nebo scoped approver
  (tedy i Šárka).
- Změny udělané přímo v Heliosu jeho vlastním klientem — tam naše brány nedosáhnou.

