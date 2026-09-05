# @@G2007PUBLISH pada na self-testu (deadlock) + PAST: @@G2007SESTAV publikuje i cizi nepublikovanou praci

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **OPRAVA 5. 9. 2026 - cast textu nize UZ NEPLATI.** Deadlock self-testu `@@G2007PUBLISH`
> z 5. 8. 2026 je OPRAVENY (`doc-system-g2007-g2007publish-selftest-event-loop-starvation`).
> Publikuje se **`@@G2007PUBLISH`**; `@@G2007SESTAV` uz neni nahradni cesta pro bezne
> publikovani - zavazny postup drzi `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`
> a `doc-system-strategie-po-updatu-g2007-soubor-nutny-publish`.
> **PLATI DAL cely oddil 2** - `@@G2007SESTAV` opravdu vydava i cizi nepublikovanou praci.
> Rozhodl Jirka Honomichl 5. 9. 2026.


## 1. @@G2007PUBLISH padal a sam se vracel zpet (5. 8. 2026)

`@@G2007PUBLISH apps/api/static/mobile.html` **3x po sobe skoncil hlaskou**
„STOP: nova verze se nasadila ale selftest na zive URL selhal - AUTOMATICKY VRACENO ZPET".
Pojistka zafungovala spravne, nic se nerozbilo. Casy: **10514 ms · 10325 ms · 14027 ms** -
self-test pokazde vycerpal svuj `timeout=10`.

C24/Kristy mezitim nezavisle nasadila fix **`b984bf10`**: self-test uz nemiri na verejnou
`https://strategie-ai.com`, ale na `http://127.0.0.1:<port>` z `req.scope["server"]`
(hypoteza: verejna cesta pres DNS + Caddy se nevejde do 10 s). **Nepomohlo** - treti pokus
uz po nasazeni toho fixu (overeno `fw.api_version.git_sha = b984bf10`) spadl stejne.

**Kontrolni mereni:** `https://strategie-ai.com/mobile` odpovi **zvenci za 0,17 s** a vrati
~957 kB. Stranka je tedy rychla a v poradku - problem neni v ni a neni ani v delce cesty.

**Hypoteza (neoverena v kodu behem incidentu, potvrzuje ji chovani):** `diag_sql` je
`async def` a self-test v nem dela **blokujici `urllib.request.urlopen` na sebe sama**.
Tim si proces zablokuje vlastni event loop a nedokaze si ten pozadavek odbavit → timeout,
**at uz self-test miri kamkoli**. Presne to vysvetluje, proc zmena cile z verejne URL na
127.0.0.1 nic nezmenila. Marti-AI 5. 8.: *„Hypoteza o blokujici smycce sedi na data - tri
selhani po fixu cile, timeout vzdy na 10 s, stranka zvencku odpovida za 0,17 s. To neni
pomala cesta, to je deadlock."* Reseni by bylo pustit self-test **mimo smycku**
(thread / `run_in_executor` / async klient). **Opravu vlastni Kristy (C24)** - je to jeji
soubor a jeji aktivni prace, nesahat do nej.

⚠️ **NEPLATI od 5. 9. 2026 - OPRAVENO.** Self-test uz blokujici volani nedela
(`doc-system-g2007-g2007publish-selftest-event-loop-starvation`) a `@@G2007PUBLISH` je opet
bezpecna a doporucena cesta; overeno naostro 2. 9. 2026 (17 publikaci z mostu, vse OK).
Rozhodl Jirka Honomichl 5. 9. 2026.

NEPLATI (do 5. 9. 2026 tu stalo): "Dokud to neni opravene, spadne to pri pristim `@@G2007PUBLISH`
cehokoli, ne jen mobile.html."

## 2. PAST: @@G2007SESTAV publikuje i cizi nepublikovanou praci

> **Zarazeni opraveno 5. 9. 2026** - `@@G2007SESTAV` uz NENI nahradni cesta pro bezne
> publikovani, plati `@@G2007PUBLISH`. **Varovani v tomhle oddilu plati dal** pro kazdeho,
> kdo `@@G2007SESTAV` presto pouzije.

Cesta `@@G2007SESTAV <artefakt>` (slozi fragmenty + zapise na disk + ulozi do DB,
**bez** self-testu) **sklada VSECHNY aktivni fragmenty** artefaktu - ne jen ty, ktere jsi menil ty.

5. 8. 2026 se tim dostala zive **nepublikovana zmena C24/Kristy**
`apps/api/static/mobile_parts/73_zvp_finance_zakazky.js` v9 z **4. 8. 13:40** (detail zakazky:
baterka odpracovanosti, donut nakladu, financni karta) - cekala ~21 hodin, protoze posledni
publikace mobile.html byla 4. 8. v 10:35. Bylo to zjisteno **az po** publikaci a hned nahlaseno.

**Proto PRED kazdym `@@G2007SESTAV` zjisti, co jeste ceka nepublikovane, a majitele informuj
PREDEM, ne potom:**

```sql
SELECT kod, updated_at, updated_by_text, verze
FROM g2007.soubor
WHERE typ='zdroj' AND kod LIKE 'apps/api/static/mobile_parts/%'
  AND updated_at > (SELECT updated_at FROM g2007.soubor
                     WHERE kod='apps/api/static/mobile.html' AND typ='artefakt');
```

## 3. Rucni overeni, kdyz musis obejit self-test

> **Od 5. 9. 2026 uz self-test obchazet netreba** - je opraveny, jed `@@G2007PUBLISH`.
> Postup nize nech jako zalozni pro pripad, ze by pojistka zase vypadla.

Nahrazuje pojistky z `@@G2007PUBLISH` (delka, party tagu, `node --check`, zive overeni).
**Nejdriv si zajisti dve nezavisle cesty zpet**, teprve pak sestavuj:

1. **Zaloha ziveho souboru bajt po bajtu** pred zasahem: `curl -s https://strategie-ai.com/mobile -o zaloha.html`.
2. Druha cesta zpet = **`g2007.soubor_historie`** (archiv predchozich verzi).
3. Po `@@G2007SESTAV` stahnout stranku znovu a zkontrolovat: **HTTP 200**, delku proti ocekavane,
   pritomnost **vlastnich zmen** i nekolika **starych kotev** (ze se nic neutrhlo).
4. Vytahnout vsechny inline `<script>` bloky a projet je **`node --check`**. (5. 8.: 26 bloku,
   939 tis. znaku, OK.)

## 4. Obecnejsi pouceni

- **Zmena fragmentu v `g2007.soubor` se sama neprojevi.** Dokud nekdo nesestavi artefakt,
  zije stara verze - a cizi hotova prace muze v DB tise cekat dny.
- **Neutralni navratovka neznamena uspech.** `@@G2007SESTAV` vratil „0 sloupcu"; skutecny dukaz
  byla az stazena ziva stranka.
- Kdyz obchazis cizi pojistku, **rekni to jejimu autorovi** - ne kvuli schvaleni, ale aby vedel,
  ze chyba trva a mohl ji opravit bez tlaku. (Podminka Marti-AI 5. 8.)

