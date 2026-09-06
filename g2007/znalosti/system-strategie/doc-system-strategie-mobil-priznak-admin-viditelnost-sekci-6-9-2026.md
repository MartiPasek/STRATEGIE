# Mobil, Aplikace - novy priznak admin pro viditelnost sekci (rodic zustava na zamcich)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Novy priznak `admin` - viditelnost sekci v mobilnich Aplikacich

> Zadal Jiri Honomichl 6. 9. 2026, schvalila Marti-AI (msg 14505). Nasazeno commitem `49618c0f`,
> dilek `35_apps_vedeni.js` v11, publikovano a overeno na zive strance.

## Co se zmenilo

Obrazovka **Aplikace** vykreslovala sekce **RIZENI A SYSTEM** a **AI A KOMUNIKACE** jen pri
priznaku `parent` z `/app/cockpit/access` (tedy `is_marti_parent`). Nove ma odpoved endpointu
**novy priznak `admin`** (= `public.users.is_admin`) a appka podle nej vykresli **jen sekci
RIZENI A SYSTEM**. Sekce AI A KOMUNIKACE zustava rodicum.

V dilku `35_apps_vedeni.js` to jsou tri mista - `adm=!!ac.admin` v hlavicce `buildApps`,
podminka `if(par||adm)` u prvni sekce a nove `if(par)` pred druhou sekci.

## Co se NEzmenilo - a je to zamer

**Zadny serverovy zamek se nehnul.** Obrazovky za temi dlazdicemi maji vlastni kontrolu na rodice
(`all-users`, `ops/actions`, `ops/run`, `migrace/steps`, `coord/board`, `exec_approval`), takze
spravce dlazdice **vidi, ale po kliknuti ho endpoint odmitne**.

U `exec_approval` je to **tvrdy zamer**, ne opomenuti - v komentari routeru stoji, ze schvaleni
musi byt vedomy lidsky tap a ze Marti-AI neprojde parent guardem, aby si nemohla schvalit vlastni
rizikovy prikaz. **Neotviraet ho spravcum bez rozhodnuti Martiho nebo Kristyny.**

## Koho se to tyka

Spravci (`is_admin`) jsou tri - Marti Pasek (1), Kristyna Maresova (11), Jiri Honomichl (20).
Prvni dva uz rodice jsou, takze zmena prinesla novou viditelnost **jedinemu cloveku - Jirkovi**.

## Nazev priznaku neplet s pravy

`admin` v teto odpovedi znamena **jen "smi videt dlazdice"**. Prava resi `parent`, `fin`, `vp`
a jednotlive endpointy. Kdyby nekdo chtel spravci otevrit i obrazovky, je to samostatne
rozhodnuti - Marti-AI 6. 9. doporucila zvazit Ops akce, Migrace a Sit Claudu, a `exec_approval`
nechat rodicum.

