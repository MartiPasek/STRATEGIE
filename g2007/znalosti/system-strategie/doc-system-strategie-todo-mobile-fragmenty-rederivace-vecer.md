# TODO (VECER 3.8.2026, mimo produkci): znovu rozrezat mobile.html v6 na fragmenty bajtove presne - sestav==zivak

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> **NEPLATNE od 5. 9. 2026.** Postup publikace obsahu mobilu popsany nize UZ NEPLATI - plati @@G2007PUBLISH, viz doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje (24. 8. 2026) a doc-system-strategie-po-updatu-g2007-soubor-nutny-publish (31. 8. 2026). Duvod - @@G2007SESTAV vydava i cizi nepublikovanou praci. Rozhodl Jirka Honomichl 5. 9. 2026. Dokument zustava jen jako historie.

## Zadani (dohoda Marti + Jirka + C23, rano 3.8.2026)

Provest AZ VECER po produkci (riziko zasahu do zive appky). Erika/zluta hlaska VYRESENA JINAK Jirkou - export v6 NENI potreba, zadna urgence.

## Stav a pricina (overeno C23 rano 3.8., cisla sedi na znak)
- Zivy artefakt g2007.soubor 'apps/api/static/mobile.html' = v6, 911 984 zn, md5 3e05f808b086391f7b9e2d64b31f5d7b (v5 rollback-monolit z 1.8. 15:59 + Jirkuv patch +1656 zn z 3.8. 07:27, ktery je JEN v DB, na disku/zivaku neni a nema byt - funkce vyresena jinak; pri rederivaci vyjasnit s Jirkou, zda v6 patch v artefaktu ponechat nebo vratit na v5 obsah).
- 28 fragmentu mobile_parts/* v DB pochazi z JINE vyvojove rady (izolacni experiment 1.8., v2/v4 = 865 540 zn, spadl na syntax chybe) - NEJSOU vyrezy ziveho monolitu: jen 3 z 28 jsou v zivaku verbatim (01_boot_lock, 02_styles, 03_shell), soucet fragmentu 866 852 vs zivak 911 984 (rozdil 45 132 zn). Konce radku (CRLF) vylouceny (0 CR vsude).
- DUSLEDEK: @@G2007SESTAV/@@G2007PUBLISH pro mobile.html NEPOUZIVAT do opravy - slozily by vadnou verzi. Sanity kontrola v PUBLISH to spravne blokuje (proto Jirkova stopka 3.8. 07:17).

## Postup opravy (vecer)
1. Vzit aktualni obsah artefaktu (po dohode s Jirkou v6 nebo v5) jako zdroj pravdy.
2. Rozrezat na fragmenty podle STEJNYCH hranic jako slozeno_z (vc. <script> obalek - kazdy fragment musi byt doslovny vyrez, zadna normalizace), rezy vest po celych radcich.
3. UPDATE vsech 28 zdroj radku + kontrola: konkatenace fragmentu v poradi slozeno_z == artefakt BAJTOVE (md5 shoda) - az pak povazovat publikacni cestu za duveryhodnou.
4. Zpresnit sanity kontrolu v @@G2007PUBLISH (pocitani tagu ignoruje vyskyty v JS retezcich, nebo nahradit md5/diff kontrolou proti zivaku) - kandidat pro Marti-AI (doladovani).
5. Overit @@G2007PUBLISH nanecisto + zapsat vysledek do G2007.

## Kontext
Souvisi: doc-system-g2007-migrace-python-soubor-stav-2026-08-01 (vznik systemu + incident 1.8.), zprava C28 v conv 363 (3.8. 07:17, otazky Q1-Q4), eskalace Marti-AI tamtez. Odpovedi C23: Q1 zamysleny stav = zivy monolit; Q2 nepublikovat ze skladani; Q3 kontrola hruba ale zachranila produkci; Q4 vyreseno jinak (Jirka).

