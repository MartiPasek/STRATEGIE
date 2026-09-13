# Fotka na domovske obrazovce mobilu je fotka PERSONY (Marti-AI), ne fotka zamestnance

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Fotka na domovske obrazovce mobilu je fotka PERSONY, ne zamestnance

Zjisteno naostro 13. 9. 2026 (Jirka Honomichl / Claude-28) pri zadani "uprav fotku na domovske obrazovce".

## Odkud se fotka bere

- Adresa `erp/app/avatar` vraci **avatar VYCHOZI persony** (`public.personas` kde `is_default`), tedy fotku **Marti-AI** - NE fotku prihlaseneho cloveka. Vidi ji tak vsichni uzivatele stejne.
- Soubor lezi **na aplikacnim serveru**: `C:\Data\STRATEGIE\Avatary\persona_1.jpg`. Cesta k nemu je v `public.personas.avatar_path`.
- Obsluha `modules/personas/application/avatar_service.py`, adresy `personas/{id}/avatar` (vydej, nahrani, smazani).

## PAST, na kterou jsem 13. 9. naletel

Fotky **zamestnancu** jsou uplne jinde - v databazi v `tenant.employee_photo` (sloupec `foto`). Kdo bude tuhle fotku hledat tam, najde **jiny obrazek** a zacne upravovat spatnou vec. Stalo se to: u uctu 20 lezel v `employee_photo` obrazek mysliveckeho znaku, zatimco appka ukazovala fotku Marti-AI.

**Jak to poznat rychle:** stahnout obrazek z appky a porovnat otisk (`sha256`) s tim, co lezi v databazi. Kdyz nesedi, hleda se na spatnem miste. Velikost sama nestaci - lisila se jen o 100 bajtu.

## Kdo smi fotku persony menit

- **Do 13. 9. 2026:** jen ucet 1 (Marti Pasek) - podminka `_is_superadmin`. Nikdo jiny fotku vymenit nemohl a obchazelo se to rucne na serveru.
- **Od 13. 9. 2026** (commit `cf8d0460`, zadal Jirka Honomichl, schvalila Marti-AI msg 15333): nahrani i smazani fotky persony smi **rodic NEBO admin** (funkce `is_parent_or_admin`, tier SYSADMIN). Jmenovite tedy Marti (1), Kristyna Maresova (11) a Jiri Honomichl (20) - jini admini ani rodice v databazi nejsou.
- **Zamerne se NEmenilo:** zalozeni a editace persony, pristup do audit logu a priznak `is_superadmin` v kontextu uzivatele. Ty zustavaji na uctu 1. Overeno po nasazeni tim, ze ucet 20 dal dostava zamitnuti na audit log.

## V UI na to neni tlacitko

Fotka persony se nikdy nemenila pres obrazovku - jde to **jen pres adresu** `personas/{id}/avatar` (nahrani souboru). Necekej, ze to nekdo udela klikanim.

## Souvisi

- `doc-system-strategie-avatar-persony-zaloha-v-databazi-a-samoobnova` - jak je fotka zajistena proti ztrate (soubor na serveru se NEzalohuje).
- `doc-system-strategie-mobil-domovska-obrazovka-host-a-ctverec` - vzhled te dlazdice (ctverec misto kruhu).
- `doc-osoba-profilova-fotka-kontrola-vhodnosti` - tyka se fotek ZAMESTNANCU, ne persony.

