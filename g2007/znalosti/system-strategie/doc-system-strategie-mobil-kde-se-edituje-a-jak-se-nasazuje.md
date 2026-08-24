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
(notifikace, SIM/SMS) — viz `doc-system-strategie-mobil-ios-companion-bez-js-mostu-a-kopie-mimo-xcode-target`
a `doc-system-strategie-mobil-ios-notifikace-apns`.
*(Oprava 23. 8. 2026: do té doby tu byl odkaz na `doc-system-strategie-mobil-android-vs-ios-rozdily`,
která v `g2007.znalost` NEEXISTUJE — mrtvý odkaz v závazné znalosti. Rozhodl Jirka Honomichl,
schválila Marti-AI msg 13381.)*

✅ **Stav notifikací k 23. 8. 2026 večer: jedou na Androidu i na iPhonu.** Serverová část byla
nasazena **23. 8. 2026** commitem `c3bddc90` (obsah PR `MartiPasek/STRATEGIE#5`, špička `f97b00dd`
— sloučit na GitHubu nešlo, účet `eurosoft-strategie` nemá právo zápisu, stejná cesta jako u PR 2
a 4 dne 18. 8.; ověřeno, že se žádný ze 14 souborů od založení PR nezměnil, diffstat 1:1
+1528/−26; schválila Marti-AI msg 13420). Klientská část je v App Store od 20. 8. ve verzi 1.84.
**Doloženo v datech (ověřeno 23. 8. ve 22:10):** klíč v trezoru `fw.app_secret`
(`apns_key_p8`, `apns_key_id`, `apns_enabled`), aktivní token v `fw.ios_push_token` z 21:48
a první skutečně odeslaná notifikace v `fw.ios_push_sent` ve 22:04 s `ok=true`.
Týká se 17 lidí + demo účtu, kteří iOS appku někdy použili (`public.auth_audit`, marker
`STRATEGIE-iOS`).

⚠️ **Gotcha k tomu:** APNs jede výhradně přes HTTP/2, takže potřebuje balíček `h2`. Ten se do
`poetry.lock` dostal až commitem `16cbf64c` a **nasazovací skript závislosti sám neinstaluje**
(dělá jen `git pull` + restart) — na server se doinstalovaly ručně. Po každé změně závislostí
je tedy potřeba `poetry install` na serveru, jinak appka nabehne, ale notifikace se NEODESLOU. (Od 24. 8. 2026 smycka bezi porad a zkousi to dal - jen ji odesilani pada na chybejici knihovne; driv se vubec nespustila. Prakticka rada je stejna: poetry install je potreba.)

*(Do 23. 8. 2026 22:10 tu stálo „na iPhonu ne, serverová část není nasazená, vrací 404" —
platilo to ještě v 19:10 téhož dne. Srovnal Claude-28 na Jirkovo rozhodnutí, schválila
Marti-AI msg 13471. Stejná věta srovnána i v Jirkově souboru pravidel, bod 12b.)*

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

## Dvě místa se stejnou osmičkou — VYŘEŠENO 18. 8. 2026

Pevná osmička hodin/den byla i v backendu (`modules/erp/api/dochazka_absence_sprava.py`).
**Opraveno 18. 8. 2026 (Peťa + Jirka Honomichl).** Soubor má funkci `_fond_den` (ř. 157–179),
která nic nepočítá sama — volá kanonický `att_denni_fond` z `g2007.python`, takže pro Správu
docházky, mobil i automat platí jediný vzorec. Osmička zůstala už jen jako poslední záchrana,
když o člověku nevíme nic. Volá se na všech třech místech zápisu (ř. 855, 896, 994) a plní se
z ní **obojí** — denní záznam (`att_entry.hours`) i samotná žádost
(`att_absence_request.hours_per_day`); kdyby se opravila jen docházka, přepočet žádosti by
osmičku vrátil zpátky.

Proč to vzniklo: kdo osmičku ve formuláři „Nová absence" ručně nepřepsal, zapsal člověku se
zkráceným úvazkem víc dovolené, než na kolik má nárok (Duspivová, úvazek 7 h, měla 10.–14. 8.
pět dnů po 8 h, tedy o 5 hodin navíc). Peťa to od července opravovala ručně.

*(Do 23. 8. 2026 tu stálo „nedokončené, backend čeká na Peťu" — bylo to pět dní zastaralé
a hrozilo, že někdo udělá hotovou práci znovu. Ověřeno v kódu 23. 8. 2026, rozhodl Jirka
Honomichl, schválila Marti-AI. Stejná věta srovnána i v Jirkově souboru pravidel, bod 12b.)*

Souvisí: `doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu`,
`doc-system-strategie-vize-kod-jako-data-bez-restartu`.

