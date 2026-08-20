# Podklad OSVC Faze 2: zapis zpet (nase strana + Helios + ukol) — co je nasazeno 19.8.2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Faze 2 — zapis zpet po vygenerovani podkladu OSVC

Claude-24 (Kristy), 19. 8. 2026. Navazuje na `doc-mzdy-podklad-osvc-vypocet-zakazek-final`.
Navrh a rozhodnuti: `docs/navrh_osvc_faze2_zapis_zpet.md`.

## Retez funkci (vse `g2007.python`)

| kod | vedl. ucinek | co dela |
|---|---|---|
| `podklad_vyplaceni_pdf` | ne | POCITA podklad (obdoba `_Priprava`). Vraci navic `radky_data` = strojova podoba radku + ID zdroju k orazitkovani |
| `podklad_osvc_helios_plan` | ne | NAHLED objednavky: organizace, rada dokladu, kterou pripravenou objednavku by pouzil a jake polozky by vznikly. Jde pustit pres `@@PYRUN` |
| `podklad_osvc_zapis` | ANO | hlavicka `tenant.osvc_vobj` (stav 'navrzeno') + radky `tenant.osvc_vobj_radek` + razitka `fakturace_obj_id` na rezii a dovolenou |
| `podklad_osvc_helios_obj` | ANO | polozky objednavky (`CCBEZDANIKC`) + `EC_Zakazky_PlatbyZam` + razitka `IDPolVObj` v Centrale + prepocet dokladu; stav → 'objednano', `centrala_vobj_ref` = poradove cislo |
| `podklad_ukol_send` | ANO | ukol na Nakup (11001) — nove pres `_Loc` (seznam kopii) + `EC_Ukolnik_OdesliUkol` (notifikace) |
| `podklad_osvc_generuj` | ANO | ORCHESTRATOR: 1) zapis u nas 2) objednavka 3) ukol |

## Endpointy (tenke delegaty v router.py)

- `GET /app/vyroba/podklad-osvc/plan?uid=&firma=` → nahled
- `POST /app/vyroba/podklad-osvc/objednavka {uid, firma}` → ostry beh

Brana `_PODKLAD_OSVC_UIDS = {41, 18, 13}` + rodice (`is_marti_parent`): Dusan Havlat (41),
Petra Safrankova ml „Peta" (18, c. 1), Sarka Novotna (13), Kristy (11) a Marti (1).
Kristy 19.8.2026: *„casem to budou vsichni vedouci oddeleni, budou si to delat pro sve lidi"*.

## FLOW

Dve tlacitka podle firmy — **EC → rada dokladu 800**, **ES → 801** (Kristy: *„aby si Dusan
mohl pri generovani vybrat, kam to chce generovat"*), plus tlacitko „Nahled objednavky".

## Zasadni detaily, at se neztrati

- **Objednavka se NEZAKLADA** — bere se posledni nerealizovana dane organizace
  (`TabDokladyZbozi`, `Realizovano=0`) a smazou se jeji prazdne polozky. Nove prazdne
  objednavky zakladaji **rucne holky z Nakupu** (overeno: zadny `INSERT INTO TabDokladyZbozi`
  v Centrale neexistuje, autori dokladu jsou AndreaB / Michelle / IvanaH).
  Kdyz zadna neni → hlaska, nic se nezapise.
- **Nerealizuje se** (`DatRealizace` zustava prazdne) — realizuji holky rucne (Kristy).
- **Poradove cislo objednavky jde do PREDMETU ukolu** (Kristy 19.8.2026), proto se ukol
  zaklada az po uspesnem zapisu objednavky. `@IDDoklad` = ID objednavky → PDF do adresare ukolu.
- **Kopie ukolu:** 475 Bernardova Andrea, 442 Hruzova Iva, 420 Honomichlova Ivana,
  381 Safrankova Michelle, 1 Safrankova ml Petra + **zadavatel** (kdo tlacitko zmackl).
- **Nulovy podklad** (0 Kc, dnes Havlat): nic se nezaklada, nic neposila, uzivatel dostane
  hlasku proc.
- **Poradi zapisu je zamerne**: nejdriv k nam ('navrzeno'), pak Helios. Kdyz Helios spadne,
  hlavicka zustane 'navrzeno', nic se neorazitkuje a jde to spustit znovu.
- **Pojistka proti dvojimu behu**: existuje-li pro cloveka hlavicka ve stavu 'navrzeno',
  dalsi generovani skonci hlaskou s jejim cislem.
- `dry=True` je DEFAULT u obou zapisovych funkci — bez explicitniho `dry=False` se nezapise nic.

## Overeno nanecisto (Kilberger 346, 19.8.2026)

Organizace 715, rada 800, objednavka ID 769944 / poradove 861582 (zalozila AndreaB 9:38,
4 prazdne polozky k smazani — overeno, ze maji nulovou castku a zadnou vazbu na platbu).
Plan: Rezie 1 278 · Rezie/odmena 1 000 · VR10641 29 557 · VR10676 2 083 (zaloha) ·
VR10684 68 639 (zaloha) = **102 557 Kc**. Orazitkovalo by se 3 radky u nas a 1 odmena v Centrale.

## Co zbyva

- **Ostry beh nikdo jeste nespustil.** Prvni musi jit z aplikace (most zapisove skripty
  nepousti). Doporuceni: nejdriv na jednom cloveku a hned zkontrolovat doklad v Heliosu.
- `flow.html` neni v `g2007.soubor` — migrace je samostatny ukol (meni se i umisteni
  souboru do gitignorovaneho `static_db/`), Kristy 19.8.2026 odsouhlasila odlozeni.

