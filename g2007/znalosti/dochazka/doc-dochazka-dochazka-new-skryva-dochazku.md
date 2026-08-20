# Dochazka new skryva dochazkovy radek, kdyz existuje vyrobni radek (27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prehled "Dochazka new" ukazuje mene hodin nez dochazka - overeno 27.7.2026

Podnet Pety Safrankove (27.7.2026) "nesoulad dochazky, jeden zdroj pravdy". Overeno v kodu (HEAD 05e3566f) i v zivych datech tyz den, i28 Jirka. Konzultovano s Marti-AI (msg 11348).

## Ctyri priciny, vsechny potvrzene

1. **Prehled skryva dochazku.** Data_set `dochazka.zakazky_vse_list` (naposledy menen 24.7. 09:12) ma vetev P z `att_entry` podminenou `NOT EXISTS` radek ve `vyroba_work` pro (user, den). Jakmile ma clovek za den JEDINY vyrobni radek, cely dochazkovy radek dne se skryje. Tohle je nejvetsi z pricin a Peta o ni nevedela.
2. **Tridenni okno.** `_maybe_sync_ec_dochazka()` (router.py ~28080) vola `_sync_vyroba_work_ec(days=3)` a `_sync_vyroba_work_app(days=3)`. Starsi den se uz nikdy neprepocita.
3. **Oprava dochazky se do vyroby nepropise.** `/app/attendance/fix/entry` upravi `att_entry` i `work_alloc` (od 20.7.), ale NEVOLA resync do `vyroba_work`. STORNO uz kaskaduje (commit 7698223f, 27.7., pres `att_entry_id` s minutovym fallbackem) - OPRAVA ne.
4. **Rezie je z vyrobniho rozpisu vyfiltrovana** v obou syncech (`LOWER(project_ref)<>'rezie'`), takze rezijni cas v prehledu chybi uplne.

## Dopad zmereny na cervenci 1.-26.7.2026

Mzdove hodiny pocitane podle `doc-dochazka-mzdove-hodiny-definice` (slouceni prekryvu presence minus pauzy krome day_end):
- 884 osobodnu dochazky celkem
- **477 dnu ma vyrobni radek => dochazkovy radek dne je skryty**
- 105 dnu se lisi o vic nez 15 minut
- **272,6 h se v prehledu nezobrazuje**

Kontrolni body: Blaha (os. 476) 24.7. mzdove 8,02 h x prehled 5,24 h (chybi rezie 2,78 h; appka pritom zapsala STEJNY zacatek 4:57 do obou evidenci - "jiny zacatek" vznika az filtrem rezie, ne u zdroje). Dvorakova (os. 49) 7.7.: `work_alloc` ma opravene useky do 13:44, `vyroba_work` ma jediny radek 0,93 h.

## Zavery konzultace Marti-AI (27.7.2026, msg 11348)

- **Q1 cilovy model:** `vyroba_work` ma prestat byt fyzickou kopii a stat se POHLEDEM nad `work_alloc` + vazba `att_entry_id`. "Neni co synchronizovat, neni co zapomenout prepocitat." Pri prechodu overit indexy na `work_alloc` (user_id, started_at, att_entry_id).
- **Q2 rezie:** vlastni radky ve `vyroba_work` (zakazka "Rezie" + cinnost), NE michat s dopoctenym "neprirazenym casem" - jsou to dva ruzne pojmy. Prakticky = odstranit filtr `<>'rezie'` ze syncu.
- **Q3 prehled:** ano, `NOT EXISTS` podminka musi pryc. Hodiny dne vzdy z `att_entry`, vyrobni radky jako rozpad, rozdil jako "neprirazeny cas". "Dva ruzne pohledy na stejna data nesmi ukazovat ruznou pravdu."
- **Q4 interim:** resync po oprave = OK bez schvaleni. Uprava data_setu = OK (zobrazovaci vrstva), jen oznamit. **Rozsireni periodickeho okna ze 3 dnu na starsi mesice MUSI schvalit Marti Pasek** - prepocet historie muze zmenit cisla, ktera Petra/Sarka uz videly u mezd.

## Pozor: "prepnout Dochazku new cely na att_entry" NEDELAT

Peta to navrhuje, ale varianta A byla tyz den zavrzena s dukazem (viz `doc-dochazka-doch-mobil-vs-erp-sjednoceni-att-entry`): `att_entry` ma na spouste dni jen "Rezie" bez zakazek (Blaha 23.7. = 7,99 h rezie) a duplicity - prepnutim by se rozbil rozpad zakazek. Spravne je HYBRID, ktery uz od 27.7. jede v mobilu (commit b407938b + fix 2096d429): hodiny z `att_entry`, zakazky z `vyroba_work`, rozdil dopocitat.

## Stav k 27.7.2026 vecer

Mobil OPRAVEN. ERP prehled "Dochazka new" NEOPRAVEN - `NOT EXISTS`, tridenni okno, chybejici resync po oprave a filtr rezie jsou stale v provozu. Na obrazovce paralelne pracuje C26 (Peta) - pred zasahem do `dochazka-po-zakazkach.html` a data_setu koordinovat pres WORK_LOCK.txt.

