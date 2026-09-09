# Nález „prázdný den doplněn" se zavíral sám, protože automat přepsal řádek pod ním (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026.** Peťa ráno: *„potřebuji zjistit, proč se to doplnil fond zelený, jako by už ověřený a odsouhlasený."*

Navazuje na `doc-dochazka-prazdny-den-doplnen-nalez-jednou-na-den` (1. 9. 2026) a doplňuje ho o druhou půlku téhož problému — ta se týká ZAVÍRÁNÍ nálezu, ne jeho zakládání.

## Co se dělo

Nález `prazdny_den_doplnen` u Zuzany Duspivové (den 3. 9. 2026) byl zavřený krátce po půlnoci 5. 9., bez `resolved_by` a bez záznamu v `att_anomaly_scan` historii oprav. V Opravách docházky proto svítil ZELENĚ jako „den je mezitím opravený", i když ten den nikdo neověřil a dopíchnutí do fondu 7 h v něm dál viselo.

Rozsah k 9. 9. 2026 — 80 nálezů tohoto pravidla zavřel automat, z toho 51 se nikdy nikdo nedotkl; otevřený nebyl ani jeden.

## Příčina

`att_automat_level_day` každou noc své doplňovací řádky maže a zakládá znovu s novým `id`. Nález na původním řádku (u Duspivové 10017410) tím ztratil, na čem visel — a OBECNÝ ÚKLID v `att_anomaly_scan` (zavedený 11. 8. 2026 kvůli hláškám po stornu) zavírá každý nález, jehož `entry_id` už neexistuje nebo je superseded. Vyhodnotil to jako „záznam neplatí, není co řešit".

Nový nález se nezaložil, protože od 1. 9. platí „jednou na člověka a den" — a ta pojistka je správná, jen bez téhle opravy zakonzervovala falešné zelené.

## Oprava (nasazeno 9. 9. 2026, `att_anomaly_scan`)

1. Obecný úklid pravidlo `prazdny_den_doplnen` **vynechává** (`AND a.rule <> 'prazdny_den_doplnen'`).
2. Vlastní úklid — nález se zavře, teprve když v tom dni **žádné aktivní doplnění do fondu není** (člověk si docházku doplnil).
3. Nález se **přesměruje na živý řádek**, když ho automat přepsal. Bez toho by ho fronta Oprav neukázala — `att_fix_queue` má `LEFT JOIN` na zaniklou entry a podmínka na `status` propadne do NULL.
4. Znovuotevření — co zavřel AUTOMAT (prázdný `resolved_by` a žádný `att_audit` s `action='resolve'`), se vrátí, dokud příčina trvá. Co odklikl člověk, zůstává zavřené. Stejný vzor jako u `chybi_zakazka` od 3. 9. 2026. Staré nálezy bez vyplněného dne se nevracejí, u nich už den nedohledáme.

## Data srovnaná ručně

- Petra Šafránková ml. 7. 8. 2026 — nález zavřen jako odbavený Peťou (`resolved_by = 18`), na její pokyn.
- Zuzana Duspivová 3. 9. 2026 — nález vrácen do fronty, `entry_id` narovnáno na aktuální řádek.

## Pojistka

`nalez-prazdny-den-zavira-jen-clovek` — hlídá, že žádný nález tohoto pravidla se dnem není zavřený automatem, když v tom dni pořád visí samotné dopíchnutí do fondu. Zapsána 9. 9. 2026; v ručním běhu `tenant.pojistky_check()` prošla, `posledni_beh` doplní denní automat.

## Poučení

Nález nesmí viset na `id`, které si jiný automat pravidelně přepisuje — a úklid „záznam už neplatí" nesmí platit pro pravidla, jejichž řádek se z principu obnovuje. Zelená patří jen tomu, co odbavil kontrolor.

