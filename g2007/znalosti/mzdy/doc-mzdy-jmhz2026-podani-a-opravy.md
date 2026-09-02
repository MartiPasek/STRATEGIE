# JMHZ 2026 (Jednotné měsíční hlášení zaměstnavatele) — podání na ČSSZ, chyby a opravy

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# JMHZ 2026 (Jednotné měsíční hlášení zaměstnavatele) — podání na ČSSZ, chyby a opravy

**Oblast:** mzdy · **Zapsal:** Claude-26 (Marti), 20. 7. 2026 · **Opraveno:** Claude-24 (Kristý), 2. 9. 2026 (sekce Opravné hlášení)
**Stav:** červen 2026 přijat 0 chyb. Pro červenec 2026 viz [[doc-mzdy-jmhz-cervenec2026-tichy-propad-generatoru]].

## Co to je
JMHZ = nové jednotné měsíční hlášení zaměstnavatele od 1/2026 (zákon 323/2025), nahrazuje starý přehled o pojistném. e‑Podání XML, namespace `http://schemas.cssz.cz/JMHZ/podani/1.0`. Generátor: `modules/erp/api/mzdy_jmhz.py`. Spouští se z **Výplatnice** tlačítkem **„🏛️ JMHZ → ČSSZ"** (endpoint `…/app/mzdy/jmhz/xml`).

Firmy: **EC** = EUROSOFT‑Control, VS `4445158191` · **ES** = EUROSOFT‑System, VS `4442058998`. kodOSSZ **444** (Plzeň‑město = prefix VS). DS e‑Podání ČSSZ `5ffu6xk`.

## Struktura hlášení
Hlavička `formularePocet` = **počet osob + 2** (formulář SOUHRN + formulář PVPOJ). Typ podání: ŘÁDNÉ `R` / OPRAVNÉ `O` / STORNO. Každá osoba = jeden `formularOsoby` (typ dle druhu činnosti: `bezPriznaku`, `cinnostKS` = jednatel/druh S, pěstoun, vězeň…).

## Pět chyb, které ČSSZ vrátila — a jejich příčiny (klíčové know‑how)

1. **20235** — špatný počet formulářů. Příčina: hlavička nepočítala SOUHRN a PVPOJ. Oprava: `pocet_formularu = n + 2`.
2. **20315** — pojistné zaměstnavatele nesedí. **Zásadní gotcha:** pojistné zaměstnavatele na každém formuláři musí být `ceil(VZ × 0,248)` = **zaokrouhleno na celé koruny NAHORU**. Helios ale ukládá `SocPojFirma` matematicky zaokrouhlené → u části lidí to o korunu nesedělo. Navíc **VZ = `ZakladSocPoj` (SocPoj vyměřovací základ), NE `HrubaMzda`.** Oprava: `sp_firma_form = ceil(vz_sp × 0,248)`, VZ tažen z Heliosu (`ZakladSocPoj`). (První diagnóza VZ=HrubaMzda byla mylná — 20315 nezmizelo, dokud jsem nezaokrouhlil pojistné zaměstnavatele nahoru.) ⚠️ **Tato oprava se 20. 7. aplikovala jen na formuláře osob, do souhrnu PVPOJ ne** — v 07/2026 to způsobilo zamítnutí celé pojistné části (20008/20168), viz [[doc-mzdy-jmhz-cervenec2026-tichy-propad-generatoru]].
3. **20267** — u **nulové mzdy** se nesmí posílat rozpad mzdy. Oprava: rozpad je prázdný, když hrubá = 0.
4. **40343** — **jednatel** musí mít formulář `cinnostKS` (druh činnosti **S**), ne `bezPriznaku`; a jeho formulář NESMÍ obsahovat `vymerovaciZakladParagraf5` ani `slevaZamestnavatele` (ČSSZ je u KS nečeká). ⚠️ **Od 2. 9. 2026 se druh S odvozuje z kódu ELDP `S++`, ne z natvrdo zadaného `JEDNATEL_OIC`** — v tom chyběl druhý jednatel (Mózer, oič 1163295640).
5. **20262** — **IDPPV musí být 13místné.** Opravené hodnoty: Pašek `4002765527578`, Peřina `4003127306142`. Zapsáno do **UCTO_EC.dbo.TabMzJmhzPP** (cloud MSSQL 188.12 = zdroj, který generátor čte; NE do live DB_EC).

## Výpočetní pravidla (celé koruny NAHORU = ceil)
- Pojistné zaměstnance (SP): `ceil(VZ × 0,071)`.
- Pojistné zaměstnavatele (per formulář): `ceil(VZ × 0,248)`.
- PVPOJ souhrn K8: `ceil(0,248 × Σ VZ)`, kde **Σ VZ = součet `ZakladSocPoj`, ne hrubých mezd**.

## Opravné hlášení — OPRAVENO 2. 9. 2026

⚠️ **Původní znění této sekce bylo VĚCNĚ ŠPATNĚ.** Stálo v ní, že se opravné podání páruje „na původní podání podle období + VS (čistší než přes GUID)". **Není to pravda a ČSSZ podle toho podání zamítne.**

Ověřeno 2. 9. 2026 na obou firmách naráz: obě opravná podání byla zamítnuta s vadou **40217 (nepropustná) „Chybný GUID podání. Řádné podání se nenašlo"**.

**Platí:** opravné podání (`typPodani` = `O`, formuláře `typFormulare` R→O) MUSÍ v elementu **`<n1:idPodani>` nést GUID JMH původního ŘÁDNÉHO podání**. `idPodani` = GUID měsíčního hlášení; ČSSZ podle něj páruje. Generátor jinak dosadí náhodné UUID a ČSSZ z něj vyrobí nové JMH bez vazby na řádné podání.

**Kde GUID vzít:** protokol o kompletnosti **k ŘÁDNÉMU podání**, řádek „GUID JMH". ⚠️ **Past:** protokol o zamítnutém opravném podání obsahuje také řádek „GUID JMH", ale je v něm ten nově vygenerovaný — ten je k ničemu.

**Jak se zadává:** tlačítko **„⬇ Stáhnout OPRAVNÉ (typ O)"** na Výplatnici se na GUID zeptá, ověří tvar a pamatuje si ho per firma+období (commit `6807cfdf`, 2. 9. 2026). Přes most: `@@JMHZGEN <firma> <rok> <mesic> O <guid>`. Přes HTTP: `…/app/mzdy/jmhz/xml?firma=EC&rok=2026&mesic=7&opravne=1&guid=<GUID>`.

GUIDy řádných podání za 07/2026: EC `38472AB1-756A-407D-A6C5-6503768345B2` · ES `D3F8CD19-4DA0-47CA-B95F-1559E55E4B8F`.

## Dva protokoly — nezaměňovat (stálo to čas 3×)
- **Protokol o dílčím podání** (přijde hned, i jako XML z datovky): kontroluje **jen strukturu XML**. „Podání bylo přijato, 0 chyb" zde znamená pouze *„soubor je čitelný"*.
- **Protokol o kompletnosti** (přijde později, PDF): porovnává hlášení proti **evidenci zaměstnanců** a páruje na řádné podání. **Rozhoduje tenhle.** Podání může mít dílčí protokol „0 chyb" a přesto být v kompletnosti zamítnuté.
- Odpovědi ČSSZ se **do Heliosu nenačítají** — `TabMzJmhz.DatumPrijeti` i `TextOdpovedi` jsou u všech období prázdné. Protokoly žijí jen v datovce.

## Chyba 40226 — NEŘEŠÍ se opravným hlášením
„V podání nebyly nalezeny očekávané individualizované součásti dle evidence registru zaměstnanců" = ČSSZ eviduje otevřený pojistný vztah, který jsme nevykázali. Řeší se **odhláškou z evidence zaměstnanců (REGZEC, akce 2)**, ne hlášením. Detail: [[doc-mzdy-jmhz-40226-evidence-zamestnancu-odhlasky]].

## Validace vs. realita
`epodani_validace` (SOAP `ePodaniValidace`, per `formularOsoby`, `test=True`) je zdarma a bez podpisu, ale **NEodhalí 20235 ani 20315** — to jsou produkční kontroly ČSSZ. Stejně tak neodhalí 40217 (GUID). Nutná reálná zkušenost z odmítnutého podání. Rychlý test přes most: `@@JMHZGEN <firma> <rok> <mesic> [O <guid>]` (regeneruje + lokální kontroly + validace) a `@@EPVALSTR | <xml>` (validace libovolného e‑Podání ze stringu).

## Výsledek (20. 7. 2026 — přijato)
- **EC** VS 4445158191: 19 formulářů, **0 chyb**, SOUHRN OK, PVPOJ OK (vč. Pašek jednatel + opravená IDPPV).
- **ES** VS 4442058998: 35 formulářů, **0 chyb**.

## Infrastruktura (most)
Deploy: `scripts/claude_sql/CLAUDE_DEPLOY.txt` (+`_GO`) → watcher py_compile + commit/push + cloud `/deploy/now`. SQL most: `CLAUDE_SQL.sql` + `CLAUDE_GO.txt` (db=pg / mssql188 = UCTO_EC/ES / mssql = live DB_EC, `nonce=n<epoch>`) → `CLAUDE_OUT_FULL__<nonce>.txt`. Občas transientní `HTTP 401` na cloud deployi → stačí zopakovat trigger.

