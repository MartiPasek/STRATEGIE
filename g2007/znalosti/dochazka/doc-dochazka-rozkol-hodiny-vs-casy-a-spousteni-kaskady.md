# Rozkol docházka × rozpad — hodiny neseděly s vlastními časy + kaskáda se nespouštěla všude (18.–19. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Odkud to vzešlo.** Kontrolní přehled *Docházka → Kontrolní přehledy → Docházka × rozpad*
hlásil rozdíly mezi hodinami docházky (`tenant.att_entry`) a součtem položek rozpadu
(`tenant.vyroba_work`). Předání Péťa → Kristý 17. 8. 2026, rozbor Claude-24 pro Kristý.
Nešlo o jednu chybu, ale o **tři nezávislé příčiny**.

## 1. Hodiny hlavičky neodpovídaly časům téže hlavičky (hlavní, přesah do mezd)

Trigger `tenant.att_entry_round_minutes` (BEFORE INSERT/UPDATE, jen tenant_id 2) ořízne
`started_at` a `ended_at` na celé minuty, ale sloupec `hours` nepřepočítá. Aplikace ho přitom
počítala z `now()` **včetně sekund**. Hodiny proto byly systematicky vyšší než rozdíl uložených
časů; položky rozpadu počítaly z oříznutých časů, a tak vycházely níž.

- Měřeno 10.–14. 8. 2026 (866 záznamů): žádný záznam nemá v časech sekundy; odchylka na záznam
  −0,003 až +0,020 h, prakticky vždy plus. Součet 1.–14. 8. **+8,63 h** z 3 574,9 h (0,24 %).
- **Přesah do mezd** — druhý trigger `att_entry_resummary` sčítá `hours` do
  `att_day_summary.cas_celkem` (typy work, homeoffice, fond_doplneni), a to je mzdový podklad.
- **Opraveno 19. 8. 2026** (A1) — ve všech pěti místech se hodiny počítají z
  `date_trunc('minute', now())`. `ended_at` se needituje, ten trigger ořízne tak jako tak.
- **Zbytkový rozdíl je strukturální** — `att_entry.hours` je `numeric(5,2)`, kdežto
  `vyroba_work.hodiny` má 3 desetinná místa. Zaokrouhlení na 2 místa dělá ±0,005 h na záznam,
  ale náhodně na obě strany, takže se to nesčítá jako dřív.
- **Historie se sama neopraví** — přepočet srpna je samostatný krok (má mzdový dopad,
  schvaluje Marti).

## 2. Položka rozpadu přesahovala přes pauzu

`_wa_open` (příchod / přepnutí zakázky) maže právě zavřenou položku kratší než 60 s a nová
položka **převezme její začátek** (pravidlo proti parazitním úsekům, Marti 19. 6. 2026).
Když mezi tím byla pauza, položka ji snědla — Jirkovský 11., 13. i 14. 8. 2026 (13 až 17 minut),
Honomichl 12. 8. dokonce 137 minut.

Kanonická kaskáda `att_sync_vyroba_work` tohle **umí srovnat** (ořez položky na hranice úseku
plus vyplnění okrajů) — jen se v těch případech vůbec nespustila. Do 18. 8. běžela pouze při
odhlášení přes notifikaci a při ručních opravách.

## 3. Dvě kopie téhož kódu (databáze × router.py)

Ořez časů položek na celé minuty doplnil Péťa 4. 8. 2026 do `g2007.python`, ale staré kopie
`_wa_close_running` a `_wa_open` zůstaly i v `router.py` a ořez nemají. Proto mělo
**408 z 1 277 srpnových položek sekundy v `od`** a 365 v `konec`. Sjednocení je rozdělané —
sdílená implementace `att_wa_close_running` už v g2007.python je (zatím ji nic nevolá).

## Co je nasazeno (autorizovala Kristý, C24)

| Kód | Změna | Kdy |
|---|---|---|
| `att_sync_vyroba_work` | guard na `att_period_locked` před zápisy, fail-closed | 18. 8. |
| `att_checkout` | volá kaskádu po uzavření úseku | 18. 8. |
| `att_do_att_action` | kaskáda i ve větvi checkin a resume_work | 18. 8. |
| `att_auto_checkout_midnight` | RETURNING vrací i den, kaskáda po půlnočním uzavření | 18. 8. |
| `att_confirm_day` | kaskáda po potvrzení dne | 18. 8. |
| `att_wa_close_running` | nová sdílená implementace (nikdo ji zatím nevolá) | 18. 8. |
| `att_checkin`, `att_checkout`, `att_do_att_action` | hodiny z času na celé minuty (A1) | 19. 8. |

**Pozor na pořadí** — guard na zámek období musel být dřív než rozšíření spouštěčů. Do 18. 8.
zámek období nekontroloval **žádný** zapisovatel do `vyroba_work`, takže rozšířená kaskáda by
jinak přepisovala i uzavřené mzdy.

## Co zbývá

Přepočet hodin za srpen (mzdový dopad, Marti) · backfill položek za srpen přes `att_fix_resync`
(9 přesahů u 4 lidí) · dokončit sjednocení `router.py` s databází (blokuje konflikt v gitu) ·
prevence v `_wa_open`, aby nová položka nepřebírala začátek přes mezeru · hlídání
„položka rozpadu bez zakázky" ve frontě Oprav (dnes to nehlídá `att_fix_queue` ani
`att_anomaly_scan`).

## Gotcha pro každého, kdo bude editovat kód v g2007.python přes SQL most

Most posílá celý příkaz přes SQLAlchemy `text()`, takže **dvojtečka následovaná slovem**
kdekoli — i v komentáři, i v hodnotě sloupce — spadne na *A value is required for bind
parameter*. Vnitřní SQL skládej konkatenací, a když potřebuješ do zdroje uložit skutečné bind
parametry, pošli placeholder a nech dvojtečku doplnit Postgres přes `chr(58)`. Úprava
existujícího kódu jde bez banneru (konstruktivní), **založení nového kódu banner vyžaduje**.
Ověřuj čtením a kompilací staženého zdroje, ne návratovkou.

Podklady: `docs/navrh_dochazka_rozpad_sjednoceni.md` (rozbor), `docs/navrh_dochazka_rozpad_zmeny.md`
(změnový list se stavem).

