# Systém adresářů pro dokumenty — v2 (závazný design)

Stav: **schváleno** (Marti zadání + konzultace Marti-AI 18. 6. 2026). Vychází z modelu
Centrály `EC_OrgAdresare` + `EC_ZjistiAdresar_NEW`, přeneseno čistě do STRATEGIE.

## Princip
Neukládáme celé cesty v záznamech. **Konfigurace + resolver**: z *typu entity* (`sys_name`)
+ *ID záznamu* (+ volitelně řada) se složí kořen + podsložka. Každý přehled/modul má
svůj `dir_config`; typicky **podsložka podle ID věty → každý záznam má svou složku**.

```
\\192.168.30.11\data\podklady vyroba\VR12345\ZL
└────────── kořen (storage.root_path) ┘└ podsložka (subfolder_rule) ┘
```

## Závazné závěry z konzultace Marti-AI (18. 6. 2026)

1. **`dir_config` = first-class tabulka**, ne `comp_def` řádek (jiná dimenze, lifecycle,
   ACL). Reuse `data_source` jen pro kontext entity (odkud přichází záznamy → co je `entity_id`).
2. **Úložiště jako `dir_config_storage` (1:N)** od začátku, sloupec `role`
   (`primary` | `mirror` | `archive`). MVP seeduje jen `primary` + max. 1 `mirror`,
   ale model je 1:N → resolver nevětví na „má copy, nebo ne", jen fetchne řádky.
3. **Mirror = best-effort + povinný audit při selhání.** Primár = transakce (projde/ne).
   Mirror async záměr; selhání → `dir_access_log` `write_mirror_failed` + důvod (tiché
   selhání je horší než žádný mirror). Data jen na mirroru (`role!='primary'`, žádný
   primár) → selhání = chyba.
4. **ACL scope vynucován v ADAPTERU, ne jen v UI.** `acl_scope ∈ self | hr | business |
   parent | confidential`. UI skrývání = UX; enforcement v adapteru = bezpečnost
   (chrání i přímé API / autonomní AI přístup). `confidential` = HR+parent + audit na
   každý read.
5. **`dir_access_log` append-only**, povinný pro všechny zápisy; pro `hr`/`self`/
   `confidential` i pro čtení. (`business` = log jen zápisy, čtení je běžný provoz.)
6. **Výjimky = data (`dir_config_rule`)**, handlery (ZL/DL/Prohlášení) = kód.
   Engine ví o existenci podmíněných pravidel, neví co jsou zač (`org=327 → jiný kořen`
   = řádek, ne `if junker`). Hranice předčasného zobecnění: 2+ výjimky → engine; 1 →
   pojmenovaný handler OK.
7. **Migrace: jen aktivní/relevantní podmnožina** z `EC_OrgAdresare` (ne všech 94 slepě
   = tech dluh). Mapování `SysNazev` → `sys_name` (snake_case, bez lomítek/diakritiky).
   UNC kořeny **zachovat** (`backend='eurosoft_unc'`, kontinuita). Cloud verze = nový
   `dir_config` záznam, ne přepis starého (překlopení do cloudu = separátní rozhodnutí Martiho).
8. **Hranice Marti-AI** (sama si určila):

   | Scope | AI read | AI write | Poznámka |
   |---|---|---|---|
   | `business` | ✅ | ✅ | zakázky, výměry, generované smlouvy = pracovní materiál |
   | `sablona` | ✅ | ✅ | generuje šablony, ukládá výstupy |
   | `hr` | ⚠️ jen na task | ❌ | osobní karty/mzdové doklady — nikdy autonomně |
   | `self` | ❌ | ❌ | osobní složky lidí — nevidí, nezakládá |
   | `confidential` | ❌ | ❌ | vyžaduje parent gate (jako hard delete) |

   Adapter: actor=`persona` + scope `self`/`confidential` bez `parent_override` v requestu
   → `acl_denied` (ne tichý fail). Princip: *„nejde o to, jestli to technicky projde —
   jde o to, co si člověk myslí, že AI vidí. Asymetrie ochrany = základ důvěry."*

## Datový model (tenant.* — vlastní Marti-AI, GRANT strategie)

**`tenant.dir_config`** — id, tenant_id, sys_name, short_code, series('' default),
name, subfolder_rule (`id`|`cislo_zakazky`|`poradove_cislo`|`cislo_org`|`user_id`|`none`),
data_source_id (nullable), acl_scope, doc_series_id (nullable), active, created_at,
updated_at. UNIQUE (tenant_id, sys_name, series).

**`tenant.dir_config_storage`** — id, tenant_id, dir_config_id, role
(`primary`|`mirror`|`archive`), backend (`eurosoft_unc`|`cloud`), root_path, active,
created_at. UNIQUE (dir_config_id, backend, root_path).

**`tenant.dir_config_rule`** — id, tenant_id, dir_config_id, condition_type
(`org`|`date_before`|`date_from`|…), condition_value, override_field
(`root_path`|`subfolder_rule`|`backend`|…), override_value, priority, active.

**`tenant.dir_access_log`** (append-only) — id, tenant_id, actor_type
(`user`|`persona`|`system`), actor_id, dir_config_id, entity_id, resolved_path,
action (`read`|`write`|`list`|`delete`|`write_mirror_failed`), acl_scope, ts, ok,
error_message.

## Resolver + adapter (Fáze A backend)
- `resolve(sys_name, entity_id, series='') → {config, storages[], sub, related[]}`:
  konfigurace z DB; aplikuje `dir_config_rule` (match podle podmínky); speciální
  handlery (ZL/DL/Prohlášení) jako pojmenované strategie; DirectDir (`subfolder_rule='none'`)
  = jen kořen; strukturovaná chyba místo `'ERR'`.
- **Storage adapter** — jednotné `write/read/list/exists/delete` nad backendy:
  `eurosoft_unc` (přes MCP `eurosoft_file_*`) a `cloud` (lokální/objektové úložiště
  STRATEGIE). Před každou operací **ACL check** + zápis do `dir_access_log` dle pravidel.
  Zápis: primár (transakce) → mirror(y) best-effort + audit při selhání.

## Fázování
- **Fáze A** — DDL (4 tabulky + GRANTy) → resolver + adapter → seed relevantní podmnožiny
  z `EC_OrgAdresare` (UNC zachovat). Napojení `doc_template` generátoru (cíl = resolve).
- **Fáze B** — UI souborový panel (typ adresáře + ID záznamu → soubory z resolveru;
  u zakázek i `related[]` jako záložky). Per-modul/přehled napojení.
- **Fáze C** — cloud backend (pokud Marti rozhodne překlopit část do cloudu) + archive role.

— Claude (id=23) + Marti-AI, 18. 6. 2026
