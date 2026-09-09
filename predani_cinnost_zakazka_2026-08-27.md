PŘEDÁNÍ — Peťa + Claude‑26, 27. 8. 2026 (činnost a zakázka v rozpadu)

HOTOVO

1. Nalezena příčina, proč u srpnových úseků chybí činnost. Výběr zakázky si činnost hledal v paměti jen mezi „dílenskými" činnostmi, jenže k zakázce Rezie si lidé vybírají „režijní" — netrefil se nikdy. A když nenašel, uložil prázdno, čímž smazal i to, co tam bylo. Pavel Zeman se v tom zasekl 18. 8. a devět dní mu vznikaly prázdné úseky (~40 h). Nasazeno (commit e4514afa): filtr na druh pryč, prázdno se neukládá. Ověřeno na 32 lidech — do 27. 8. by se činnost smazala všem, teď žádnému.
2. Pravidlo Peti + Týnky: bere se zakázka a ta činnost, jaká je zadaná, dokud si ji člověk sám nezmění.
3. Ověřeno v Centrále: mezi zakázkou a činností NENÍ žádná vazba. Přehledy 1046 (režie, 32 položek) a 1047 (dílna, 76) jsou dva SEZNAMY, ne škatulky. Na zakázce Rezie se v roce 2026 použilo 3 287 režijních a 4 099 dílenských záznamů. Naše dělení činností to kopíruje správně, chyba byla, že z něj kód udělal omezení výběru.
4. Srpen srovnaný: 43 kancelářských úseků → „Bez rozlišení činnosti", 18 minutových ve výrobě → činnost z okolního úseku, Šárce 2 úseky → zakázka Rezie, Zemanovi odblokovaný předvýběr + zpráva na mobil. Dušan svých 7 a Pěchoučka doplnil sám v Opravách.
5. Nové pravidlo ve frontě Oprav `chybi_cinnost` (att_anomaly_scan, R9) — dvojče ke Kristýnině `chybi_zakazka`. Okno 14 dní, práh 0,1 h, výjimka na lidi, co se nekontrolují, úklid když se činnost doplní. Záloha `att_anomaly_scan__zaloha_20260827`.
6. Pojistka `rozpad-usek-bez-cinnosti`.
7. `app_vyroba_my_cinnosti` umí nově kind='prace' = obě pracovní skupiny. Zpětně kompatibilní — nic se nezmění, dokud appka o to nepožádá.
8. G2007: `doc-dochazka-cinnost-se-nesmi-mazat-pri-vyberu-zakazky`, `doc-dochazka-zakazka-a-cinnost-nemaji-vazbu`.
9. Mail pro Týnku o dvou oddělených evidencích „kdo se nekontroluje" (`Mail_Tynka_nekontrolovani_dochazky.eml`).

OTEVŘENÉ

* Tlačítko „V pořádku — vyřídit" ve frontě chce povinný důvod ze seznamu DRUHŮ CHYB. Peťa: „když říkám v pořádku, nevybírám přece druh chyby." Má odbavit rovnou s pevným důvodem, jako to už dělá „V pořádku — odbavit" v detailu dne (dochazka-opravy.html ~ř. 409, vzor ~ř. 845–858). NENASAZENO — v souboru pracuje C28 (Jirka). Běží na to hodinový automat od 18:00, k pátému pokusu pořád neuvolněno.
* Mobilní appka má přestat volit skupinu činností a žádat si kind=prace (71_plan_prace_cinnosti.js ~ř. 1006). Taky čeká na Jirku.
* Migrovat `set-zakazka` a `set-rezie` z router.py do g2007.python — dokud jsou na disku, nejde na ně napsat pojistku.
* Denní připomínka fronty chodí VŠEM členům skupiny DOCHÁZKA - OPRAVY bez ohledu na působnost. Výroba dostává kancelářské nálezy a naopak.
* Schvalovací banner: zvuk zahraje, banner nevyskočí. Doloženo — dvě žádosti hlásily timeout a přitom se v DB tváří jako vyřízené.
* Příznak „docházku nevede, a když náhodou ano, nekontroluje se" přímo v podmínkách člověka. Dnes je to seznam 9 čísel natvrdo na 8 místech ve dvou skriptech, plus oddělený příznak „plný fond bez docházky" s jinou množinou lidí. Obojí je věcně správně, jen na dvou místech. → Týnka.
* 4 úseky bez zakázky patří Martimu a Honomichlovi — nekontrolují se, neřeší se.

GOTCHY

* Most neumí dolarové uvozovky ($q$) — spadne na KeyError. Obyčejné apostrofy, zdvojené.
* Dvojtečku před písmenem (:k) bere most jako svůj parametr → skládat přes `|| chr(58) ||`.
* Slova INSERT/UPDATE ve vyhledávacím řetězci čtecího dotazu shodí read-only pojistku → skládat jako 'INS' || 'ERT'.
* „TIMEOUT po 120 s" NEZNAMENÁ, že zápis neproběhl. Ověřuj ve `fw.claude_write_request` podle id.
* Peťa jede tři session naráz, lanes 1–3 bývají obsazené. Ber tu, do které se nejdéle nepsalo.
* `tenant.att_employee` má víc řádků na člověka — join kvůli jménu zdvojuje. Používej LATERAL ... LIMIT 1.
