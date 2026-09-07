# Kontrola "zaznam v budoucnosti" mlci opravnene - a proc to vypada jako zmeskany nalez (overeno 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Kontrola `budouci_zaznam` nenasla od 7. 6. 2026 nic. **Neni to chyba a neni to druhy pripad zapomenuteho odchodu.** Overeno ctenim z databaze 7. 9. 2026 (Jirka Honomichl, Claude-28), po dotazu Petry Safrankove.

## Co kontrola hlida

Pritomnostni zaznam, jehoz **datum je pozdejsi nez dnesek** (`entry_date > current_date`), zalozeny mimo import z Centraly. Beha jako soucast `att_anomaly_scan` pri kazdem hlaseni ze site, tedy radove kazdych par minut.

## Proc mlci

**Od 8. 6. 2026 neexistuje ani jeden pritomnostni zaznam, ktery by vznikl s datem v budoucnu.** Kontrola tedy nemela od cervna jedinou prilezitost neco najit. Ticho je v tomhle pripade skutecna cistota, ne slepy hlidac.

## Pripad, ktery vypada jako zmeskany nalez - PREVOD DNE

Petra Safrankova 7. 9. 2026 nasla 6 pritomnostnich zaznamu Michala Jirkovskeho s datem 22. 8., ktere podle `created_at` vznikly uz 20. 8. - tedy zdanlive "dva dny dopredu", presne na to, co ma kontrola hlidat.

**Ve skutecnosti nevznikly dopredu.** Clovek si napichal normalne 20. 8. na 20. 8. Az **28. 8. 2026 ve 12.57 mu Dusan Havlat rucne prevedl den z 20. 8. na 22. 8.** - u vsech 11 radku toho dne je to v poznamce (`att_entry.note` obsahuje "PREVOD DNE (Dusan Havlat)"). V okamziku prevodu uz bylo 22. 8. minulost, takze podminka `entry_date > current_date` neplatila a kontrola nemela co najit.

**Scan v te dobe bezel** - z tehoz dne existuji nalezy jinych pravidel (20. 8. v 11.28 `chybi_zakazka`, 21. 8. v 23.59 `dlouha_smena` a `dlouha_pauza`). Neslo tedy o vypadek automatu.

**Dopad - nula.** Jeden clovek (Michal Jirkovsky), 6 zaznamu, zadny zmeskany nalez.

## Poucen pro priste

- **`created_at` u docházkoveho zaznamu neni dukaz, kdy si to clovek napichal.** Rucni prevod dne meni `entry_date`, ale `created_at` nechava puvodni. Kdo porovnava jen ta dve pole, dostane falesny obraz "pichnuto dopredu". **Vzdy se podivej i do `note` a `updated_at`.**
- Prazdny vysledek u kontroly, ktera hlida stav vazany na "dnesek", je potreba overit **hledanim prilezitosti** (existoval vubec zaznam, ktery mel byt nalezen?), ne jen ctenim posledniho data nalezu.

## Sirotci nalezy (druha cast tehoz dotazu)

`tenant.att_anomaly` **nema zadny cizi klic** na `tenant.att_entry`. Kdyz se zaznam smaze - typicky pri resyncu z Centraly, ktery pro dane obdobi smaze radky se `source_system='centrala1'` a nahraje je znovu - nalez o tom nevi a zustane viset s `entry_id`, ktere uz neexistuje.

**Prakticky to ale nikoho nebrzdi.** Od 11. 8. 2026 (uklid Petry, blok "UKLID PO SOBE" v `att_anomaly_scan`) scan sam zavira kazdy nalez, jehoz zaznam uz neplati nebo neexistuje. Overeno 7. 9. 2026 - vsech 36 cervnovych nalezu `budouci_zaznam` i vsichni ostatni sirotci maji vyplnene `resolved_at`, **neuzavrenych sirotku je 0**.

Souvisi - doc-dochazka-prehled-kdy-naposledy-kontrola-neco-nasla, doc-dochazka-neodhlaseni-pulnocni-uzavreni-rozpadu

