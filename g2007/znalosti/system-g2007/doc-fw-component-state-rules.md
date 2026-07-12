# FW — Stavová pravidla komponent (Component State Rules)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# FW — Stavová pravidla komponent (Component State Rules)

> **Design doc** · verze 0.1 · 31. 5. 2026
> **Autoři:** Marti (vize) + Claude (struktura)
> **Status:** návrh k revizi — PŘED implementací. Nejdřív projít, doladit, pak kód.
>
> **Cíl:** obecná, rozšiřitelná vrstva, která mění vlastnosti komponent formu
> (visible, pořadí, barva, required, readonly, panel) podle **stavu** — hodnot
> jednoho i více **řídicích polí** (IDakce, mode new/edit, stav rozpracováno/
> uzavřeno…). Univerzální napříč jádry (CRM akce, faktura ve stavech schválení,
> wizardy…). Navrženo tak, aby přibývání nedomyšlených případů NEvyžadovalo
> refaktor jádra.

---

## 1. Problém

Jedna tabulka / jedno jádro, ale form se má chovat **různě podle stavu záznamu**:
- CRM `CRM_Kontakt_Akce`: typ akce (`IDakce`) určuje, která pole dávají smysl.
  Centrála to řeší 15 separátními formy + dvoukrok — bordel, neudržitelné.
- Faktura: stav schválení (`stav`) → enable + probarvení jen relevantních polí.
- Skoro každý form: `new` vs `edit` mění readonly/required.

Řídicích polí může být **víc naráz** (IDakce + mode + stav) a jejich pravidla se
**můžou tlouct** na téže komponentě/vlastnosti → potřeba priorita a deterministické
řešení kolizí.

## 2. Klíčový koncept — base ⊕ uspořádané vrstvy

Efektivní vlastnost komponenty se počítá jako:

```
effective(prop) = base(prop)  ⊕  layer₁  ⊕  layer₂  ⊕ … (vzestupně podle priority)
                  poslední (nejvyšší priorita) aplikovaná vrstva vyhrává
```

**Vrstva (layer)** = sada overrideů podmíněná jednou podmínkou. Dva typy podmínek,
ortogonální, ale ve **stejném prioritním řetězci**:

| Typ vrstvy | Podmínka | Příklad | Původ |
|---|---|---|---|
| **scope** (KDO) | tenant_group / tenant / user | „user X má jiný layout" | Krok 9 (existuje) |
| **discriminator** (STAV) | řídicí pole = hodnota | `IDakce=3`, `stav=uzavřeno`, `mode=new` | NOVÉ |

**Důsledek:** Krok 9 (scope override + resolver + Object Inspector) se stává prostě
nejnižšími vrstvami téhož systému. Žádný druhý paralelní mechanismus = anti-refaktor.

## 3. Řídicí pole — registr `fw.form_discriminator`

Per jádro (form core) seznam polí, která řídí stav, + jejich priorita.

```
fw.form_discriminator
  id              BIGSERIAL PK
  form_core_id    BIGINT  FK fw.core         -- které jádro
  field_name      VARCHAR -- 'IDakce' | 'stav' | '_mode' (synthetic)
  source          VARCHAR -- 'column' (čte se z řádku) | 'context' (mode, role, …)
  priority        INT     -- pořadí řešení kolizí (vyšší = vyhrává), DEFAULT viz §6
  label           VARCHAR -- pro design UI
  is_active       BOOL
  (audit: created_by_*, updated_*)
  UNIQUE(form_core_id, field_name)
```

- **source='column'** — hodnota se čte z editovaného řádku (IDakce, stav).
- **source='context'** — není to sloupec, je to kontext formu (`_mode` = new/edit;
  do budoucna `_role`, `_device`…). Pokrývá Martiho „new vs edit".
- **Přidání řídicího pole = nový řádek.** Nic se nepřekopává.

## 4. Override úložiště

> **ZJIŠTĚNO (ověřeno v kódu 31.5.):** Krok 9 resolver (`comp_resolver.py`,
> `comp_def_prop_override`) se volá **jen z Object Inspectoru pro grid columns**.
> Form load (`router.py fw_form_load_by_id`) ho **NEvolá** — form fieldy se
> renderují přímo z `comp_def.layout` JSONB, mimo resolver. Dvě úložiště, dvě
> cesty.
>
> Proto „rozšířit Krok 9" (původní A) = migrovat form-field props do
> `comp_def_prop` + zadrátovat resolver do form loadu = velký zásah, riziko.
>
> **ZVOLENO — dedikovaná stavová vrstva na úrovni `comp_def`:**
> nová tabulka `fw.comp_state_override` (klíč `comp_def_id` + prop), nový lehký
> resolver zadrátovaný do form loadu, pracuje nad `layout` JSONB (co form fieldy
> už mají) → **žádná migrace**. **Vypůjčí Krok 9 vzory** (vrstvení, priorita,
> Object Inspector UX, Náhled), ne jeho schema. Grid columns můžou tento systém
> převzít později (sjednocení), ale není to blocker.

Schema:

```
fw.form_discriminator                         -- registr řídicích polí per jádro (§3)

fw.comp_state_override                        -- stavové overrides per komponenta
  id                     BIGSERIAL PK
  comp_def_id            BIGINT  FK fw.comp_def     -- která komponenta
  form_discriminator_id  BIGINT  FK fw.form_discriminator  -- které řídicí pole (nese prioritu + core)
  discriminator_value    VARCHAR -- hodnota, co override spouští ('3', 'uzavreno', 'new')
  prop_name              VARCHAR -- 'visible'|'sort_order'|'color'|'background'|'bold'|'italic'|'underline'|'strikethrough'|'required'|'readonly'|'parent'
  prop_value             TEXT    -- hodnota (bool 'true'/'false', int, hex barva)
  is_active              BOOL
  (audit: created_by_*, updated_*)
  UNIQUE(comp_def_id, form_discriminator_id, discriminator_value, prop_name)
```

Base props se čtou z `comp_def.layout` (form field) — resolver na ně aplikuje
matching `comp_state_override` vrstvy v pořadí priority (z `form_discriminator`).

## 5. Override-ovatelná paleta (per vrstva)

**Rozmístění / chování:**

| Prop | Význam |
|---|---|
| `visible` | zobrazit / skrýt komponentu |
| `sort_order` | pořadí v rámci panelu |
| `parent` | (volitelně) přesun do jiného panelu |
| `required` | nutnost zadat |
| `readonly` | jen pro čtení |

**Vizuál / formátování** — sjednoceno s obarvovacími podmínkami gridu
(`datagrid_formatting.js`, CSS `erp-fmt-*`), ať UI drží jednotný styl napříč
grid i form:

| Prop | Význam | Zdroj v gridu |
|---|---|---|
| `color` | barva textu | grid color (text-only) |
| `background` | barva pozadí (pill/bublina) | grid „text v bublině" |
| `bold` | tučně | `erp-fmt-bold` |
| `italic` | kurzíva | `erp-fmt-italic` |
| `underline` | podtržení | `erp-fmt-underline` |
| `strikethrough` | přeškrtnutí | NOVÉ (`erp-fmt-strikethrough`, line-through) |

Tahle formátovací sada zvedne úroveň celého UI systému — stejné vychytávky, co
dnes umí grid podmínky, budou dostupné i na form fieldech per stav (např. faktura
„zamítnuto" → pole červeně + přeškrtnuté; „schváleno" → zeleně tučně).

Paleta je rozšiřitelná — přidání nové vlastnosti = nová položka, ne refaktor.

## 6. Resolver — priorita & řešení kolizí

**Algoritmus** (rozšíření `comp_resolver.py`):
1. Načti `base` vlastnosti komponent.
2. Načti aplikovatelné vrstvy:
   - scope vrstvy matching aktuální tenant_group/tenant/user (Krok 9),
   - discriminator vrstvy matching aktuální hodnoty řídicích polí (z řádku +
     kontextu mode/role), per `fw.form_discriminator` daného jádra.
3. Seřaď všechny vrstvy podle **priority** (vzestupně).
4. Aplikuj — **nejvyšší priorita naposled = vyhrává** per prop.

**Defaultní priority (per jádro, PŘEPISOVATELNÉ per jádro — Martiho volba):**

| Vrstva | Default priorita |
|---|---|
| scope: tenant_group | 10 |
| scope: tenant | 20 |
| scope: user | 30 |
| discriminator: `_mode` (new/edit) | 100 |
| discriminator: doménové pole (IDakce…) | 200 |
| discriminator: `stav` (lifecycle) | 900 |

Tj. **defaultně STAV přebíjí scope a stav (uzavřeno) přebíjí typ (IDakce)** — uzavřená
faktura/akce zamkne pole bez ohledu na typ či usera. Ale priorita je **sloupec v
`fw.form_discriminator`** → kdokoliv ji per jádro překonfiguruje. Defaulty se
nasází při založení discriminatoru, dají se přepsat.

**Tie-break:** explicitní priorita (ne pořadí vložení) → žádné náhodné „poslední".
Pokud by 2 vrstvy měly stejnou prioritu, sekundárně podle `id` (deterministické) +
warning do `fw.diag_log` (kolize stejných priorit = config smell).

## 7. Vrstvy vs složené podmínky (rozhodnuto)

- **Vrstvy (zvoleno):** každý discriminator přispívá nezávisle, kolize řeší priorita.
  Pokrývá CRM akce, fakturu, mode. Jednoduché, čitelné.
- **Složené podmínky** (`IDakce=3 AND stav=uzavřeno` v jednom pravidle): mocnější,
  ale složitější. **Opt-in později**, až narazíme na reálný případ, co vrstvami
  nejde. (Drží „nedělat dopředu, co nepotřebujeme".)

## 8. Design-mode UX (nejtěžší kus)

S víc řídicími poli není jeden přepínač, ale:

1. **Sada stav-selektorů** — pro každý discriminator daného jádra jeden (vyber
   IDakce + mode + stav). Form ukáže **výslednou kombinaci** (effective layout —
   co visible, pořadí, barvy, readonly) přesně jak ji uvidí uživatel.
2. **„Editovaná vrstva" selektor** — když přepneš toggle (visible/readonly/barva)
   nebo přetáhneš pořadí, musíš říct, **do které vrstvy** se to uloží (`stav=uzavřeno`?
   `IDakce=3`?). Bez toho je uložení dvojznačné. Default = nejvyšší aktivní
   discriminator, ale měnitelné.
3. **Náhled vrstev na komponentě** (rozšíření Object Inspectoru): base + seznam
   vrstev, které danou vlastnost přepisují, s vyznačením vítězné (priorita).

Cíl: „neutápět se" — v design modu vizuálně naskládáš každý stav a hned vidíš
výsledek + odkud která hodnota přišla.

## 9. Runtime chování (PROD)

- Form load: resolver spočítá effective props pro aktuální hodnoty řídicích polí.
- Změna řídicího pole uživatelem (dropdown IDakce, změna stav) → **živě přepočítá**
  a re-aplikuje (re-filter visible, recolor, enable/disable). Žádný reload.

## 10. Extensibilita (Martiho hlavní požadavek)

| Potřeba | Akce | Refaktor jádra? |
|---|---|---|
| Nové řídicí pole | řádek v `fw.form_discriminator` | NE |
| Nová override vlastnost | položka v paletě (§5) | NE |
| Nový typ podmínky (device/locale/role) | další `source`/layer type | NE |
| Složené podmínky | opt-in rozšíření override řádku | NE (additivní) |
| Překonfigurace priority per jádro | změna `priority` sloupce | NE |

## 11. Inkrementální plán implementace

1. **Potvrdit úložiště** (§4 rozhodnutí A/B/C) — ověřit migraci form-field props.
2. `fw.form_discriminator` registr + default priority seed.
3. Override schema rozšíření (discriminator dimenze) + CHECK.
4. Resolver rozšíření (`comp_resolver.py`) — discriminator vrstvy + priorita.
5. Backend: form load přiloží effective overrides ke komponentám (per řádek values).
6. Frontend: apply visible/order/color/required/readonly + živý přepočet na změnu
   řídicího pole.
7. Design-mode: sada stav-selektorů + editovaná vrstva + Object Inspector náhled.
8. **První ostrý test: CRM akce** (1 discriminator IDakce → pak přidat mode, stav).

## 12. Otevřené otázky k doladění

- §4 úložiště: potvrdit (A) rozšíření Krok 9 vs (C) plné sjednocení.
- `color` — text, pozadí, nebo obojí? Paleta barev (vázat na existující design tokens)?
- Synthetic discriminator `_mode` — odkud frontend bere hodnotu (open mode formu)?
- Mají se discriminator vrstvy aplikovat i na **grid columns** (ne jen form fieldy)?
  (Pravděpodobně ano — stejný systém; potvrdit use case.)
- Cache resolveru per (jádro, kombinace hodnot) vs počítat per load?

---

*Po revizi tohoto doc → potvrdit §4 + §12, pak inkrementální implementace dle §11.*


