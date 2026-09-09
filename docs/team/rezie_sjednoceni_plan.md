# Sjednocení „Režie" → „Rezie" — připravený plán (čeká na pokyn Peti)

> Claude‑26 pro Peťu, 20. 7. 2026. **Rozhodnutí Peti:** kanonický tvar je **`Rezie`
> bez diakritiky** a **ukládá se do kolonky zakázka** (`att_entry.project_ref`), tak
> jak to bývalo v Centrále — *„je potřeba ji vidět"*. **NENASAZOVAT** bez jejího pokynu.

## Stav dat (ověřeno 20. 7. 2026)

| Kde | Hodnota | Počet | Období | Zdroje (`source`) |
|---|---|---|---|---|
| `tenant.att_entry.project_ref` | `Režie` | 1 446 | 6. 6. – 20. 7. 2026 | import, manual, mobile_app, tablet |
| `tenant.att_entry.project_ref` | `Rezie` | 409 | 11. 6. – 20. 7. 2026 | manual_fix, mobile_app, notif_confirm |
| `tenant.work_alloc.project_ref` | `Rezie` | 403 | — | — |
| `tenant.work_alloc.project_ref` | (prázdné) | 95 | — | — |
| `tenant.vyroba_work.zakazka_ref` | žádná režie | 0 | — | — |

**Důležité (oprava dřívějšího tvrzení):** filtr `router.py:24755`
(`LOWER(project_ref) <> 'rezie'`) čte `work_alloc`, kde je jen bezdiakritická
varianta → **režijní hodiny do zakázek NEtečou**. Rozdíl v pravopisu tedy
zkresluje jen přehledy a filtrování, ne výkazy hodin.

## Původ obou tvarů

- **`Režie` s háčky** — jediné místo v repu, `router.py:24901`
  (`"proj": ("Režie" if rezie else …)`) = **import z Centrály**. `source` se odvodí
  z `EC_Dochazka.LoginFrom` (`router.py:24896`): D→tablet, C→manual, A→mobile_app,
  jinak import. Odtud ta čtveřice zdrojů.
- **`Rezie` bez háčků** — nikde není literál; je to **číslo zakázky z Heliosu**
  (`tenant.zakazka`, typ REZIE). Doteče přes výběr zakázky v mobilu nebo přes
  opravu záznamu.

## Co udělat (3 kroky, v tomto pořadí)

### 1) Jednorázová oprava dat — přes schvalovací banner
```sql
UPDATE tenant.att_entry
   SET project_ref = 'Rezie', updated_at = now()
 WHERE tenant_id = 2 AND TRIM(project_ref) = 'Režie';   -- ~1 446 řádků
```
Kontrola po zápisu: `SELECT TRIM(project_ref), count(*) FROM tenant.att_entry
WHERE tenant_id=2 AND lower(TRIM(project_ref)) LIKE 're%ie' GROUP BY 1;`
→ má zbýt jediný řádek `Rezie`.

### 2) Vstupy — aby nová „Režie" už nevznikala
| # | Soubor:řádek | Dnes | Po opravě |
|---|---|---|---|
| a | `modules/erp/api/router.py:24901` | zapisuje `"Režie"` (import z Centrály) | zapisovat `"Rezie"` |
| b | `modules/erp/api/router.py:23507` | `_att_apply_work_selection` bere `project_ref` bez normalizace | normalizovat `režie/rezie` → `Rezie` |
| c | `modules/erp/api/router.py:19797` + `:19617` | stránka oprav docházky ukládá doslova, co je v poli | tatáž normalizace |

Pomocná funkce (jedno místo, ať se to nerozjede znovu):
```python
def _norm_zakazka(ref):
    """Režie se v číslu zakázky píše 'Rezie' (tvar z Heliosu i Centrály).
    Peťa 20.7.2026 — sjednoceno, ať filtry v přehledech chytají všechno."""
    r = (ref or "").strip()
    return "Rezie" if r.lower() in ("rezie", "režie") else r
```

### 3) Rozhodnutí, které ještě potřebuje potvrdit Marti
`router.py:23739` (checkin z mobilu) dnes režii **maže** (`project_ref = None`)
a značí ji jen typem `overhead`. To je Martiho návrh z 7. 6. („režie = práce bez
zakázky"). Peťa chce režii v kolonce zakázky **vidět**, což znamená tenhle guard
obrátit — proto **konzultovat s Marti**, ne měnit potichu.

Dokud se to nerozhodne, přehled „Docházka po zakázkách" může režii dopočítat
zobrazením (`CASE WHEN typ='Režie' AND project_ref IS NULL THEN 'Rezie'`), takže
Peťa ji uvidí i bez zásahu do checkinu.

## Co po sjednocení zkontrolovat
- `router.py:24755` a `:24673` — porovnání na `'rezie'`; po sjednocení sedí.
- `router.py:24894`, `:26419`, `scripts/migrate_dochazka.py:136` — detekce režie ze
  vstupu z Centrály (`zak.lower() == "rezie"`); beze změny OK.
- `dochazka-centrala.html:177` — kosmetika (obarvení řádku); stránka je určená ke smazání.
- Pozor na **mrtvé kopie**: `router.py.bak_*`, `router.py.TESTCOPY`,
  `_to_delete/_recover_router.py` — needitovat.
- `mobile.html` je **generovaný** z `mobile_parts/` — editovat partial + `python scripts/build_mobile.py`.

## Nesouvisející úklid (taky čeká na pokyn Peti)
Smazat nepoužitou stránku z prvního kola 20. 7.:
`apps/api/static/dochazka-centrala.html`, `modules/erp/api/dochazka_zakazky.py`,
route `/dochazka-centrala` + include routeru v `apps/api/main.py`.
Přehled dnes jede jako běžný framework grid (`dochazka.zakazky_vse_list`).
