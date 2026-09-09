# Strom skupin — návrh v2 (po Martiho připomínkách)

> **Od:** Peťa Šafránková (připravil Claude‑26) · **22. 7. 2026**
> Navazuje na návrh z 21. 7. Marti schválil směr a doplnil požadavky — zapracováno níže.
> **Stav: NÁVRH, NENASAZENO.**

## Co Marti schválil

- **Dva kořeny: KANCELÁŘE a VÝROBA** ✅
- pod nimi **stávající podskupiny** (Vedení, Nákup, Finance… / Výroba, Zkušebna, PLC…)
- k podskupinám **přiřazení lidé** a k nim **kontrolující / schvalující osoby**
- **navíc: musí jít ručně přepsat** kontrolující/schvalující osobu **u konkrétního
  člověka** (výjimka nad rámec skupiny)

## Jak to postavíme

### 1. Strom — `staff_group.parent_id`

```sql
ALTER TABLE tenant.staff_group ADD COLUMN parent_id bigint
    REFERENCES tenant.staff_group(id);
```

Aditivní, nic nerozbije. Vznikne přesně strom z náhledu:

```
KANCELÁŘE     Vedení · Nákup · Finance · Obchod · HR · IT
VÝROBA        Výroba · Zkušebna · PLC · VP · E-plan
```

Lidé jsou v podskupinách už dnes (`staff_group_member`).

### 2. Odpovědnost — jedna UNIVERZÁLNÍ tabulka, dvě úrovně

Peťa 22. 7.: *„toto nastavení bude výchozí, mělo by být univerzální."* Tedy **jeden
mechanismus pro všechny agendy** (kontrola docházky, schvalování volna, později
přesčasy) — ne zvláštní řešení pro každou. Jedna tabulka, jeden resolver, jen se
liší hodnota `agenda`.

`tenant.att_odpovednost`:

| sloupec | význam |
|---|---|
| `agenda` | `dochazka` / `volno` (později `prescasy`) |
| `uroven` | `skupina` / `osoba` |
| `skupina_id` | u řádku na skupině |
| `user_id` | u řádku na osobě = **koho se výjimka týká** |
| `odpovedny_user_id` | kdo kontroluje / schvaluje |
| `je_zastupce` | zástup (schválí i on, když je hlavní nepřítomen) |

- **řádek na SKUPINĚ** = výchozí pro celou skupinu, **dědí se na podskupiny**
- **řádek na OSOBĚ** = ruční výjimka, **přebíjí skupinu** — přesně to, co chce Marti

### 3. Kdo za koho zodpovídá — kaskáda

Funkce `resolve_odpovedny(agenda, člověk)`, první jasná odpověď vyhrává:

1. **osobní výjimka** (řádek `uroven='osoba'` pro toho člověka) →
2. **odpovědný jeho podskupiny**, když tam není → nahoru na **kořen** (Kanceláře/Výroba) →
3. **fallback**

Takže: Dušan se nastaví jednou na VÝROBU, Peťa jednou na KANCELÁŘE, výjimka (IT →
Kristýna) na podskupině, a jednotlivec (Duspivová → Peťa) jako osobní výjimka.

Výchozí obsazení kontroly docházky (Peťa 22. 7.):

| skupina | kontrola docházky |
|---|---|
| KANCELÁŘE (kořen) | **Peťa Šafránková + Michelle Šafránková** |
| └ IT | Kristýna (výjimka) |
| VÝROBA (kořen) | Dušan Havlát + Michaela Hladíková |

### 4. Kde se to edituje

- **Správa stromu** (rodiče/HR): přesun podskupin, přiřazení lidí, u skupiny
  nastavit odpovědného pro docházku / volno.
- **U konkrétního člověka**: dvě pole — *„Kontrolu docházky řeší"* a *„Volno
  schvaluje"*. Přednastavená **zděděnou** hodnotou (ukáže se *„zděděno od
  KANCELÁŘE"*), přepínatelná na konkrétní osobu = založí osobní výjimku.

## Napojení (vratné, po krocích)

1. `parent_id` + tabulka `att_odpovednost` + funkce `resolve_odpovedny` — jen data/DB
2. **Kontrola docházky**: `_att_fix_scope_emps` / `_att_fix_editors_for_emp`
   přepnout na resolver. `att_fix_scope` nechat jako zálohu → pouštět skupinu po
   skupině, kdykoli couvnout.
3. **Schvalování volna**: `resolve_approvers` (Jirka) přepnout na tentýž resolver.
4. Editační obrazovky (strom + pole u člověka).

## Rozhodnuto 22. 7.

- **Michelle Šafránková** = spolu‑kontrolorka docházky s Peťou (Kanceláře) ✅
- model je **univerzální** — jedna tabulka pro všechny agendy ✅
- **Jiří Honomichl (Jirka)** si nechává „vše" = dohled nad celkem (vidí a smí
  opravit kohokoli), pro případ potřeby ✅
- **Fallback** = **Peťa** (kdo propadne mimo skupinu i výjimku, uvidí Peťa a přiřadí dál) ✅
- **Osobní výjimka: Marti Pašek → Peťa** pro docházku i dovolenou. Marti není
  v žádné skupině, ale docházku aktivně píchá (175 záznamů, 2 žádosti o dovolenou),
  takže dostane osobní výjimku — jeho docházku i volno řeší Peťa. (Ověřeno 22. 7.:
  Klára Vlková docházku nepoužívá vůbec → žádné krytí nepotřebuje.)

## Co to nahradí (a co ne)

Včera jsme napočítali **9 různých způsobů**, jak se dnes lidé dělí do skupin.
Ne všechny odpovídají na tutéž otázku — proto se nahradí jen část:

**Sjednotí se (4)** — všechny odpovídají na „kam patří + kdo za něj zodpovídá":

- `att_fix_scope` — kontrola docházky (dnes org podstrom natvrdo v kódu)
- `_ABSENCE_SEGMENTY` — segmenty v plánu (dnes napevno psaný seznam v kódu)
- `att_approver_group` — schvalování volna (Jirka)
- `cond_group` — podmínky (už dnes čte `staff_group`, jen ploše)

**Zůstávají (5)** — odpovídají na jinou otázku, míchat by se rozbilo:

- `org_post` + `resolve_role` — kdo je čí nadřízený, kdo drží roli
- `work_mode` — úvazek, dny v týdnu (mzdová konfigurace)
- `att_kategorie` — dopichávat fond, bez přesčasů (pravidla)
- `vyroba_cinnost.kind` — které činnosti se komu nabídnou
- `staff_group_member` sám o sobě zůstává — jen dostane strom nad sebou

## Kdo to postaví

Model je **univerzální a výchozí** (jedna `att_odpovednost` + resolver pro docházku
i volno). Dotýká se Jirkova modulu schvalování (`att_approver*`). Návrh: agendu
**docházky** postavit nově na `att_odpovednost`, Jirkovo **volno** na tentýž
resolver přepnout ve druhém kroku po dohodě s ním — ať nejsou dva paralelní systémy.

## Poznámka

Ve znalosti `doc-dochazka-schvalovani-dovolene` je uvedeno, že Peťa schvaluje
nákupčím „ne jako jejich org nadřízená". **Neplatí** — Peťa je vedoucí oddělení
nákupu a logistiky. Opravit, ať na tom nikdo nestaví špatně.
