# Dochazka: vyklad Marti Paska "cist Dochazka new pres att_entry_id" = STORNO/OPRAVA, ne display dedup (27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod 2 z emailu Marti Paska: "prehledy (Dochazka new) cist pres tuto vazbu (att_entry_id), ne pres shodu casu; oprava i storno se propisou napevno po id."

## VYKLAD (potvrdila Marti-AI msg 11313, po dry-runu)
Marti Pask myslel STORNO/OPRAVU propagovanou pres att_entry_id, NE prepsani zobrazovaci (display) logiky. "Cist pres att_entry_id" bylo zduvodneni mechanismu storna/opravy.

## STAV = SPLNENO
- Storno/oprava pres att_entry_id: HOTOVO (att_fix_void hybrid cascade, drivejsi session).
- att_entry_id naplneno 95,5%.
- Display dedup v datasetu dochazka.zakazky_vse_list (cast P att_entry pritomnost) ZUSTAVA na urovni DNE (NOT EXISTS vyroba_work user+datum) - SPRAVNE, NEMENIT.

## GOTCHA (proc display dedup NEMENIT na link-based) - overeno dry-runem 27.7:
Naivni prepnuti "zobraz att_entry pritomnost pokud k ni nevede vyroba_work.att_entry_id" by PRIDALO 6705 radku pritomnosti (dnes skryte, protoze user MA vyroba_work ten den, ale ta pritomnost neni individualne linkovana - vetsina app radku ma att_entry_id prazdne). => DVOJI POCET hodin v mzdovem prehledu (napr. Blaha 24.7: pritomnost 8.02h NAVIC k rozpadu 5.24h). Day-guard dedup tam je SCHVALNE aby se nezdvojovalo. Souvisi [[doc-dochazka-doch-mobil-vs-erp-sjednoceni-att-entry]].

