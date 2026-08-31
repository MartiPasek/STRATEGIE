# Migrace rodiny /app/work do g2007.python - att_employee pripraveno, ceka na aktivaci (Kristy)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Migrace rodiny /app/work do g2007.python - stav k 31. 8. 2026

Peta (Claude-26), 31. 8. 2026. **Nic neni zive. Ceka se na aktivaci, kterou ma odklepnout Kristy.**

## Proc to vzniklo

27. 8. 2026 se opravovaly endpointy `/app/work/set-zakazka` a `/app/work/set-rezie`
primo v `router.py` (Zemanova dira - mizela cinnost). Podle zavazneho pokynu Martiho
z 1.-2. 8. 2026 (`doc-system-g2007-smer-zdroj-pravdy-python-soubor-2026-08-01`) se mela
pri te prilezitosti provest migrace do `g2007.python`. Neprovedla se - v prepisu te session
neni pro odklad zadny duvod, migrace se zminila az PO nasazeni opravy a odlozila se
bez dotazu. Peta to 31. 8. otevrela znovu a zadala dotazeni.

## Co uz je hotovo

- **`att_employee`** vlozeno do `g2007.python` jako `stav_zivota='navrzeno'`, verze 1,
  `vedlejsi_ucinek=true`, kategorie `dochazka`, puvodni umisteni `_att_employee (router.py 23233)`.
  Overeno ctenim - 2712 znaku, md5 `177a042e46b076a85b2b350b73c45ced`, sedi na bajt
  s lokalnim zdrojem. Zapsano pres base64 vzor (`doc-system-strategie-most-pyrun-a-base64-zapis`).
- **Chovani je 1(ku)1 s originalem**, vcetne zakladani zamestnance "U"+uid. Zamerne -
  viz nize.

## Co je jeste potreba

1. **Aktivace `att_employee`** (`stav_zivota='active'`). Funkce ZAPISUJE do
   `tenant.att_employee` (adopce i zalozeni), takze podle doktriny ji neaktivuje jedna
   instance sama. **Odklepne Kristy spolu s Petou.**
2. Teprve pak sest endpointu rodiny `/app/work` - `state`, `current`, `today`,
   `set-zakazka`, `set-rezie`, `set-cinnost` (router.py 27758-27960). Volaji `att_employee`,
   takze bez bodu 1 nemaji na co navazat.

Uz migrovane a aktivni zavislosti (jen se volaji, nic se s nimi nedela):
`att_wa_open`, `att_wa_close_running`, `att_is_working`, `att_apply_work_selection`.
K vepsani do skriptu zbyva jen drobnost - `_ATT_TENANT`, `_REZIE_REF`, `_norm_zakazka`,
`_wp_get`, `_wp_save` (dohromady cca 35 radku, pouzivaji se jen uvnitr rodiny /app/work,
tabulku `tenant.work_pref` v celem projektu nic jineho necte).

## Proc migrace NEMENI chovani

`_att_employee` pri nenalezeni zamestnance SAM ZALOZI noveho s cislem "U"+uid a oznaci
ho za aktivniho. Peta 31. 8. 2026 - kdyz je nekdo prihlaseny, ma ho najit, ne zakladat.
Jirka 11. 8. 2026 vyslovne rekl to v ramci demo opravy NEMENIT a oznacil to za samostatne
zadani (`doc-dochazka-demo-ucet-izolace-ukazkova-data`). Otazka odesla 31. 8. Tynce.
**Dokud nepadne rozhodnuti, migrace stehuje jen misto, kde kod bydli, ne chovani.**

## Overeno v datech 31. 8. 2026

Takto zalozeni existuji presne dva a ani jeden neni skutecny zamestnanec -
**U2** (Marti-AI, 8. 6.) a **U104** (demo ucet, 23. 6.). Zadny otevreny nalez, zadny
radek v dennich souhrnech, takze do mezd ani do FPD to nejde.

Po demo uctu ale zustalo v OSTRE dochazce EUROSOFTu smeti - **14 zaznamu `att_entry`
a 10 radku `vyroba_work`** z 1.-7. 8. 2026, vcetne dne s 31,94 h. 11. 8. v 11.50 se
u devi z nich jen preplo `is_active` na false (coz u `att_entry` znamena "prave na tom
dela", ne "platny zaznam") - **smazano nebylo nic**. Tri dalsi zaznamy vznikly az
11. 8. ve 12.23, tedy po te oprave, a vypadaji na testovaci. Co s tim, je druha otazka
pro Tynku.

## Poznamka k praci 31. 8.

Pokus vypnout `att_employee` U104 (`is_active=false`) prosel jako pozadavek 2632, Peta ho
vzapeti zastavila (nekdo ji rekl, ze tam nejaky demo zamestnanec byt musi) a vratil se
pozadavkem 2633. Stav je zpet puvodni, U104 je aktivni. **Duvod, proc tam musi byt,
neni overeny - jen predany ustne.** Kdo na to sahne priste, at si ho zjisti.

