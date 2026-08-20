# TODO (VECER 3.8.2026, spolecne okno s rederivaci mobile.html): 2 male zasahy do kodu pro orchestraci Martinek

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Oba vyzaduji git deploy (~5s restart API) - proto vecer, mimo produkci, spolu s rederivaci fragmentu mobile.html (viz doc-system-strategie-todo-mobile-fragmenty-rederivace-vecer).

## 1. uid volajiciho do /app/erp_registry/run (router.py)
Endpoint zna uid (auth), ale NEpredava ho skriptum - UI posila args=[null,...] a ukoly Martinek maji zadal_user_id=NULL. Reseni: placeholder konvence - v erp_registry_run_ep pred call nahradit v args kazdy vyskyt stringu "__uid__" skutecnym uid volajiciho (zpetne kompatibilni, zadna zmena existujicich volani). Pak v UI martinky.html zamenit prvni arg null -> "__uid__" u vsech run() volani. Dopad: zadal/schvalil/od_koho v ukolech Martinek budou realni lide.

## 2. Periodicky sweeper automat martinky_sweeper (automat_domeny.py)
Dnes je sweep zaseknutych 'bezi' behu + jistic pokusu jen OPORTUNISTICKY (spousti se pri martinka_prehled z UI a pri martinka_dispatch) - kdyz nikdo neotevre UI a nic se nedeje, zaseknuty ukol lezi. Reseni: novy DOMAIN_CHECK v modules/erp/api/automat_domeny.py (vzor _check_poptavky_status): kod='martinky_sweeper', interval ~10 min, telo = erp_registry.call('martinka_dispatch', None, None) (sweep + jistic + rozjeti fronty je uz v dispatch v5) + zapis status_block ("Ukoly: X ve fronte, Y bezi, Z ceka na cloveka...") do g2007.automat - cimz vznikne i status blok domeny martinky pro composer (pozdejsi pozadavek Marti-AI). + INSERT radek do g2007.automat (kod, interval_min=10, eskalace_agent='haiku', domain_kod=NULL nebo novy 'martinky').

Zapsal C23 3.8.2026 rano po dohode s Martim (produkce nesmi byt rusena pres den).

