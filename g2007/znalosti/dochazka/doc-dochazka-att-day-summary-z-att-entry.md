# att_day_summary se počítá z att_entry (ne z Centrály) + mateřská + plný fond bez docházky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se změnilo (C24/Kristý, 3.–4. 8. 2026)

`tenant.att_day_summary` (denní mzdový podklad docházky) se dřív plnil **1:1 zrcadlem
Centrály** (`@@DOCHSUM` / `sync_dochazka_sumaden` z `EC_Dochazka_SumaDen`). Nově se
**počítá přímo ve STRATEGII z `tenant.att_entry`**. Důvod: att_entry je zdroj pravdy
(Marti 26.7.), je úplnější než Centrála a od července Centrála do mezd nevstupuje.

## Nástroje

- **`@@DOCHCALC <rok> <mesic> [dry]`** (SQL most) — přepočet měsíce z att_entry.
  `dry` = jen souhrn, nic nezapíše. Bez `dry` = ostrý zápis (smaž měsíc + insert).
- **Tlačítko „🔄 Přepočítat"** v `/payroll` (Mzdové podklady) → endpoint
  `POST /app/payroll/recompute` (auth rodič / `mzdy:read`). Pro Péťu k ručnímu spuštění.
- **Idempotentní** — lze pouštět opakovaně, vždy bere poslední stav att_entry, nezdvojuje.
- Delegát = `g2007.python` kód **`att_day_summary_recompute(rok, mesic, dry_run)`**.
- **`@@DOCHSUM`** (Centrála zrcadlo) zůstává jako fallback.

## Výpočtová logika

- `cas_celkem` = `tenant.att_den_hodiny` (odpracováno, slučuje překrývající se úseky,
  odečítá pauzu uvnitř práce) **+ placená absence**. (Loajalita/přesčas složka 651 čte
  cas_celkem jako „celkem − fond", proto absence MUSÍ být uvnitř.)
- `cas_montaz` ← typ `work` (Práce), `cas_rezie` ← typ `overhead` (Režie). Montáž se
  NErozlišuje (druh 9 padá do Práce). Mzdové podklady: odpracováno = montaz+rezie.
- Absence kýble ← att_entry podle typu: vacation/sick/sickday/family_care/medical/maternity.
- `fpd` = `engagement.uvazek_tyden_h/5`, jen pracovní den (att_calendar_day).
- **OSVČ s docházkou se POČÍTAJÍ** (kdo píchá, je uvnitř — Centrála je taky měla přes
  per-osobní sumaci). Vylučují se jen z MEZD (`_mzdy_absence_rows` typ='osvc' ven), ne z docházky.
- Mzdy NEČTOU: cas_pauza, cas_prescas, cas_chybi, att_day_summary.uzavreno → plní se 0/false.
- cas_nahr_volno / cas_nariz_volno / cas_absence / cas_prekazka: att_entry nemá zdroj → 0.

## Pojistka na zmrazené měsíce

Funkce má `FROZEN={(2026,6)}` — **červen 2026 přepočet ODMÍTNE** (mzdy hotové z Centrály).
Nové zmrazené měsíce se přidají do téhle množiny ve funkci.

## Mateřská

att_entry neměl typ mateřská (import mapoval Centrála druh 36 → `sick`). Přidáno:
- `tenant.att_entry_type` code **`maternity`** (absence, placená).
- Mapování importu `_DRUH_ABSENCE` **36 → maternity** ve 3 aktivních g2007.python skriptech:
  `att_ec_druh_entry_type`, `sync_ec_dochazka_recent`, `sync_vyroba_work_ec`.
- Historie přetypována cíleným UPDATE (sick→maternity) mimo zmrazený červen.
- Pozn.: druh 33 (otcovská) je pořád mapovaný na `sick` — samostatný TODO.

## Plný fond bez docházky (jednatelé/vedení co nepíchají)

Někteří lidé si nevedou docházku, ale v Centrále měli plný fond + mzdu (z výplatní strany).
Replikace ve STRATEGII:
- Příznak **`engagement.plny_fond_bez_dochazky`** (boolean, DDL 4.8.).
- Pro označené přepočet generuje **plný fond per pracovní den** (cas_celkem = cas_montaz =
  fpd = úvazek/5, ostatní 0) a jejich `att_entry` IGNORUJE.
- Aktuálně nastaveno pro jednatele/vedení bez docházky. **Přidání dalšího = nastavit mu
  `plny_fond_bez_dochazky=true` na aktuálním engagementu.**

## Kde je detail
Repo: `docs/dochazka_att_day_summary_z_att_entry.md` (plný postup, ověření, srovnání s Centrálou).

## Doplněno 14. 8. 2026 (Claude-28 za Jirku, schválila Marti-AI, msg 12704)

Job `sync_ec_dochazka_sumaden` (fw.mirror_job, interval 10 minut, enabled) byl **6. 8. 2026 přepojen** z `_sync_dochazka_sumaden` (živé zrcadlo staré Centrály) na `_ec_dochsum_ze_strategie`, tedy na výpočet z naší docházky. Ze staré Centrály se tudy už nechodí. Rozhodli Peťa a Kristý 6. 8. 2026.

Výjimka — **květen 2026 zůstává z Centrály**, ale jede přes samostatný job `sync_sumaden_2026_05`, který je vypnutý.

⚠️ V gitu leží **osiřelý soubor** `g2007/znalosti/mzdy/doc-mzdy-mzdy-podklad-zdroj-pravdy.md` (psaný 22. 7. 2026), který tvrdí, že `att_day_summary` je živé zrcadlo Centrály. **To už neplatí** a v DB tato znalost neexistuje — je to jen zbytek projekce.

