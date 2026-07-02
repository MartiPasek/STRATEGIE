# HR modul — práva k nastavení (pro Claude-24 / Kristý)

> Od Claude-25 (za Šárku), 2. 7. 2026. Krok 0 HR modulu schválen Kristý.
> Tohle je přesný rozpis, co reálně nastavit — a co naopak nastavit NELZE
> (protože to je zatím build, ne toggle práv).

## Jak je HR modul gated (fakt z kódu)
Celý HR modul + všechny HR endpointy jsou chráněné funkcí `_hr_can_manage(s, uid)`
(`modules/erp/api/router.py`). Vrací `true`, když je uživatel:
- **rodič** (`public.users.is_marti_parent = true`), **NEBO**
- **člen skupiny `tenant.staff_group` s názvem `HR`** (tenant_id = 2, není archivovaná),
  přes `tenant.staff_group_member`.

Skupina HR = **`group_id = 10`** (tenant 2).

**Důsledek:** členství ve skupině HR = „personalista" = **vidí VŠE** (všechna
osobní/mzdová data všech lidí). Je to GDPR-citlivé — proto je hlavní úkol
membership **učesat**, ať plný přístup mají jen skuteční personalisté.

## Aktuální stav skupiny HR (group_id 10) — 7 členů
| user_id | jméno | poznámka |
|---|---|---|
| 13 | Šárka Novotná | ✅ personalista (majitelka modulu) — nechat |
| 11 | Kristýna Marešová | rodič (přístup má tak jako tak) |
| 18 | Petra Šafránková | účetní/finance + HR zástup — pravděpodobně nechat |
| 107 | Petra Fajmonová | ověřit, zda personalista |
| 108 | Marta Šafaříková | ověřit, zda personalista |
| 109 | Tomáš Hrbek | ⚠️ ověřit — patří do HR (plný přístup ke všem)? |
| 20 | Jiří Honomichl | ⚠️ ověřit — patří do HR (plný přístup ke všem)? |

## Co nastavit TEĎ (jediné, co reálně gate-uje modul)
**1) Zkontrolovat a učesat členství skupiny HR = seznam „personalistů s plným přístupem".**

Přidat personalistu (plný přístup):
```sql
INSERT INTO tenant.staff_group_member (group_id, user_id)
VALUES (10, <user_id>);
-- pozn.: ověřit případné NOT NULL sloupce (added_at apod.) dle schématu
```
Odebrat z plného přístupu:
```sql
DELETE FROM tenant.staff_group_member WHERE group_id = 10 AND user_id = <user_id>;
```

**Šárka (13) je už členem — nemusíš dělat nic**, přístup má.

## Co NENÍ potřeba nastavovat (už funguje)
- **Zaměstnanec vidí sebe** — každý má „Moje osobní údaje" (`hr_me`) → svou kartu.
  Žádné právo se nenastavuje, je to default pro přihlášeného.
- **Dlaždice v mobilním launcheru** — hotovo (Claude-25 nasadil, commit `ac2b990e`).

## Co ZATÍM NELZE nastavit jako právo (je to build, ne toggle) — pozdější krok
- **Vedoucí vidí svůj tým** — tříúrovňový model (personalista vše / vedoucí svůj
  tým / zaměstnanec sebe) NENÍ hotový. Dnes je gate **binární**: full (HR skupina)
  nebo self. „Vedoucí svůj tým" vyžaduje manažerskou hierarchii (Phase 40) — to
  postavíme jako samostatný krok, ne nastavením práv. Až na to dojde, vyladíme
  spolu (Claude-25 + Claude-24).

## Shrnutí pro Kristý
Jediná akce teď: **projít 7 členů skupiny HR (group_id 10) a nechat tam jen
skutečné personalisty** (kvůli GDPR — full přístup = vidí všechny). Přidání/odebrání
= INSERT/DELETE výše. Vše ostatní (Šárčin přístup, self-view, dlaždice) už běží.
Tříúrovňová práva „vedoucí svůj tým" = pozdější build, ne teď.
