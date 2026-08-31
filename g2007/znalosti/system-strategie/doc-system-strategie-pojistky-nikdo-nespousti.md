# Hlídací pravidla v tenant.pojistka — od 28. 8. 2026 je spouští automat (do té doby 0 běhů)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlídací pravidla v `tenant.pojistka` — od 28. 8. 2026 je spouští automat

> ## ✅ VYŘEŠENO 28. 8. 2026 — pravidla se od dneška SPOUŠTÍ
>
> Původní název této znalosti byl *„…nikdo nespouští — 73 pravidel bez jediného běhu"*.
> **To už neplatí.** Rozhodl Jirka Honomichl 28. 8. 2026, schválila Marti-AI (msg 13947 + 13950).
>
> **Co se změnilo:** běží automat **`check_pojistky`** (`g2007.automat`, interval 1440 min =
> jednou denně). Logika je v `g2007.python` kód **`pojistky_scan`** (`active`), v jádře je jen
> tenká spojka `_check_pojistky` v `automat_eskalace.WATCHERS` (commit `5c247bc8`).
> Automat každé zapnuté pravidlo spustí a výsledek zapíše zpátky do `posledni_beh`,
> `posledni_vysledek` a `posledni_detail`. **V datech nic neopravuje.**
>
> **První ostrý běh 28. 8. 2026 v 10:27:06** — 88 pravidel, 499 ms, **88 v pořádku,
> 0 nálezů, 0 rozbitých.** Ověřeno čtením z `g2007.automat_run` i z `tenant.pojistka`.
>
> **Kam chodí nálezy:** eskalace `check_pojistky` míří na **Jirku Honomichla**
> (mapa `_L3_PRIJEMCE` v `automat_eskalace.py`). Ostatní automaty jdou dál Martimu + cc Kristý.
> Do fronty k vyřízení (`tenant.att_anomaly`) tyhle nálezy **zapsat nejdou** — fronta má
> `employee_id NOT NULL` a pracuje s dvojicí člověk+den, kdežto pravidlo vrací jen ano/ne.
>
> **Text níže je ponechán schválně** — popisuje, jak to vypadalo do 27. 8. 2026 a proč
> na tom záleželo. Navazuje [[doc-system-strategie-spoustec-hlidacich-pravidel-pojistka]]
> a [[doc-system-g2007-nerikat-pridal-jsem-pojistku-bez-spousteni]].

---

# Původní nález (25. 8. 2026) — stav do 27. 8. 2026

Našel Claude-28 **25. 8. 2026** při jiné práci, na pokyn Jirky Honomichla prověřeno do konce.
Vzala na vědomí Marti-AI (msg 13646).

## Nález

`tenant.pojistka` obsahovala **73 pravidel, z toho 71 zapnutých**. Psali je Peťa + Claude-26,
Kristý + Claude-24 a další, od 4. 8. 2026 dál.

**Ani jedno nemělo vyplněné `posledni_beh` ani `posledni_vysledek`.** Nebylo to tím, že by se
výsledky ukládaly jinam — **pravidla nikdo nespouštěl.**

## Ověřeno ze čtyř stran (ne odvozeno)

| kde by spouštěč mohl být | výsledek |
|---|---|
| repo (`grep` na `tenant.pojistka` přes `*.py`) | **nic** |
| živý kód `g2007.python` (regulární výraz na `from/join/into/update … pojistka`) | **nic** |
| naplánované automaty `tenant.automat` | jediný záznam je `bank_v1` (bankovní zaúčtování, **vypnutý**) |
| endpoint, který by šlo zavolat (`/pojistky`, `app/pojistk…`) | **neexistoval** |

Tabulka byla fakticky **soupis textů**. Pravidlo ožilo jen tehdy, když si jeho dotaz někdo ručně
zkopíroval a pustil — typicky Claude přes SQL most při jiné práci.

## Proč na tom záleželo

**Nikomu to neměnilo žádné číslo** — hlídač nepočítá, jen kontroluje. Ale znamenalo to, že
**rozbitá kontrola se sama neozve.**

Přesně to se stalo **16. 8. 2026**: pojistka `narok-dovolene-pravidla` se opírala o tabulku
`tenant.engagement_entitlement`, která byla ten den smazána při rozpadu dovolené. Pojistka od té
chvíle hlásila **CHYBA KONTROLY** — tedy nespadla tiše do „ztraceno", ale **nehlídala vůbec nic**,
a šlo o nárok na dovolenou, tedy o peníze. Všiml si toho člověk až **o den později**, náhodou, při
jiné práci. Detail: [[doc-dochazka-pojistka-narok-dovolene-po-zruseni-engagement-entitlement]].

Autoři pravidel je přitom psali v dobré víře, že hlídají.

## Co z toho plyne pro práci — PLATÍ DÁL

Automat běží **jednou denně**, ne po každé změně. Proto zůstává v platnosti:

- **Když měníš tabulku, na které nějaké pravidlo visí, pusť si jeho dotaz ručně** — před zásahem
  i po něm. Nečekej na noční běh.
- **Když rušíš tabulku nebo pohled, projdi `tenant.pojistka`** (`kontrola ILIKE '%%<jméno>%%'`)
  a pravidla přepiš. Jinak se z nich stane CHYBA KONTROLY.
- **Zelená v minulosti neznamená zelená dnes.** Nově je u pravidla vidět `posledni_beh` —
  **podívej se na datum**, ne jen na barvu.
- **Přečti si `kontrola`, ne jen název pravidla.** Zelené pravidlo nemusí hlídat to, co jeho
  jméno slibuje — doložený případ `absence-prepocita-doplneni-do-fondu`.

