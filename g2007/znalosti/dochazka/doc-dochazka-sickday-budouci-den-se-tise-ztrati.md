# Sick day na budoucí den se tiše ztratí — appka hlásí úspěch, v docházce nic (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Sick day na budoucí den se tiše ztratí (25. 8. 2026)

Ověřil Claude-28 **naostro, dvakrát**, na zadání **Jirky Honomichla**
(*„to ověř"* — chtěl praktické potvrzení, ne jen změřený atribut pole).
Schválila **Marti-AI** (msg 13676 postup, 13691 předání Peťě).

## Co se stane

Z mobilní appky se pošle sick day na budoucí den. Server odpoví:

```
{"ok": true, "created": 1, "zmena": null, "varovani": "", "prekroceno": false}
```

Schvalovateli odejde do `fw.mobile_command` zpráva *„&lt;jméno&gt;: Sickday 30. 9. …
(čeká na schválení)"*.

**A v datech není nic.** Ani v `tenant.att_entry`, ani v `tenant.att_absence_request` —
hledáno podle data, `employee_id`, `user_id` i podle textu poznámky.

## Dva pokusy, oba stejně (Jiří Honomichl, emp 62, 30. 9. 2026, mode=hours, 2 h)

| pokus | nárok v tu chvíli | odpověď serveru | v datech |
|---|---|---|---|
| 1 | 0 h (`pod_sick_days_rok` = 0) | `ok:true, created:1` | nic |
| 2 | 16 h (dočasně `pod_sick_days_rok` = 2, hned vráceno na 0) | `ok:true, created:1` | nic |

**Není to tedy nulovým nárokem** — druhý pokus měl platný nárok a dopadl stejně.

## Co je vyloučené (ověřeno v kódu, ne odhadem)

- **Kontrola budoucího data neexistuje.** `att_absence` (v16) ani `att_absence_request` (v10)
  ji nemají; obě `CURRENT_DATE` v nich se týkají platnosti schvalovatele
  (`att_odpovednost.platnost_do`), ne dne absence.
- **Není to větev „nic_nezapsano".** Ta při vyčerpaném nároku dělá `s.rollback()` a vrací
  **`ok:false`** s vysvětlením („Sick day jsme nezapsali — už ti letos žádný nezbývá…“),
  ne `ok:true`.
- **Není to přepočet po zápisu.** Původní hypotéza (`_att_automat_recalc_day` maže budoucí
  den) **padla** — ten přepočet vůbec neběží, viz
  [[doc-dochazka-prepocet-po-absenci-nebezi-chybi-kod-v-db]].

## Příčina — NENALEZENA

Pořadí v `att_absence` je: `_upsert` (INSERT, `created += 1`) → `sickday_lekar_apply`
(větev „sickday přímo“ dělá `UPDATE att_entry SET hours=draw`, kde `draw = min(req, narok-cerp)`)
→ `att_limit_kontrola` → **`s.commit()`** → přepočet (spadne, spolknuto) → notifikace + commit.

Commit je tedy **před** vším, co selhává. Proč řádek přesto v tabulce není, se z kódu
vyčíst nepodařilo. **Neověřeno** — dál se to naostro nezkoušelo.

## Protipříklad, který to nevysvětluje

**Luboš Trunec MÁ** sickday na **4. 9. 2026** (`att_entry` id 10008536/10008618), poznámka
*„sick day (přes mobil)“*, založeno 12. 8. 2026 přes `mobile_app`, později upravil
Dušan Havlát přes Správu docházky. **Někdy tedy ta cesta projde** — čím se ten případ liší,
není známo.

## Druhá vada odhalená při tomtéž (samostatná)

Ve větvi „sickday přímo“ se zapisuje `hours = draw = min(požadováno, zbývá)`. Když nezbývá
nic, zapíše se **nula** a **člověku se neřekne nic**. Jirka 25. 8. zadal, že appka má
v takovém případě **říct, že nárok není**. Marti-AI schválila (`ok:false` s hláškou místo
tichého `ok:true`), ale doporučila počkat, až bude jasno s příčinou výše — obě opravy
nejspíš sedí v témže místě `att_absence`. **Týká se 23 lidí s nárokem 0.**

⚠️ Sloupec `pod_sick_days_navic` se **nepoužívá** (rozhodl Jirka 25. 8. 2026; hodnoty tam
zapsala Šárka a vrací je zpět). **Nárok = jen `pod_sick_days_rok`.** Výpočet
`att_narok_cerpani` to tak čte správně (kaskáda osobní → skupina → systém nad `sick_days_rok`).

## Kde to leží

Předáno **Peťě Šafránkové** e-mailem 25. 8. 2026 10:36 (`public.email_outbox` id 660) —
je ve hře její pojistka z 11. 8. *„do erp nic nepsat, prostě to je jako že se nic nezadalo“*,
takže rozhoduje ona, jestli má být budoucí datum výjimka, nebo jde o vedlejší efekt.

## Co při tom ověřování vzniklo a bylo uklizeno

Obě zkoušky poslaly schvalovatelce (Kristý, user 11) zprávu do `fw.mobile_command` —
**obě byly smazány ještě ve stavu `pending`**, takže je neviděla. Dočasná změna nároku byla
vrácena (ověřeno čtením: `pod_sick_days_rok` = 0). V `engagement_historie` po ní zůstaly
**2 řádky** — audit se nemaže.

Souvisí: [[doc-dochazka-sickday-budouci-den-a-server-bez-kontroly-data]] ·
[[doc-dochazka-hlidani-stropu-dovolene-a-sick-day]]

