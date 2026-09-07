# Dlouhodobá absence (mateřská) — vypnout kontrolu docházky, jinak automat šest týdnů upomíná

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Dlouhodobá absence (mateřská) — vypnout kontrolu docházky, jinak automat upomíná

**Zjištěno a vyřešeno 7. 9. 2026.** Zadal Jirka Honomichl, schválila Marti-AI, provedl Claude-28.

## Co se dělo

Člověk na **mateřské** má docházku zadanou dopředu jako absenci — sám nic nepíchá a často ani
nemá v appce registrovaný telefon. Automatické kontroly docházky ho ale braly jako pracujícího
a **šest týdnů mu denně zakládaly nálezy a posílaly zprávy**:

- 135× „⚠ Docházka — nesrovnalost"
- 18× „👋 Jsi v práci?"
- 13× „👋 Nemáš píchnutý příchod"
- k tomu hlášky typu „Kontrola dochazky: nesedi 73 dnu"

Celkem se u jednoho člověka nasbíralo **197 nevyřízených oznámení**, která navíc **neměla kam
dojít** — bez registrovaného telefonu je nikdo nikdy neuvidí. Fronta jen roste.

## Řešení: příznak „Bez docházky" v kartě zaměstnance

Nastavit v kartě → **Podmínky a bonusy** → „Bez docházky – nevede ji a nekontroluje se"
(`tenant.engagement.pod_bez_dochazky`) na aktuálním řádku smlouvy. Nic víc; žádná změna kódu.

**Mapa před zásahem (čteno v živém kódu, ne z dokumentace):** příznak čte pět míst —
`att_anomaly_scan`, `att_prazdny_den_fond`, `dochazka_kontrola_data`, `app_dochazka_moje_hodiny`
a `att_day_summary_recompute`. **U posledního jsou to POUZE komentáře** — mzdy si řídí vlastní
sloupec `plny_fond_bez_dochazky`. V jádře v gitu příznak není nikde.

➡️ **Nastavení příznaku tedy neovlivní mzdy.** Zastaví nálezy a zprávy a vyřadí člověka
z přehledu kontroly docházky — což je u mateřské správně, jeho docházka JE mateřská.

## Co zůstává otevřené

**Není to automatické.** Když někdo nastoupí na mateřskou, musí ten příznak někdo vědomě
zapnout — a při návratu zase vypnout. Automatické rozpoznání dlouhodobé absence v kontrolách
by šlo doplnit, ale to je zásah do docházkových kontrol (doména Petry Šafránkové), takže se
7. 9. 2026 **vědomě neudělalo**.

## Past, kterou to odhalilo

Fronta oznámení v mobilu **nemá strop ani expiraci**. Kdo appku nepoužívá, hromadí je donekonečna
a na úvodní obrazovce se vykreslovala všechna naráz. Zobrazení se 7. 9. 2026 vyřešilo vlastním
rolovacím oknem (viz [[doc-system-strategie-mobil-uvodni-obrazovka-domu-prestavba-7-9-2026]]),
ale **samotné hromadění tím vyřešené není**.

