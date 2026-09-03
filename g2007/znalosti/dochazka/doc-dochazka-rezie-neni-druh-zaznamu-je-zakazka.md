# Režie NENÍ druh záznamu, je to zakázka — zdroj zastaven 2. 9. 2026, historie převedena 3. 9. 2026 (HOTOVO)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Peťa, 2. 9. 2026.** Peťa: „už jsme to řešili asi 100×, 100× jsme si řekli, že už nikde se režie používat nebude, vždy jsi mi to potvrdil — a teď mi píšeš taková čísla, jak je to možné?" Tohle je odpověď a zároveň záznam, aby to bylo naposled.

## STAV K 3. 9. 2026 — UZAVŘENO
Zdroje zastaveny 2. 9., historie převedena 3. 9. **V docházce nezůstal ani jeden záznam s druhem Režie** (ve všech stavech, superseded včetně). Detail převodu: `doc-dochazka-rezie-druh-zaznamu-preklopen-na-praci`.

## Závazný model (Peťa 2. 9. 2026)
**Režie NENÍ druh záznamu.** Druhy jsou jen tři:
1. **Práce** — nese zakázku (`Rezie`, `VR…`, `PR…`, `SW…`) a k ní činnost
2. **Pauza**
3. **Absence** — na zakázce `Rezie`, druh určuje činnost

`Rezie` se píše **bez diakritiky** a je to **zakázka** (Peťa + Marti 20. 7. 2026, tak to má Helios i Centrála). „Režie" s háčkem není nic.

## Proč to přežilo tolik kol
Pokaždé se zavřely **dveře, kterými to bylo vidět**, ne ty, **kterými to teče**:

| kdy | co se udělalo | co zůstalo |
|---|---|---|
| 21. 7. 2026 | Režie zmizela z nabídky v Opravách | server ji dál přijímal |
| 1. 9. 2026 | `overhead` vypadl z `_ATT_FIX_TYPES` (server) | **appka ji zakládala dál** |
| 2. 9. 2026 | opraveny tři skripty u zdroje | historie zůstala |
| 3. 9. 2026 | historie převedena | **hotovo** |

**Nikdo neměřil, jestli se to přestalo zakládat.** Stav k 2. 9. 2026: 5 849 aktivních záznamů u 67 lidí — a jen za 1.–2. 9. dalších 39 u 10 lidí, všechny z mobilu.

**Poučení (platí dál a je hlavní hodnota tohoto zápisu):** u pravidla typu „tohle se už nikde nepoužívá" nestačí zavřít nabídku. Musí se změřit, jestli data opravdu přestala vznikat — a měřit až **u zdroje**, ne na obrazovce.

## Kde to vznikalo a co se změnilo (nasazeno 2. 9. 2026)
Tři místa v `g2007.python`, všechna na serveru — **appka se neměnila**, posílá `kind='overhead'` dál a server z toho udělá Práci:

| skript | bylo | je |
|---|---|---|
| `att_checkin` (píchnutí z mobilu) | `tcode = {"overhead": "overhead", …}` | `work`; když chybí zakázka, doplní `Rezie` |
| `att_apply_work_selection` (výběr zakázky za chodu) | `_novy_code = "overhead" if is_rezie` | vždy `work`, režie zůstává v zakázce |
| `att_entry_project` (přiřazení zakázky) | `overhead` + `stored_ref = None` | `work` + `stored_ref = 'Rezie'` |

U `att_entry_project` se navíc **zahazovalo číslo zakázky** — proto vzniklo 83 záznamů typu Režie úplně bez zakázky.

## NEPLATNÉ — dřívější plán, překonáno 3. 9. 2026
Původně tu stálo, že se převod historie **odkládá až po srpnových mzdách**. NEPLATÍ. Převod proběhl 3. 9. 2026, ještě před mzdami, protože se ukázalo, že je mzdově neutrální (žádný mzdový skript druh `overhead` nečte) a naopak blokoval opravy: dokud měl záznam druh Režie, server ho odmítl uložit v Opravách.
Rovněž NEPLATÍ obava, že převod „sahá na hodiny 67 lidí" — hodiny se nemění, mění se jen druh (obojí je `category='presence'`, `is_paid=true`, `affects_balance=true`).

## Co ZBÝVÁ (jediné otevřené)
**Archivovat druh `overhead` v `tenant.att_entry_type`**, aby bylo vidět, že se nesmí použít. Teď už to jde — žádný záznam na něm nevisí. Pozor: `overhead` čte ~22 skriptů a 8 stránek (většinou jako `code IN ('work','overhead','homeoffice')`), takže archivace se má udělat vypnutím nabídky, ne smazáním řádku.

**Vedlejší účinek, se kterým počítat:** bývalé režijní záznamy jsou teď Práce, takže na ně platí kontroly, které `overhead` vyjímaly — hlavně „zapomenutý odchod" (výjimka Marti 27. 6. 2026). To je v pořádku, zapomenutý odchod je zapomenutý odchod.

## Souvislosti
- `doc-dochazka-rezie-druh-zaznamu-preklopen-na-praci` — samotný převod, počty, zálohy
- `doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie` — „Režie nikdy nebyla činnost"
- `doc-dochazka-opravy-jen-prace-cesta-pauza-absence-patri-do-spravy` — kolo z 1. 9.

