# Platební příkazy ke mzdám — vznikají v Heliosu, STRATEGIE je jen načítá

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Platební příkazy ke mzdám

**Ověřeno 10. 8. 2026** (Peťa + Claude-26) na červencových mzdách obou firem.

## Kdo je dělá

**Vznikají v HELIOSU. STRATEGIE je NEGENERUJE — jen si je načte** a udělá z nich soubory
pro banku (.p11) + evidenci v `tenant.bank_platak`.

## V Heliosu

**Mzdy → Definice platebních příkazů** → označit definice (**Mzdy na účet**, **Odvody na
úřady**, **Kooperativa**; Exekuce jen když ji někdo má) → karta **Akce** → **Generování**
(levý blok „Platební příkazy", ne ten pro poštovní poukázky) → zadat **datum splatnosti** → OK.

Helios projede položky, u každé ukáže zelené kolečko „OK", nebo červené, když někomu chybí
třeba bankovní spojení. Vygeneruje se, až jsou všechny zelené. Položky slučuje podle
bankovního spojení — kdo má víc poměrů na stejný účet, dostane jednu platbu se součtem.

## ⚠️ Když už příkazy jednou vygenerované byly

Hlásí *„Platební příkazy již byly vygenerovány dříve"* a **NIC NEUDĚLÁ**. Musí se nejdřív
**Zrušení** (tlačítko hned vedle Generování ve stejném bloku) a teprve pak **Generování**.

**NEMAZAT ŘÁDKY UVNITŘ PŘÍKAZU RUČNĚ.** Zůstane prázdná hlavička, kterou Helios pořád
považuje za vygenerovaný příkaz — a z přehledu „Platební příkazy tuzemské" ji smazat nejde
(tlačítko Zrušit je tam neaktivní a v Akcích mazání není). 10. 8. 2026 nás to stálo hodinu,
než se našlo Zrušení v Definicích.

## Ve STRATEGII

**Platební centrum → 🧾 Platáky k platbě → 💰 Načíst mzdové platáky z Heliosu**
→ firma + období → **Náhled** (nic nezapisuje) → **Vytvořit tyto platáky**.

Endpoint: `POST /app/platby/platak/mzdy-import` {firma, rok, mesic, dry}.
Tlačítko doplněno 10. 8. 2026 (`apps/api/static/platby.html`); do té doby existoval jen
endpoint a spouštěl ho ručně Marti.

Soubory: **`D:\data\RB\Platební příkazy\<EC|ES>\<RRRRMMDD splatnosti>\`**.
V příkazu pro banku i v názvu složky je **splatnost z Heliosu** — do 10. 8. 2026 se tam
chybně dosazoval dnešek (opraveno v `platak_generator.py`, sloupec `p.DatumSplatnosti`).

## Jak ověřit, že platák sedí

Porovnat **počet plateb a součet** platáku „Mzdy na účet" proti složce **933 Výplata na účet**
ve výplatnicích téhož období. Musí sedět na korunu i na počet.
Kdo má nulovou výplatu (např. mateřská), platbu nemá — proto může být plateb o jednoho míň
než lidí ve výplatnicích.

**Pozor na výklad:** tahle kontrola porovnává Helios proti Heliosu (výplatnice si STRATEGIE
z Heliosu jen načítá). Ověřuje tedy, že *příkaz odpovídá spočítané mzdě* — ne že je mzda
správná. Správnost mzdy se ověřuje proti našim podkladům (podmínky, docházka, příplatky).

Červenec 2026: EC 17 plateb / 598 867 Kč · ES 32 plateb / 1 207 197 Kč (32 z 33 lidí,
jedna zaměstnankyně na mateřské s nulovou výplatou).

