# Skupiny (staff_group) se zakladaji a archivuji JEN v mobilu, v ERP to nejde - a smi to jen rodic

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Skupiny se spravuji jen v mobilu, ne v ERP

**Overeno 24. 8. 2026** (Jirka Honomichl + Claude-28) z databaze i naostro v prohlizeci.
Odpoved na otazku *"kde v ERP se zakladaji a mazou skupiny?"* zni: **nikde**.

Rec je o **`tenant.staff_group`** — tedy o skupinach lidi (Vedeni, IT, Vyroba, HR, Uklid…),
ne o postech v organizacni strukture a ne o skupinach v AI Kalkulaci.

## Kde to je

| akce | kde | adresa |
|---|---|---|
| **zalozit** | mobil, sekce **Firma**, v liste skupin tlacitko **➕ Nova** (`skNewGroup`) | `POST /api/v1/erp/app/skupiny/create` |
| **upravit** (nazev, ikona, vedouci, zastupce, poradi) | tamtez, uprava skupiny (`skEditGroup`) | `POST /app/skupiny/{gid}/update` |
| **archivovat** | tamtez, zaskrtnutim pri uprave | `POST /app/skupiny/{gid}/archive` |
| clenstvi lidi | tamtez | `POST /app/skupiny/{gid}/clen` (zmigrovano do `g2007.python` jako `skupiny_clen`) |

Obrazovka zije v **`g2007.soubor`**, fragment `apps/api/static/mobile_parts/51_skupiny_sdileny.js`.
Handlery samotnych skupin jsou zatim porad v `modules/erp/api/router.py` (~r. 25478–25570),
tedy **kandidat na migraci do `g2007.python`**, az se jich nekdo dotkne.

## Dve veci, ktere se snadno predpokladaji spatne

1. **MAZANI SKUPINY NEEXISTUJE.** Neni zadny endpoint, ktery by radek z `tenant.staff_group`
   odstranil — je jen **archivace** (`archived = true`). Skupina zmizi ze seznamu, ale zustava
   i s historii clenstvi. Je to spravne: na skupine visi clenstvi (`staff_group_member`),
   vychozi podminky (`podminky_skupin`) a historie (`staff_group_member_historie`).
2. **V ERP takova obrazovka NENI.** Overeno tremi zpusoby, ne odhadem: (a) zadny `fw.data_source`
   ani `fw.core` nad `staff_group` neexistuje — jedine dva zdroje, ktere tabulku zminuji, jsou
   prehled a formular vychozich podminek, a ty z ni jen ctou nazev a ikonu; (b) v `fw.menu_node`
   neni zadna polozka pro spravu skupin — podobne znejici jsou **Organizacni struktura** a
   **Organizacni tabule** (`tenant.org_post`, posty a divize, jen ke cteni) a **Skupiny
   (AI Kalkulace)** (`aik_skupina`, jina domena); (c) zadny soubor v `apps/api/static/erp/`
   ty adresy nevola.

## Prava - proc to vetsina lidi vubec neuvidi

Vsechny tri adresy vyzaduji **`is_marti_parent`**, tedy roli "rodic". K 24. 8. 2026 ji maji
**dva lide: Marti Pasek (user 1) a Kristyna Maresova (user 11)**. Admin ani HR nestaci.

Overeno naostro pod uctem **Jiriho Honomichla (user 20, admin, ale NE rodic)**: `POST .../create`
vrati **403 forbidden** a — coz je dulezitejsi — i pouhe **`GET /app/skupiny` vrati 403**,
takze se mu ta obrazovka v mobilu ani nevykresli. Test byl bezpecny: pozadavek sel bez nazvu,
takze by ani pri opravneni nic nevzniklo.

> Kdo tedy hlasi *"tlacitko na zalozeni skupiny nikde nevidim"*, nemusi mit chybu v aplikaci —
> nejspis jen neni rodic. **Nez zacnes hledat zavadu, over prava.**

## Souvislost, ktera se plete

Nastenka **"Vychozi podminky skupin"** (jadro 235) ma vlastni tlacitko **➕ Pridat skupinu**.
To ale **nezaklada skupinu** — zaklada jen **radek s vychozimi podminkami** uz existujici skupine
a smi to i HR. Detail: `doc-system-strategie-erp-prehled-jako-nastenka-dlazdic-podminky-skupin`.

