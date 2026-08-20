# Navsteva lekare cerpa PREDNOSTNE sick day, po vycerpani se zapise Lekar a je potreba listecek

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Prednostni cerpani sick day pri navsteve lekare

Puvod pravidla - Marti, 28. 6. 2026. Do 17. 8. 2026 nebylo NIKDE popsane, zilo jen v kodu.
Potvrdil Jirka 16. 8. 2026, znalost zalozena na pokyn Marti-AI (msg 12788).

## Pravidlo
Kdyz clovek nahlasi, ze jde K LEKARI, system to rozpocita takto:
1. Z navstevy se bere nejvyse **4 h** (cap na jednu navstevu). Co je nad, se zkrati
   a clovek se o tom dozvi.
2. **draw = min(4 h, zbyvajici narok sick day)** - tahle cast se zapise do dochazky
   jako **SICKDAY**, s poznamkou "lekar do sickday".
3. **rest = zbytek** - zustane v dochazce jako **LEKAR** (medical).
4. Kdyz na sick day **nezbyva nic**, cela navsteva zustane jako **LEKAR** - a k tomu
   patri **listecek od lekare**.

Limit 4 h neni natvrdo - je to podminka lekar_listecek_limit_h v tenant.staff_cond,
takze jde zmenit pro cloveka i pro skupinu. Vychozi hodnota 4.

## Kde to zije
g2007.python **sickday_lekar_apply**. Vola ji att_absence pri typu medical i sickday.
Narok se bere z Podminek (staff_cond, sick_days_rok krat denni fond z work_mode),
cerpani ze skutecne dochazky (att_entry, typ sickday, mimo status superseded).

## Kdyz sick day nezbyva a clovek zada primo SICK DAY
att_absence cely zapis VEZME ZPET (rollback) - v dochazce nevznikne nic, ani nulovy radek.
Od 16. 8. 2026 k tomu vraci priznak **nabidnout_lekare** a appka nabidne tlacitko
"Zapsat jako navstevu lekare", ktere posle tentyz rozsah znovu jako typ Lekar.
Duvod (Peta 11. 8. 2026): "do erp nic nepsat, proste to je jako ze se nic nezadalo."
Do 11. 8. tam misto toho zustaval viset zaznam na 0,00 h.

## Sjednoceni vypoctu zustatku (17. 8. 2026)
Zustatek sick day se pocital na dvou mistech jinak. Funkce att_sick_balance_h, kterou
pouziva evidence navstevy lekare s fotkou listecku (att_med_start, endpointy
/app/med/balance a /app/med/start), brala cerpani z tenant.att_med_note.kryto_sick_h
a denni fond natvrdo jako uvazek deleno peti.
Ta tabulka ma za rok 2026 JEDINY zaznam a ten ma kryti 0 h, takze funkce videla cerpani
NULA u vsech a kazdemu ukazovala plny narok - i lidem s vycerpanymi sick days. A protoze
att_med_start podle toho cisla ROZHODUJE, kolik navstevy kryje sick day a kolik listecek,
nebylo to jen spatne zobrazeni.
Od 17. 8. 2026 (zadal Jirka, schvalila Marti-AI) bere cerpani z dochazky a fond z work_mode -
stejne jako prehled Narok a cerpani i jako sickday_lekar_apply. Jeden zdroj pravdy.
Zmerene pred nasazenim: zmenilo se zobrazovane cislo u 43 lidi (celkem 710,7 h),
NAROK se nezmenil nikomu, ctyri lide vysli v minusu (Pechoucek, Maresova, Urbanova,
Hladikova, kazdy minus 4 h) - presne jak to uz ukazuje Petin prehled.

## POZOR na rozdil proti prehledu
att_sick_balance_h scita cerpani za CELY ROK vcetne dnu v budoucnu, protoze odpovida na
otazku "kolik jeste muzu cerpat". Prehled Narok a cerpani naproti tomu deli na "cerpano"
(do dneska) a "naplanovano" (po dnesku). U cloveka, ktery ma sick day naplanovany dopredu,
proto sedi soucet, ale ne jednotlive sloupce. Neni to chyba, je to jina otazka.

## Overeno v provozu 17. 8. 2026
Jirka (cislo 9030) nahlasil navstevu lekare na 19. 8. Pravidlo z ni vzalo 4 h a zapsalo je
do dochazky jako sickday s poznamkou "u lekare do 12.00 [lekar do sickday]".
Endpoint /app/med/balance pak vratil narok 16 h, cerpano 4 h, zbyva 12 h - sedi.

