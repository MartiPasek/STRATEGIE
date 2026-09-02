# JMHZ 07/2026 — proč generátor tiše vyrobil vadné hlášení a jak se to opravilo

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# JMHZ 07/2026 — tichý propad generátoru do defaultů

**Oblast:** mzdy · **Zapsal:** Claude-24 (Kristý), 2. 9. 2026
**Stav:** opraveno a nasazeno (commit `7a73b466` → `d6bd9a03`), opravná hlášení odeslána, čeká se na protokoly ČSSZ.

## Co se stalo
Hlášení za 07/2026 odeslané 18. 8. 2026 ČSSZ vrátila: **Control (VS 4445158191) 23 vad + ZAMÍTNUTÁ pojistná část**, **System (VS 4442058998) 2 vady**. Reálných příčin bylo šest, ne 23 — osm kódů `40xxx` byly jen následky zamítnuté pojistné části („kontrola potřebuje Pvpoj formulář").

## Kořenová příčina (ověřeno v datech, ne odhad)
`mzdy_jmhz.py` bere z cloud Heliosu tři věci, ale **každou jinak**:
- `attach_identifikatory` (OIČ, ID PPV) — z **posledního dostupného měsíce ≤ období** → přežilo
- `attach_dane` (prohlášení poplatníka, sleva) — taky z posledního měsíce → přežilo
- `attach_eldp` (kód ELDP, vyloučené/odečitatelné doby) — **striktně jen za dané období** → nedostal NIC

Za 07/2026 je `TabMzJmhzEldp` i `TabMzJmhzPP` v UCTO_EC i UCTO_ES **prázdná** (mzdy v `TabZamVyp` spočítané jsou: 17 a 33 osob). Generátor to spolkl a spadl do defaultů.

## Proč to v červnu prošlo — DŮLEŽITÉ
Ne proto, že by Helios ta data měl. Podle `Autor` + `DatPorizeni` v `TabMzJmhzEldp`/`TabMzJmhzPP` (EC 2026):
- 04/2026 — autor `Martia` (uživatel Heliosu), pořízeno 18. 5.
- 05/2026 — autor `Martia`, pořízeno 12. 6.
- **06/2026 — autor `sa` (SQL admin), pořízeno 12. 7. ve 23:50** = ruční výplň přes SQL most, ne z Heliosu
- 07/2026 — nic

Červen tedy prošel jen proto, že ta data někdo v noci ručně doplnil. **Nespoléhat na to** — proto oprava dělá přenos automaticky.

## Mapování vad na osoby (Control 07/2026)
| Osoba | oič | Kód ELDP v 06 | Prohlášení | Vady v 07 |
|---|---|---|---|---|
| Mózer, č. 47 | 1163295640 | S++ (jednatel) | false | 40087, 40244, 40245, 40343 |
| Pašek, č. 2 | 1122284229 | S++ | true | 40087 |
| Herejtová, č. 525 | 1628688886 | prázdný = ZMR (druh T) | false | 40087, 40244, 40245 |
| Senft, č. 374 | 1328922298 | prázdný = ZMR (druh T) | false | 40087, 40244, 40245 |
| Vlková, č. 361 | 1628612513 | 1++ | false | 40244 |

Čtyři s 40087 = přesně ti, co nemají kód `1++`. Čtyři s 40244 = přesně ti bez prohlášení. **Mózer byl druhý jednatel, kterého jsme v kódu neměli** (`JEDNATEL_OIC` obsahoval jen Paška) → 40343.

## Čísla k zamítnuté pojistné části (20008 + 20168)
Posláno: základ **660 845**, pojistné zaměstnavatele 160 666. ČSSZ počítá 24,8 % z 660 845 = 163 890 → nesedí o 3 224.
Správný základ = součet `ZakladSocPoj`, ne `HrubaMzda` = **647 845** (Herejtová hrubá 4 000 / VZ 0, Senft 9 000 / VZ 0 — dohody bez účasti). 24,8 % ze 647 845 = **160 666**, tedy přesně vykázané pojistné.
Loňská oprava „VZ = ZakladSocPoj, ne HrubaMzda" (chyba 20315) se aplikovala **jen na formuláře osob**, do souhrnu PVPOJ ne.

## Co bylo opraveno
1. `build_jmhz` — `zaklad_zam_a` počítán z `vz_sp` místo z `hruba`. Filtr na `zmr` ponechán (u nich se nuluje pojistné, musí vypadnout i ze základu).
2. `attach_eldp` — doplněn **přenos kódu z posledního dostupného období** (stejný vzor jako `attach_identifikatory`/`attach_dane`), `eldp_zdroj='helios-prenos'`. Přenáší se POUZE kód; vyloučené a odečitatelné doby patří ke konkrétnímu měsíci a přenášet se NESMÍ.
3. `_person_form` — `cinnostKS` se odvozuje z kódu ELDP začínajícího `S`, ne z natvrdo zadaného `JEDNATEL_OIC` (ten zůstal jen jako pojistka).
4. `_person_form` — `prohlaseniPoplatnikaDane` se **neposílá vůbec**, když prohlášení není. ČSSZ nestačí nula, atribut musí chybět.
5. `prepare_persons` — nové pole `varovani`, `eldp_prenos`, `eldp_bez_osoby`. Když Helios za období nemá ELDP, generátor to napíše místo aby tiše dosadil `1++`.

Výsledek po opravě (Control): základ 647 845, kódy 13× `1++` + 2× `S++` + 2× `T++`, `cinnostKS` 2, blok slevy jen 13×. Validace ČSSZ přes `@@JMHZGEN EC 2026 7`: 17/17 OK.

## Co ZBÝVÁ (neopraveno)
**40245 — srážková daň.** Generátor ji **neumí vůbec** (grep přes repozitář: nikde), vždy posílá `zalohaNaDan`. Herejtová (4 000 → 600) a Senft (9 000 → 1 350) mají v Heliosu `zvldanSrazenaDan` > 0, tedy srážkovou daň — a ČSSZ u nich atributy zálohové daně odmítá. K dodělání je potřeba XSD ČSSZ pro blok srážkové daně; v repozitáři žádné XSD není.
Otevřené: u Mózera (zálohová daň, ale druh S) není jisté, jestli 40245 spadne samo tím, že jde nově jako `cinnostKS`. Vlková má taky prohlášení `false` a 40245 nedostala — samotné chybějící prohlášení to tedy nespouští.
Otevřené: pojistné zaměstnance vykazujeme jako součet po osobách (EC 46 004, ES 88 659), zaokrouhlení ze součtu VZ by dalo 46 001 / 88 646. U zaměstnavatele sedí na korunu. Jestli ČSSZ ten rozdíl toleruje, ukáže až protokol.

## Gotchy, které stály čas
- **Dílčí protokol ≠ protokol o kompletnosti.** Dílčí kontroluje jen strukturu XML a může být „0 chyb", zatímco kompletnost (přijde později, porovnává proti evidenci zaměstnanců) najde vady. ES měl přesně tohle. Zápis „0 chyb" u června se týkal dílčího protokolu.
- **Chyba 40226 se NEŘEŠÍ opravným hlášením**, ale odhláškou z evidence zaměstnanců — REGZEC akce 2, viz `doc-mzdy-jmhz-40226-evidence-zamestnancu-odhlasky`.
- Odpovědi ČSSZ se do Heliosu nenačítají — `TabMzJmhz.DatumPrijeti` i `TextOdpovedi` jsou u všech období prázdné. Protokoly žijí jen v datovce.

