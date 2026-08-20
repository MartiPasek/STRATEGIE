# Faze E davka POST2: 10 dalsich POST HTTP endpointu vyroby migrovano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovano 10 dalsich POST/zapisovych HTTP endpointu domeny vyroba na DB-driven delegaty (Cesta B), navazujici na prvni POST pilot (app_vyroba_todo_create): app_vyroba_plan_overlay, app_vyroba_prirazeni_create (VYJIMKA - samostatne 401 pak zvlast 403), app_vyroba_prirazeni_zrusit, app_vyroba_prirazeni_poradi, app_vyroba_zprava (jen 401), app_vyroba_odvoz_pozn_create, app_vyroba_odpoved, app_vyroba_zprava_resolve, app_vyroba_finish (jen 401), app_vyroba_todo_done.

Pri sestavovani (v predchozi kontejnerove session) vznikla chyba v app_vyroba_finish - leftover radek odkazujici na nedefinovanou promennou 'body' uvnitr run() (NameError riziko). Zachyceno a opraveno PRED nasazenim wrapperu (skript uz byl v DB jako active, ale zadny provoz na nej jeste nemohl narazit, protoze router.py jeste volal puvodni kod). Pouceni: pri navazovani na drivejsi/preterhnutou session vzdy znovu zkontrolovat build-skripty na obecne nazvy jako 'body', ne jen JSONResponse/req.query_params.

Deploy commit 58bdadd5e, 53 insertions/247 deletions. CELKEM AKTIVNICH FUNKCI: 103. router.py: 63729 radku (z puvodnich 67789 = 5.99% zmenseni od zacatku cele migrace).

