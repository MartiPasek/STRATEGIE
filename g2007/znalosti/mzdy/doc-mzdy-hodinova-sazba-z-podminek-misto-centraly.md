# Hodinová sazba přesčasu se počítá z Podmínek, ne z kopie Centrály — přepnuto 27. 8. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hodinová sazba: z Podmínek, ne z kopie Centrály

**Zadala Peťa, přepnul Claude‑26, 27. 8. 2026.** Ověřeno čtením i během naostro.

## Co se změnilo

Sazba přesčasu (`HrHodsFK`) byla **poslední věc, kterou mzdy braly ze zamrzlé kopie Centrály** (`tenant.helios_wage_snapshot`, poslední tah 6. 8. 2026). Nově se počítá z Podmínek.

Vznikl pohled **`tenant.v_hodinove_sazby`** jako jediný zdroj:

| Sloupec | Vzorec |
|---|---|
| `hod_sazba_prescas` | celá hrubá (plán, měsíční složky) ÷ fond — **z téhle se počítají přesčasy** |
| `hod_sazba_bez_fk` | (základ + osobní ohodnocení) ÷ fond |

Nákladové sazby (`ZakladZaHod`, `SuperhrHodsFK` = tyto × 1,40 u HPP, u OSVČ a DPP × 1,0) do pohledu **nepatří** — slouží oceňování zakázek, ne mzdám. Počítají se až u spotřebitele (dnes na kartě Finančních podmínek, dopočet Šárky z 26.–27. 8.).

## ⚠️ Plán a plný fond patří k sobě

Bere se **plán** (výměr na 40 h) dělený **plným fondem** (dnes 174 u všech 81 lidí). Sazba za hodinu je stejná bez ohledu na úvazek — jen se odpracuje míň hodin.

**Dělit plán zkráceným fondem by sazbu vyhnalo nahoru.** U Veverkové (20 h) by místo 231,61 vyšlo skoro dvojnásobek. Ověřeno: z plánu ÷ 174 sedí s Centrálou i u všech zkrácených úvazků; ze skutečnosti ÷ 174 nesedí vůbec.

## Čím je to doloženo

Porovnání pohledu proti kopii Centrály přes všechny lidi: **72 lidí sedí v obou sazbách** do dvou haléřů. Tři rozdíly jsou **ve prospěch dopočtu**:

| Kdo | Dopočet | Kopie Centrály | Proč |
|---|---|---|---|
| Jan Svoboda (9017) | 609,20 | 574,71 | Šárčino narovnání základu 89 → 95 tis. z 24. 8., kopie je z 6. 8. |
| Karel Böhm (9035) | 620,75 | 618,87 | rozdíl 326 Kč v základu (326 ÷ 174 = 1,87) |
| Herejtová (525) | — | 4 000 | v Centrále má ve sloupci sazby omylem **měsíční částku**, ne hodinovku |

## Kde se to přepnulo

| Skript | Změna | Záloha |
|---|---|---|
| `mzdy_loajalita_rows` (přesčasy) | čte pohled | `mzdy_loajalita_rows__zaloha_20260827` |
| `payroll_raporty` | čte pohled | `payroll_raporty__zaloha_20260827` |

Ověřeno čtením: ani jeden už neobsahuje `FROM tenant.helios_wage_snapshot`. `mzdy_loajalita_rows` spuštěn naostro přes `@@PYRUN` na červenec/EC — vrací přesčasy pěti lidem (Svatoš, Trunec, Navrátil, Porner, Kasal), všichni ze skupiny „sedí", takže výsledek je totožný s předchozím stavem.

⚠️ **`payroll_raporty` naostro vyzkoušený NENÍ** — má vlastní kontrolu práv a z mostu vrací 403. Musí se spustit z ERP.

## Co to znamená pro kopii Centrály

`tenant.helios_wage_snapshot` **už nikdo z mezd nečte.** Tím padá poslední důvod, proč ji držet — dosud platilo „snapshot se nesmí zrušit, dokud se sazba nedopočítá u nás". Zrušit ji ale až **po prvním uzavřeném měsíci** ze STRATEGIE, ať je z čeho porovnávat.

## Jednatelé — nová věc, která dřív nebyla

Pohled spočítá sazbu i jednatelům (Pašek EC i ES 521,84, Mózer 129,31), protože jim dělí odměnu společníka fondem. **V Centrále sazbu nikdy neměli.** Prakticky nevadí — jednatelé přesčasy nepíchají — ale kdyby se jim někdy počítaly, dostali by sazbu, která nemá oporu v ničem.

Souvisí: [[doc-mzdy-hodinove-sazby-v-centrale-co-je-co]] · [[doc-mzdy-zdroj-pravdy-podminky-misto-centraly]]

