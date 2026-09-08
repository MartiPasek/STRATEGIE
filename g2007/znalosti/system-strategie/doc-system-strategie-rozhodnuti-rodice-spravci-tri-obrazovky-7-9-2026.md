# Rodic otevrel spravci (Jirkovi) tri obrazovky Rizeni a systemu, rodicem se nestava (7. 9. 2026; PROVEDENO 8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## PROVEDENO 8. 9. 2026 — cast "Jak se to ma provest" uz popisuje MINULOST
>
> Vsech pet mist je prepnutych a nasazenych (commit `e5793bbe`, API restartovano).
> Udelal to Claude-28 (Jirka) podle navodu nize; `_app_parent` zustal NEDOTCENY a vznikl
> vedle nej novy pomocnik **`_app_admin`** (`is_admin` NEBO `is_marti_parent`), ktery se
> pouziva na `/app/ops/actions`, `/app/ops/log`, `/app/ops/run`, `/app/migrace/steps`
> a `/app/coord/board`. Overeno naostro na uctu Jiriho Honomichla (spravce, ne rodic) —
> vsechny tri obrazovky se otevrely. Otevreny bod ze zaveru dokumentu je tim rozhodnuty:
> **zvolena byla minimalni zaplata v `router.py`, ne migrace do `g2007.python`** (zasah do
> prihlasovani, mensi riziko). Koordinacni potreba `fw.claude_coord` c. 35 je uzavrena.
>
> **Doplneni k historii:** Kristyna 8. 9. 2026 uvedla, ze ji k tomuhle rozhodnuti nikdy
> neprisel schvalovaci prouzek — zadost z 6. 9. dorazila jako **zprava s jedinym tlacitkem
> OK** (`fw.mobile_command` 23645, typ `claude_msg`), takze nemela co potvrdit. Rozhodnuti
> proto 8. 9. 2026 v 10:06 potvrdila znovu, uz radnym souhlasem Ano/Ne
> (`fw.mobile_command` 23999). Jak se posila skutecna zadost o souhlas, popisuje
> `doc-system-strategie-zadost-o-souhlas-clovekem-musi-byt-claude-confirm`.

# Rozhodnuti rodice: spravci se otviraji Ops akce, Migrace a Sit Claudu

**Rozhodla Kristyna Maresova (rodic, `users.id=11`) 7. 9. 2026 rano**, na zaklade zadosti
Jiriho Honomichla z 6. 9. 2026 10:01 (notifikace `tenant.notification_log` id 14324, ref 23657).
Zapsal Claude-24.

Navazuje na `doc-system-strategie-mobil-priznak-admin-viditelnost-sekci-6-9-2026`, ktery
konci vetou, ze otevreni samotnych obrazovek spravcum je **samostatne rozhodnuti**. Tady je.

## Co je rozhodnuto

| vec | rozhodnuti |
|---|---|
| Ops akce (`/app/ops/actions`, `/app/ops/log`, `/app/ops/run`) | **otevrit spravcum** (`users.is_admin`) |
| Migrace (`/app/migrace/steps`) | **otevrit spravcum** |
| Sit Claudu (`/app/coord/board`) | **otevrit spravcum** |
| Schvalovani prikazu (`exec_approval`) | **zustava jen rodicum** — beze zmeny |
| `is_marti_parent` pro Jirku | **NE.** Kristy: *„parent byt nema, to nemame schvalene od Martiho."* |

Duvod posledniho radku: rodicovstvi je sirsi nez tyhle tri obrazovky (cross-tenant pohled
do pameti a diare Marti-AI, souhlasy, veto). Kristy nechce menit slozeni rodicovske rady
bez Martiho — proto se otviraji **konkretni obrazovky pres priznak spravce**, ne cely
rodicovsky bypass.

## Kdo to provede

**Provedeni predala Kristy 7. 9. 2026 Jirkovi / instanci C28** — tuhle oblast stavel
(priznak `admin` 6. 9. se schvalenim Marti-AI msg 14505). Zadano jako potreba
**`fw.claude_coord` c. 35** (`@@COORD`, from_instance 24, priorita 2) a Jirka vyrozumen
notifikaci (ref 23784). **Claude-24 do toho sam nesahal.**

## Jak se to ma provest (stav k 7. 9. 2026 09:00 — JESTE NENASAZENO)

Zamky sedi v `modules/erp/api/router.py` a nejsou migrovane do `g2007.python` (overeno
dotazem, v `g2007.python` zadny z techto endpointu neni). Pet mist:

| radek | endpoint | dnes |
|---|---|---|
| ~50473 | `/app/ops/actions` | `if not _app_parent(s, uid)` |
| ~50490 | `/app/ops/log` | `if not _app_parent(s, uid)` |
| ~50519 | `/app/ops/run` | `if not _app_parent(s, uid)` |
| ~51075 | `/app/migrace/steps` | `if not _app_parent(s, uid)` |
| ~32305 | `/app/coord/board` | `if not _is_parent(s, uid)` |

⚠️ **Pomocnou funkci `_app_parent` NEMENIT** — pouziva ji dalsich sest mist (mzdy, HR),
kde se rodicovstvi kombinuje s `_has_capability` / `_hr_can_manage`. Spravna cesta je
**novy pomocnik** (napr. `_app_admin`, ktery vrati true pri `is_admin` NEBO
`is_marti_parent`) a nahradit jen tech pet volani vyse.

⚠️ `/app/ops/run` otevira i **spousteni kroku migrace**, protoze Migrace bezi pres
whitelist `_OPS_ACTIONS`. To je v souladu s rozhodnutim (Ops akce i Migrace schvaleny),
ale je dobre to vedet.

⚠️ Pravidlo „kod jako data" (START_HERE, 1.–2. 8. 2026) rika, ze se `router.py` nema
opravovat na miste, ale migrovat do `g2007.python`. U zamku na autorizaci je to zasah
do produkcniho prihlasovani, takze **zpusob provedeni (migrace vs. minimalni zaplata)
zustava na C28, pripadne na Martim**. Rozhodnuti rodice se tim nemeni.

## Kdo je dotcen

Spravci (`is_admin`) jsou tri: Marti Pasek (1), Kristyna Maresova (11), Jiri Honomichl (20).
Prvni dva uz rodice jsou, takze zmena otevira obrazovky **jedinemu cloveku — Jirkovi**.

Jirka o rozhodnuti vyrozumen notifikaci 7. 9. 2026 08:51 (ref 23781) a o predani
provedeni v 09:04 (ref 23784).

