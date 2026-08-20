# Prepnuti zakazky za chodu DELI dochazkovy zaznam (koren problemu hlavicka vs rozpad) - nasazeno a OVERENO 20.8.2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se zmenilo
Do 20.8.2026 `att_apply_work_selection` menila bezici `tenant.att_entry` IN-PLACE - prepsala `project_ref` a radek NEDELILA. Hlavicka tedy nesla POSLEDNI volbu zakazky dne a tvarila se, ze cely blok byl na jedne zakazce; pravda zustavala jen v rozpadu `tenant.vyroba_work`.
Od 20.8.2026 (zadal Jirka, schvalila Marti-AI msg 13028) se pri ZMENE zakazky nebo typu bezici zaznam UZAVRE k now() a zalozi se NAVAZUJICI s novou zakazkou. Verze funkce 4.

## Proc to slo udelat bezpecne (vse cteno v zivem kode 20.8.2026)
- **Hodiny dne se nemeni.** `tenant.att_den_hodiny` slucuje souvisle pracovni useky pres min(zacatek)/max(konec) v ramci skupiny a scita ROZPETI, ne radky. Rozdeleni bloku na navazujici casti da tentyz soucet. Mzdy ctou att_day_summary, ktera jede z teto funkce.
- **Mechanismus uz existoval.** `att_checkin` se `switch=true` uzavira a otevira zaznam uplne stejne (ended_at=now(), is_active=false, hours=dopocet minus break_minutes). Nevznikl novy vzor.
- **Prekryvy se nerozsviti.** `att_fix_overlap` porovnava ostre (zacatek < novy_konec AND konec > novy_zacatek), takze navazujici radky (konec = zacatek dalsiho) kolizi nedelaji.
- **Trigger `att_entry_round_minutes`** zarovnava oba casy na minuty, takze konec uzavreneho a zacatek noveho sedi presne.

## Pojistky ve funkci (schvalila Marti-AI)
1. Deli se jen prace/rezie - break, day_end a commute jako dosud vubec ne.
2. Deli se jen kdyz se SKUTECNE meni zakazka nebo typ.
3. Zmena samotne CINNOSTI nedeli - att_entry cinnost nenese, vznikly by dva identicke radky; cinnost si drzi rozpad.
4. Kdyz bezici zaznam jeste nema ani minutu, prepise se in-place. Diky tomu nevznikaji nulove radky a hlavne `att_checkin`, ktera funkci vola hned po zalozeni prichodu, nezalozi druhy radek.
5. Novy radek je kopie puvodniho (den, zdroj, stav, ec_druh, misto); meni se zakazka, typ a cas zacatku. Poznamka zustava na uzavrene casti.
6. Vazba rozpadu (att_entry_id) na konci funkce miri na NOVY radek.

## Kdo funkci vola
`att_checkin` a tri endpointy v router.py - /app/work/set-zakazka, /app/work/set-rezie, /app/work/set-cinnost. `att_sync_vyroba_work` ji jen zminuje v komentari, nevola.

## Stav overeni - OVERENO NA PRODUKCI 20.8.2026
- Cesta BEZ deleni - po nasazeni proslo nekolik realnych prichodu a navratu z pauzy (Honal, Sedlackova, Svoboda, Egermaier, Veverka) bez chyby a se spravnou zakazkou.
- Cesta S DELENIM - **prvni realne prepnuti Lucie Jakesova 20.8.2026 v 05.52**, VR10711 -> VR10666. Dochazka 05.15-05.52 VR10711 (0,62 h) + 05.52-bezi VR10666. Rozpad sedi 1 na 1 - usek 05.15-05.52 VR10711 Dratovani navazany na prvni radek, usek 05.52-bezi VR10666 Pripravne prace na druhy. Casy navazuji bez mezery i bez prekryvu, vazba att_entry_id miri na NOVY radek.
- **Hodiny sedi** - `tenant.att_den_hodiny` za ten den vratila 0,62 h, soucet uzavrenych radku take 0,62 h.

## Co to NEopravuje
Historii. Za rok 2026 sedi 382,4 h na spatnych zakazkach (72 zakazek z 272, nejvic VR10666 +33,3 h). Tohle jen zastavuje dalsi rozchazeni.

## Souvisi
[[doc-dochazka-potvrzeni-dne-rozpad-v-mobilu]] - zobrazeni rozpadu tam, kde se hlavicka ukazuje lidem.
[[doc-dochazka-opravy-sedy-rozpad-stornovanych-radku]] - puvodni nalez (Nosek 3.-4.8.2026).

