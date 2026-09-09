# Odpovědnost za lidi — jeden strom skupin, dvě agendy (docházka + volno)

> **Výchozí, univerzální model** rozdělení lidí a odpovědnosti za ně. Rozhodla Peťa
> (Petra Šafránková, vedoucí nákupu a logistiky) + schvaluje Marti, 22. 7. 2026.
> Nahrazuje čtyři roztříštěná dělení. Jediný zdroj pravdy „kdo za koho zodpovídá" —
> pro docházku, schvalování volna i personální agendu.

## Proč

Na otázku „patří tenhle člověk do výroby, nebo kanceláře, a kdo za něj zodpovídá"
systém dnes odpovídá na **čtyřech místech a pokaždé jinak** (`att_fix_scope`,
`_ABSENCE_SEGMENTY`, `att_approver_group`, `cond_group`). Proto vypadávají lidé
jako Zuzana Duspivová (jeden okrajový post ji přebil do výroby). Sjednocujeme do
jednoho stromu a jedné tabulky odpovědnosti.

## Datový model

- **`staff_group.parent_id`** (nový, nullable) — strom nad stávajícími personálními
  skupinami. Dva kořeny: **KANCELÁŘE**, **VÝROBA**.
- **`tenant.att_odpovednost`** (nová) — kdo za koho zodpovídá, per agenda:
  - `agenda` — `dochazka` / `volno` (rozšiřitelné, např. `prescasy`)
  - `uroven` — `skupina` / `osoba`
  - `skupina_id` (u úrovně skupina) / `user_id` (u úrovně osoba = koho se týká)
  - `odpovedny_user_id` — kdo kontroluje / schvaluje
  - `je_zastupce` — zástup (schválí i on, když hlavní chybí)

## Kaskáda (první jasná odpověď vyhrává)

1. **osobní výjimka** (`uroven='osoba'` pro toho člověka)
2. **odpovědný jeho podskupiny**, není-li → **kořen** (Kanceláře/Výroba)
3. **fallback**

U konkrétního člověka jde odpovědného **ručně přepsat** (osobní výjimka) — v UI
u karty člověka, přednastaveno zděděnou hodnotou (ukáže „zděděno od …").

## Strom

```
KANCELÁŘE        Vedení · Nákup · Finance · Obchod · HR · IT
VÝROBA           Výroba · Zkušebna · PLC · VP · E-plan
```

## Výchozí obsazení (22. 7. 2026)

### Kontrola docházky

| skupina | kontroluje |
|---|---|
| KANCELÁŘE | Peťa Šafránková + Michelle Šafránková |
| └ IT | Kristýna Marešová (výjimka) |
| VÝROBA | Dušan Havlát + Michaela Hladíková |
| fallback | Peťa (předěleguje) |
| osobní výjimka | Marti Pašek → Peťa |
| dohled nad celkem | Jiří Honomichl (ponechané „vše" — vidí na všechny) |

### Schvalování volna

| skupina | schvaluje |
|---|---|
| KANCELÁŘE (Vedení, Nákup, Finance, Obchod, HR) | Peťa Šafránková |
| └ IT | Kristýna Marešová (výjimka) |
| VÝROBA | Dušan Havlát (zástup Marek Honal) |
| └ VP (Vedoucí projektů) | **Jiří Veverka** (výjimka pod výrobou) |
| fallback | Peťa (předěleguje) |
| osobní výjimka | Marti Pašek → **schvaluje si sám** |

**Pozor na dva Pašky:** Marti (jednatel, `users.id=1`) ≠ Martin Pašek (kolega VP).

## Fallback — kdo tam reálně spadne (vyřešeno s Peťou 22. 7.)

Aktivní lidé mimo všech 11 skupin:

| kdo | řešení |
|---|---|
| **Brigádník Saxana** (úklid, 252 záznamů) | osobní výjimka → **Peťa** (úklid patří pod ni), docházka i volno |
| **Klára Vlková** (prokurista, nepíchá) | ponechat na **fallbacku (Peťa)** — v praxi ji nikdo neřeší, ale kdyby jí něco naskočilo, uvidí to Peťa (pojistka). Tvrdé „nikdo" schválně NE — chyba by pak nešla nikam. |
| Marti Pašek | už kryto osobní výjimkou (docházka → Peťa, volno → sám) |
| Demo Uživatel, Marti-AI | testovací/systémové — ignorovat |

## Co model NAHRAZUJE a co NE

**Nahrazuje** (4 místa, stejná otázka): `att_fix_scope`, `_ABSENCE_SEGMENTY`,
`att_approver_group`, `cond_group`.

**Nechává být** (jiná otázka): `org_post`+`resolve_role` (nadřízenost, role),
`work_mode` (úvazek/dny), `att_kategorie` (fond, přesčasy), `vyroba_cinnost.kind`
(nabídka činností). Samotné `staff_group_member` zůstává — jen dostane strom.

## Zavedení (vratné, po krocích)

1. `staff_group.parent_id` + `att_odpovednost` + resolver `resolve_odpovedny(agenda, člověk)` — jen DB
2. **Docházka**: `_att_fix_scope_emps` / `_att_fix_editors_for_emp` na resolver;
   `att_fix_scope` nechat jako zálohu → pouštět skupinu po skupině, kdykoli couvnout
3. **Volno**: `resolve_approvers` (Jirka) přepnout na tentýž resolver
4. Editační obrazovky (strom + pole u člověka)

## Stav

Návrh odeslán Martimu ke schválení (22. 7.). **Nenasazeno.** Po schválení
a nasazení zapečetit finální verzi do G2007, oblast `dochazka`.
