# JMHZ 2026 (Jednotné měsíční hlášení zaměstnavatele) — podání na ČSSZ, chyby a opravy

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# JMHZ 2026 (Jednotné měsíční hlášení zaměstnavatele) — podání na ČSSZ, chyby a opravy

**Oblast:** mzdy · **Zapsal:** Claude-26 (Marti), 20. 7. 2026
**Stav:** ✅ VYŘEŠENO — ČSSZ přijala obě firmy 0 chyb (20. 7. 2026).

## Co to je
JMHZ = nové jednotné měsíční hlášení zaměstnavatele od 1/2026 (zákon 323/2025),
nahrazuje starý přehled o pojistném. e‑Podání XML, namespace
`http://schemas.cssz.cz/JMHZ/podani/1.0`. Generátor: `modules/erp/api/mzdy_jmhz.py`.
Spouští se z **Výplatnice** tlačítkem **„🏛️ JMHZ → ČSSZ"** (endpoint `…/app/mzdy/jmhz/xml`).

Firmy: **EC** = EUROSOFT‑Control, VS `4445158191` · **ES** = EUROSOFT‑System, VS `4442058998`.
kodOSSZ **444** (Plzeň‑město = prefix VS). DS e‑Podání ČSSZ `5ffu6xk`.

## Struktura hlášení
Hlavička `formularePocet` = **počet osob + 2** (formulář SOUHRN + formulář PVPOJ).
Typ podání: ŘÁDNÉ `R` / OPRAVNÉ `O` / STORNO. Každá osoba = jeden `formularOsoby`
(typ dle druhu činnosti: `bezPriznaku`, `cinnostKS` = jednatel/druh S, pěstoun, vězeň…).

## Pět chyb, které ČSSZ vrátila — a jejich příčiny (klíčové know‑how)

1. **20235** — špatný počet formulářů. Příčina: hlavička nepočítala SOUHRN a PVPOJ.
   Oprava: `pocet_formularu = n + 2`.
2. **20315** — pojistné zaměstnavatele nesedí. **Zásadní gotcha:** pojistné
   zaměstnavatele na každém formuláři musí být `ceil(VZ × 0,248)` = **zaokrouhleno
   na celé koruny NAHORU**. Helios ale ukládá `SocPojFirma` matematicky zaokrouhlené
   → u části lidí to o korunu nesedělo. Navíc **VZ = `ZakladSocPoj` (SocPoj vyměřovací
   základ), NE `HrubaMzda`.** Oprava: `sp_firma_form = ceil(vz_sp × 0,248)`, VZ tažen
   z Heliosu (`ZakladSocPoj`). (První diagnóza VZ=HrubaMzda byla mylná — 20315
   nezmizelo, dokud jsem nezaokrouhlil pojistné zaměstnavatele nahoru.)
3. **20267** — u **nulové mzdy** se nesmí posílat rozpad mzdy. Oprava: rozpad je
   prázdný, když hrubá = 0.
4. **40343** — **jednatel** musí mít formulář `cinnostKS` (druh činnosti **S**),
   ne `bezPriznaku`; a jeho formulář NESMÍ obsahovat `vymerovaciZakladParagraf5`
   ani `slevaZamestnavatele` (ČSSZ je u KS nečeká). Jednatel = Pašek Martin,
   oič/IKMPSV `1122284229` (řízeno přes `JEDNATEL_OIC`).
5. **20262** — **IDPPV musí být 13místné.** Opravené hodnoty: Pašek
   `4002765527578`, Peřina `4003127306142`. Zapsáno do **UCTO_EC.dbo.TabMzJmhzPP**
   (cloud MSSQL 188.12 = zdroj, který generátor čte; NE do live DB_EC).

## Výpočetní pravidla (celé koruny NAHORU = ceil)
- Pojistné zaměstnance (SP): `ceil(VZ × 0,071)`.
- Pojistné zaměstnavatele (per formulář): `ceil(VZ × 0,248)`.
- PVPOJ souhrn K8: `ceil(0,248 × Σ VZ)`.

## Opravné hlášení
Typ podání `O`; formuláře `typFormulare` R→O; **párování na původní podání podle
období + VS** (čistší než přes GUID — rozhodnutí Marti 20. 7.). Na Výplatnici je
vedle řádného tlačítko **„Opravné hlášení (typ O)"**. V našem případě nebylo nakonec
potřeba — řádné prošlo.

## Validace vs. realita
`epodani_validace` (SOAP `ePodaniValidace`, per `formularOsoby`, `test=True`) je zdarma
a bez podpisu, ale **NEodhalí 20235 ani 20315** — to jsou produkční kontroly ČSSZ.
Nutná reálná zkušenost z odmítnutého podání. Rychlý test přes most:
`@@JMHZGEN <firma> <rok> <mesic> [O <guid>]` (regeneruje + lokální kontroly +
validace) a `@@EPVALSTR | <xml>` (validace libovolného e‑Podání ze stringu).

## Výsledek (20. 7. 2026 — přijato)
- **EC** VS 4445158191: 19 formulářů, **0 chyb**, SOUHRN OK, PVPOJ OK (vč. Pašek jednatel + opravená IDPPV).
- **ES** VS 4442058998: 35 formulářů, **0 chyb**.

## Infrastruktura (most)
Deploy: `scripts/claude_sql/CLAUDE_DEPLOY.txt` (+`_GO`) → watcher py_compile + commit/push
+ cloud `/deploy/now`. SQL most: `CLAUDE_SQL.sql` + `CLAUDE_GO.txt` (db=pg / mssql188 =
UCTO_EC/ES / mssql = live DB_EC, `nonce=n<epoch>`) → `CLAUDE_OUT_FULL__<nonce>.txt`.
Občas transientní `HTTP 401` na cloud deployi → stačí zopakovat trigger.


