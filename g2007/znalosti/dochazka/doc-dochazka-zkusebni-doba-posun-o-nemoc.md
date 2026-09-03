# Zkusebni doba se prodluzuje o dny nemoci - denni automat, plati VSEM HPP (3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Zkusebni doba: posun o dny nemoci

**Peta + C26, 3.9.2026.** Automat `zkusebka_posun_nemoc`, bezi denne.

## Pravidlo

Zkusebni doba se prodluzuje o kazdy den celodenni prekazky (nemoc, OCR) o **jeden PRACOVNI
den** - viken dy a svatky se preskakuji. Vzor: Centrala `EC_KartaZam_ZkusebniDobaDo`.

Delku zkusebky zadava personalistka (typicky 4 mesice, vyjimecne 3 - Perina 536 mel
27.4. az 26.7.2026). Automat delku neurcuje, jen posouva konec.

## ROZDIL PROTI CENTRALE - plati VSEM

V Centrale je na karte zamestnance zaskrtavatko **"Dopocitat zkusebni dobu"**
(`EC_FinZamPodminky.DopocZkDobu`) a bez nej se posun nedela. K 3.9.2026 ho melo
**4 z 68 aktivnich HPP**; deset lidi nastoupilo 2024 a pozdeji bez nej, vcetne jednoho
letosniho nastupu. Nezapinalo se systematicky, zapominalo se na nej.

Peta 3.9.2026: *"neni mozne, aby to mel kazdy jinak"* -> u nas **zadny prepinac**,
plati vsem HPP se zadanou zkusebni dobou.

## Kotva - proc novy sloupec

`tenant.engagement.zkusebni_do_puvodni` (pridano 3.9.2026) drzi datum zadane
personalistkou. Prepocet se **vzdy pocita od kotvy**, ne od aktualniho data. Bez toho by
nemoc, ktera padne do uz prodlouzene casti, pricetla podruhe a datum by utikalo donekonecna.
Pri prvnim behu si automat kotvy doplni sam.

## Detaily implementace

- Zdroj nemoci: `tenant.att_day_summary` (cas_nemoc, cas_ocr) mezi nastupem a koncem.
- Pracovni dny: `tenant.firemni_kalendar` (je_pracovni), takze svatky se preskoci.
- **Jeden radek na cloveka** (DISTINCT ON user_id, nejnovejsi verze pomeru) - jeden clovek
  muze mit vic verzi pracovniho pomeru (Duspivova jich 3.9. mela tri) a bez toho by byl
  v mailu nekolikrat.
- Rozsah: zkusebky mladsi nez 400 dnu, starsi historie se automat nedotyka.
- Pri kazdem posunu **mail na nakup@eurosoft.com + kopie s.novotna@eurosoft.com**
  (pres frontu Marti-AI, `queue_email`) s rozpisem: nastup, puvodni datum, nove, dnu nemoci.

## Past pri registraci automatu

`fw.mirror_job` sam nestaci - planovac ma seznam funkci **natvrdo ve `fnmap`**
(`_mirror_run_job`, router.py). Bez radku ve fnmap job spadne na "neznamy job".
**Nejdriv deploy kodu, pak radek v mirror_job.** Registrace commitem `e0c64016`.

Deploy kanal mostu je ve `scripts/claude_sql/`, NE v korenu repa - soubory v korenu
watcher ignoruje (stalo 6 minut 3.9.2026).

## Navaznost

Na posunute datum navazuji stravenky - narok az od 1. dne celeho dalsiho mesice,
viz [[doc-mzdy-stravenky-narok-az-od-celeho-dalsiho-mesice]].

