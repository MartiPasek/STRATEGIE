# Mobilní appka: kde se co edituje a jak se to nasazuje (závazné pro všechny)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobilní appka — kde se co edituje a jak se to nasazuje

**Závazné pro všechny instance i lidi. Jirka Honomichl + Marti-AI, 17. 8. 2026.**
Vzniklo po zjištění, že práce dvou lidí se do appky nikdy nedostala a nikde to nehlásilo chybu.

## Dva světy, které se nesmí míchat

| Co | Kde žije | Jak se mění | Do gitu? |
|---|---|---|---|
| **Webový obsah appky** (obrazovky, tlačítka, logika v JS) | `g2007.soubor`, typ `zdroj`, kódy `apps/api/static/mobile_parts/*` | `@@G2007SOUBOR` + `@@G2007PUBLISH` | **NE** |
| **Sestavená stránka** | `g2007.soubor`, typ `artefakt`, kód `apps/api/static_db/mobile.html` | vzniká publikací | **NE** (gitignore od 5. 8.) |
| **Nativní appka** | `APP/Mobile` (Android, Kotlin), `APP/iOS` (Swift) | běžný git commit + deploy | **ANO, jen tohle** |

Obě appky (Android i iPhone) jsou jen okno, které načítá **tutéž** stránku `/mobile`.
Obsah se tedy mezi platformami rozejít nemůže. Rozdíly jsou jen v nativních schopnostech
(notifikace, SIM/SMS) — viz `doc-system-strategie-mobil-android-vs-ios-rozdily`.

## Správný postup při úpravě obrazovky

1. **Přečti si živý obsah z DB**, ne z disku:
   `SELECT obsah, md5(obsah), length(obsah) FROM g2007.soubor WHERE kod='apps/api/static/mobile_parts/<soubor>'`
   (u velkého dílku přes `encode(convert_to(obsah,'UTF8'),'base64')` a dekóduj u sebe)
2. **Uprav a zapiš:** `@@G2007SOUBOR apps/api/static/mobile_parts/<soubor> | zdroj` + obsah na dalších řádcích
3. **Ověř zápis čtením a porovnej md5.** Návratovka mlčí i při úspěchu.
4. **Publikuj:** `@@G2007PUBLISH apps/api/static_db/mobile.html` (má vlastní kontroly + auto-revert)
5. **Ověř na živé `/mobile`**, že změna naběhla **A že nic jiného nezmizelo**
   (stáhni stránku před a po, porovnej po řádcích — mizet smí jen to, co jsi měnil).

## Tvrdá pravidla

- **Nikdy needituj dílek na disku.** Od 17. 8. 2026 tam žádný není — složka `apps/api/static/mobile_parts/`
  je smazaná z gitu a v `.gitignore` (commit `5b130553`).
- **Nikdy nespouštěj `scripts/build_mobile.py`.** Od 17. 8. 2026 už nic nedělá, jen vypíše varování.
- **Po zápisu fragmentu VŽDY porovnej md5** — tvrdé pravidlo, ne doporučení (rozhodla Marti-AI 17. 8.).
- **Měníš cizí dílek? Stav na aktuálním obsahu z DB, ne na verzi z gitu ani ze staré kopie.**
  Jinak smažeš práci, která v DB přibyla mezitím.
- **Těsně před zápisem znovu ověř md5** — mezi tvým čtením a zápisem mohla psát jiná instance.

## Past: most ořezával konec zápisu — OPRAVENO 17. 8. 2026, obcházka už není potřeba

**Jak to bylo:** `scripts/claude_sql_runner.py:598` dělá `read_text(...).strip()`, takže zápis přes most
přišel o koncové bílé znaky včetně posledního nového řádku. Dílky se slepovaly prostým spojením, takže
koncový `//` komentář dílku **zakomentoval první řádek následujícího dílku**.
Projev: po zápisu nesedí md5, přitom všechny řádky jsou totožné.

**Opraveno u kořene commitem `d57d9ef9` (17. 8. 2026)** — detail v
`doc-system-strategie-most-orez-koncove-newline-oprava`:

- `@@G2007SESTAV` i `@@G2007PUBLISH` slepují fragmenty **newline-safe** (každý dílek zakončen newline
  před slepením). Není to `<script>` separátor — ten kdysi rozbil sdílený closure — jen řádkový zlom.
- `@@G2007SOUBOR` ukládá obsah **vždy s koncovou newline**.

⚠️ **Ruční obcházku `UPDATE g2007.soubor SET obsah = obsah || chr(10) …` už NEPOUŽÍVEJ.** Do 18. 8. 2026
ji tato znalost předepisovala, přestože od 17. 8. 15:19 platí oprava výše — dvě aktivní znalosti si tím
odporovaly. Sjednoceno podle skutečného stavu kódu; **rozhodl Jirka Honomichl 18. 8. 2026.**

⚠️ **Co ale trvá:** `.strip()` v runneru je na místě dál (ověřeno v kódu 18. 8. 2026) — opravený je následek
na straně serveru, ne příčina na straně mostu. **Koncové bílé znaky jiné než newline se pořád ztratí**,
takže **kontrola md5 po zápisu zůstává tvrdým pravidlem** (viz výše).

## Proč to pravidlo vzniklo (ať se to neopakuje)

Úklid 5. 8. 2026 správně vyřadil z gitu **sestavené** soubory, ale na **zdrojové dílky** a na
`scripts/build_mobile.py` se zapomnělo. Repo tak dál lidem návodem přikazovalo starý postup
(„edituj dílek → spusť skript → commituj"), který od 1.–3. 8. vede do prázdna. Kdo ho poslechl,
jeho práce se do appky nikdy nedostala — bez jediné chybové hlášky.

Takto tiše zmizelo (z 92 přidaných řádků jich 89 v appce nebylo):
- **Peťa 5. 8.** (`f4f7e6e7`) — rozsah absence podle úvazku místo pevné osmičky. Její vlastní
  zdůvodnění: *„lidem se zkráceným úvazkem se strhávalo víc dovolené, než měli."*
- **Šárka 12. 8.** (`6a000461`, `865f538b`, `7b233f87`, `7ca280dc`) — číselník zdravotních
  pojišťoven, profilová fotka, karta Novinky, potvrzení účasti. Backend endpointy nasazené byly,
  chybělo jen mobilní UI.

Obojí doneseno do DB a nasazeno 17. 8. 2026. **Není to chyba Peti ani Šárky** — postupovaly podle
toho, co jim repo říkalo.

**Poznámka k Petinu commitu:** `f4f7e6e7` omylem smazal řádek `var sb=el('<button ...>')`, ale
`sb.addEventListener` nechal — ta verze by při otevření formuláře spadla. Při přenosu se to
neuplatnilo, protože se stavělo na aktuálním obsahu z DB. Další důkaz, že to nikdy neběželo.

## Dvě místa se stejnou osmičkou (nedokončené)

Pevná osmička hodin/den je i v backendu: `dochazka_absence_sprava.py:715` a `:845` (nečte úvazek).
Mobilní část je od 17. 8. opravená, **backend čeká na Peťu**. Peťa musí vědět o obou místech
a řešit je koordinovaně (podmínka Marti-AI 17. 8. 2026).

Souvisí: `doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`,
`doc-system-strategie-vize-kod-jako-data-bez-restartu`.

