# Fond (FPD) se bere z úvazku ve STRATEGII, ne ze zrcadla Centrály — a co ho přepisovalo zpátky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 4. 8. 2026.** Realizace zadání z 28. 7.
(`doc-dochazka-fond-a-narok-z-podminek-ne-ze-zrcadla`).

## Pravidlo

Fond = `engagement.uvazek_tyden_h ÷ dny v týdnu` × počet pracovních dnů měsíce.
Kanonický vzor je skript **`att_denni_fond`**, podle něj se sjednocuje zbytek.

**Ze zrcadla Centrály fond NEBRAT.** V `EC_Dochazka_SumaDen.FPD` je natvrdo 7,00
bez ohledu na úvazek. Data ve STRATEGII jsou správná a sedí na `EC_FinZamPodminky`.

**Fond musí být vidět u VŠECH lidí, i u dílenských** (Peťa): sice se jim do fondu
nedopichuje, ale plnit ho musí a pro mzdy je potřeba vědět, kdo má kolik.

## ⚠️ Co to tiše vracelo zpátky (nález 4. 8. 2026)

**`sync_dochazka_sumaden`** (1:1 zrcadlo Centrály) měl v `ON CONFLICT DO UPDATE`
také `fpd=EXCLUDED.fpd`. Kdykoli někdo pustil měsíční synchronizaci z obrazovky
mzdových podkladů, přepsal fond zpátky na hodnotu z Centrály.

Doloženo: 4. 8. ve 20:47 proběhl přepočet z úvazku, ve **22:13:06 jedním během
přepsáno 391 dnů července** zpátky na 7,00 — tedy i lidem se zkráceným úvazkem
(Dvořáková 6 h, Veverková 4 h). Spuštění nebylo ani v `fw.claude_sql_log`, ani
v `fw.ops_request` → šlo z aplikace, tlačítkem.

**Oprava:** `fpd` odebráno z `ON CONFLICT` — sync aktualizuje všechno ostatní, ale
fond nechá být, protože ten sloupec vlastní STRATEGIE. Při **INSERTU** se hodnota
z Centrály použije dál (u dnů, kde jiný zdroj nemáme).

## Stav skriptů k 4. 8. 2026

| skript | stav |
|---|---|
| `att_denni_fond` | ✅ vzor — úvazek ÷ dny v týdnu |
| `att_day_summary_recompute` | ✅ fond z úvazku (Kristý, 3. 8.) |
| `sync_dochazka_sumaden` | ✅ opraveno 4. 8. — `fpd` už nepřepisuje |
| `att_fix_day` | ✅ opraveno 4. 8. — fond počítá VŠEM (dřív vracel NULL mimo kategorie s `dopichavat_fond`, proto dílna fond neviděla nikde) + nová hodnota v odpovědi `fond_dopichava`, aby se řádek „nad fond (nenárokové)" ukázal jen tomu, komu náleží |
| `dochazka_kontrola_data` | ✅ opraveno 4. 8. — fond z úvazku, bez podmínky na kategorii |
| `mzdy_loajalita_rows` | ✅ V POŘÁDKU — ověřeno 5.8.2026 (Kristý + Peťa, dvě nezávislé kontroly): sloupec `fpd` NEČTE vůbec, fond si počítá z úvazku, ze zrcadla bere jen `cas_celkem`. Loajalita výrobních → složka 651, koeficient 1,25. |
| `mzdy_benefity_apply` | ✅ V POŘÁDKU — ověřeno 5.8.2026: sloupec `fpd` NEČTE, fond počítá z úvazku, ze zrcadla bere jen hodiny absencí. Náhrada za oblečení (794), home office (795), korekce osobního ohodnocení (432). Pozor: **zatím vůbec neběží**, čeká na `lm_engine`. |
| `att_automat_level_day` | ✅ ověřeno na datech — dopichuje přesně na úvazek (Veverková na 4,00, Dvořáková na 6,00, Novotná na 7,00), chybná sedmička se do docházky nikdy nepromítla |

## Ověření po opravě

Za červenec 2026 sedí fond s úvazkem u **všech 1 313 pracovních dnů, nula odchylek**.

⚠️ **Pozor při kontrole:** porovnávej jen **pracovní dny**. O víkendu a ve svátek je
`fpd = 0` správně — naivní porovnání proti dennímu úvazku hlásí falešné odchylky
(4. 8. jsem si tím sám vyrobil 18 neexistujících chyb).

## Tichý předpoklad, který zatím nevadí

`work_mode_id` nemá vyplněné **nikdo** ze 74 aktivních lidí, takže se všude počítá
s 5 dny v týdnu. `att_day_summary_recompute` má dokonce `/5.0` natvrdo. Funguje to,
ale kdo bude mít čtyřdenní týden, spočítá se špatně.

Příklad, že se to týká reality: **Bernardová (475) ve středu nepracuje** — 32 h =
4 dny × 8 h — ale systém jí fond rozpočítává na 5 dnů po 6,4 h. Měsíčně to vyjde
nastejno, takže to zatím nic nerozbíjí.

## Pojistka

`tenant.pojistka` kód **`fond-z-uvazku-ne-z-centraly`** hlídá, že se `fpd=EXCLUDED.fpd`
nevrátilo do syncu a že `att_fix_day` počítá fond všem. **Pojistka jen POZNÁ, nezabrání** —
zámek proti přepsání neexistuje.

## Souvisí

`holiday_balance.narok_h` je natvrdo 200 h u všech bez ohledu na úvazek — stejná
třída chyby, dosud neopravená (zadání z 28. 7.).

