# Nulové záznamy a dělení píchnutí: jeden kořen (att_checkin switch), vzor byl v att_apply_work_selection, opraveno 10. 9. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Nulové záznamy a dělení píchnutí: jeden kořen, oprava na třech místech (10. 9. 2026)

Péťiny body **1** a **2** nebyly dvě chyby, ale **jedna**. Ověřeno v datech i v kódu,
opraveno 10. 9. 2026 (rozhodla Kristý jako rodič).

## Čísla, ze kterých se vycházelo (dotaz do `tenant.att_entry`, 10. 9. 2026)

| co | kolik | lidí |
|---|---|---|
| nulové pracovní záznamy za srpen (0,00 h, začátek = konec) | **149** | 37 |
| totéž za 1.–10. 9. | 13 | 11 |
| dva záznamy pod 60 s po sobě se **stejnou** zakázkou (od 1. 8.) | **205** | 46 |
| z toho úplně bez mezery (0 s) | 165 | 45 |
| původ nulových: `mobile_app` 157 · `notif_confirm` 4 · `tablet` 1 | | |

## Kořen

`att_checkin` při přepnutí zakázky (`switch=true`) ukončil běžící úsek a založil nový
**bez ohledu na uplynulý čas**. Nula sekund → nulový záznam (bod 1), pár sekund →
dělení bez důvodu (bod 2). Týž kód, jen jinak rychlý prst.

**Proč lidé ťukají dvakrát:** appka **nemá v CSS jediné pravidlo pro stav `disabled`**
(`mobile_parts/02_styles.html`). Zakázané tlačítko vypadá stejně jako aktivní, protože
barvu i pozadí mu dává vlastní třída. Člověk nevidí odezvu a ťukne znovu.
Doloženo naostro 9. 9. 2026: při testu pochůzek zůstala obrazovka stát kvůli jiné chybě,
za dvacet minut vzniklo **14 nulových úseků**. Stejný vzorec jako u lidí v provozu.

## ⭐ Vzor už v kódu BYL — v `att_apply_work_selection`

Ta funkce od začátku dělá přesně to správné: drží si příznak `dost_dlouho`
(`date_trunc('minute', now()) - date_trunc('minute', started_at) >= interval '1 minute'`)
a při změně zakázky **pod minutu úsek NEDĚLÍ** — jen přepíše `project_ref` na běžícím
(větev `elif _meni_se`, komentář *„kratší než minuta (typicky hned po příchodu) — bez dělení"*).

**Poučení: než navrhneš nové pravidlo, prohledej sourozenecké funkce.** Stejná logika
tam mohla být roky a stačí ji dorovnat. Práh „pod minutu" tedy není nový nápad — je to
konvence, která v kódu už žila, jen ji `att_checkin` a `att_checkout` neměly.

## Co se 10. 9. 2026 nasadilo

1. **`att_checkin`** (v14): při `switch` a běžící PRÁCI kratší než 60 s se útržek označí
   `superseded` a **nový úsek převezme jeho `started_at`** → neztratí se čas a ve dni
   zůstane jeden záznam místo dvou. (Pauza, `commute` a `day_end` se dělí dál.)
2. **`att_checkout`** (v11): kdo píchne příchod a hned odchod, nezanechá pracovní záznam
   s 0,00 h — označí se `superseded`.
3. **`att_apply_work_selection`** — beze změny v logice, už to uměla.

## Vedlejší nález: `GREATEST` chyběl na třech místech

Výpočet `hours` používá `date_trunc('minute', now())`, což zaokrouhlí **dolů**. Úsek
08:00:50 → 08:00:55 tedy vyjde **záporný**. `att_checkin` měl `GREATEST(…, 0)` na dvou
místech ze tří, `att_do_att_action` ho měl taky — chybělo v `att_checkin` (větev switch),
`att_checkout` a `att_apply_work_selection`. Doplněno 10. 9. 2026 jedním zápisem.

⚠️ **Těch 24 záporných záznamů v datech ale NENÍ z tohoto zaokrouhlení** — jsou mezi nimi
hodnoty −14,03 h a −10,88 h, což zaokrouhlení na minutu vyrobit neumí. Jde o záznamy,
kde je **`ended_at` dřív než `started_at`** (např. 1. 9. začátek 16:11, konec 12:58) —
tedy jiný původ (oprava nebo import). **Všech 24 je `superseded`, takže se nikde nepočítají.**
Zbývá dohledat, kdo je vyrábí.

## Postup, který se u těchto zápisů osvědčil (a je závazný)

1. Kompilace nového zdroje v sandboxu (`compile(src, kod, 'exec')`).
2. **Vložené SQL spustit naostro** jako obyčejný SELECT — kompilace SQL chyby nechytí
   (viz `doc-provoz-dve-session-jedna-funkce-zdvojene-apostrofy`).
3. Kontrola na `''` následované písmenem a na `:slovo` **i v komentářích** — 10. 9. spadla
   záplata na `:disabled` napsaném ve vlastním komentáři.
4. Pojistka v `WHERE`, že kotva je ve zdroji **právě jednou** → opožděné schválení projde 0 řádků.
5. Po zápisu **ověřit `md5(zdroj)`** proti otisku spočítanému lokálně před odesláním.

