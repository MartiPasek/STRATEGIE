# Karta zaměstnance četla neexistující sloupec label — dlaždice Skupiny a formulář Přidat zaměstnance byly rozbité ode dne vzniku (opraveno 8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Karta zaměstnance četla neexistující sloupec `label` — dvě místa byla rozbitá ode dne vzniku (opraveno 8. 9. 2026)

Zapsal Claude-28 (Jirka Honomichl) **8. 9. 2026**, schválila Marti-AI (msg 15005).

## Co bylo špatně

Dvě adresy ERP karty zaměstnance četly `tenant.staff_group.label`. **Takový sloupec
v tabulce není** (má `id, tenant_id, name, icon, leader_user_id, deputy_user_id,
sort_order, archived, created_at, created_by, work_mode_id, parent_id`), takže obě
adresy na produkci vracely `UndefinedColumn`:

| adresa | co to lidem dělalo |
|---|---|
| `GET /app/hr/person-groups` | dlaždice „Skupiny a kvalifikace“ v kartě místo skupin vypisovala text chyby |
| `GET /app/hr/create-meta` | formulář „Přidat zaměstnance“ nenačetl **žádný** číselník — prázdné Skupiny, Společnost, Úroveň oprávnění, Typ smlouvy i Pozice, takže **nebylo možné založit zaměstnance** |

**Nerozbilo se to dodatečně — bylo to tak ode dne vzniku:** dlaždice od 21. 7. 2026
(commit `2dc08cc2`), formulář od 24. 7. 2026 (commit `838dbc19`).

## Proč to nikdo nenahlásil dřív

Obě místa chybu **spolkla do vlastního výstupu** — dlaždice ji zobrazila jako šedý text
a formulář jen zůstal prázdný. Žádná hlíška „nefunguje“, žádný prázdný stav
s vysvětlením. Kdo začne zaměstnance zakládat jinou cestou, vůbec na to nenarazi.

## Oprava

Nahrazeno čtením sloupce `name`, který v tabulce je a který už čet l mobil.
`COALESCE(NULLIF(TRIM(label),''), name)` → `name`. **Zdroj dat se neměnil** — zůstává
`tenant.staff_group`, změnil se jen název čteného sloupce. Sloupec `label` se do tabulky
**nedoplňoval** — není důvod přidávat sloupec kvůli chybnému odkazu (rozhodla Marti-AI).

## Poučení

- **Názvy sloupců nehádej ani neopisuj z podobné tabulky.** `tenant.job_position` sloupec
  `label` má, `tenant.staff_group` ne — a obě se v témže souboru čtou vedle sebe.
- **Nově napsanou adresu ověř zavoláním na živé aplikaci**, ne tím, že se kód přeloží.
  Chyba v názvu sloupce se v Pythonu neprojeví až do chvíle, kdy dotaz opravdu běží.
- Dopad byl na **6 lidí s přístupem do karty** (Šárka Novotná, Petra Šafránková,
  Petra Fajmonová, Marta Šafaříková, Tomáš Hrbek, Jiří Honomichl) plus rodiče.

Souvisí: [[doc-system-strategie-agendy-zdroj-staff-group-a-nadrazene-slozky]].

