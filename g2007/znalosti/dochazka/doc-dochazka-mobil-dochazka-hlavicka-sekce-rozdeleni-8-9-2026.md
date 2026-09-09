# Mobil, obrazovka Moje docházka: hlavička s fotkou místo nadpisu, nové sekce a rozdělení „Můj přehled" na Moje hodiny + Moje volno (8. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Zadal Jiří Honomichl 8. 9. 2026, schválila Marti-AI (msg 14999, 15008, 15017, 15023, 15026, 15038, 15044).
> Vše ověřeno na živé `/mobile` v prohlížeči, ne jen v kódu.

## Co se změnilo na obrazovce docházky

1. **Textový nadpis obrazovky je pryč.** Nahoře je **hlavička s fotkou**: kolečko avatara
   (klepnutím se mění), vedle **příjmení a jméno** a pod tím **zařazení z organizační struktury**.
   Hlavička se sem **přestěhovala z „Můj přehled"** — tam už není.
2. **Horní lišta na téhle obrazovce vůbec není.** Prázdná zabírala 46 px (`.topbar`
   `min-height:40` + `margin-bottom:6`). Odsazení od horního okraje telefonu drží
   `padding-top:14px` na `body`, ne lišta; `safe-area-inset-top` se v appce nikde nepoužívá.
   Jediné místo, které lištu hledá (`_dochTopPad`), má `if(_tb)` guard, takže absenci přežije.
   **Ostatní obrazovky svou lištu s nadpisem mají dál.**
3. **Nová sekce „OBSLUHA DOCHÁZKY"** nad blokem zakázka/činnost/START, ve stylu ostatních
   nadpisů sekcí. **Tlačítko nápovědy ❓ se přesunulo z horní lišty vedle ní** a zmenšilo se
   na velikost toho textu (dotyková plocha klesla ze 44 na 26 px — Marti-AI to schválila
   s odůvodněním, že nápověda není primární akce jako START).
4. **Návod „Vyber zakázku a činnost, pak ▶️ START"** je **pod tlačítkem START**, vycentrovaný,
   a ukáže se **jen když START svítí** (je uvnitř větve `if(!aw)`). Při běžící směně tam není nic —
   nad dlaždicemi zůstává jen zelené „🟢 MAKÁŠ — klikni a změň".
5. **Nemocenská a Lísteček od lékaře** mají vlastní sekci **„NEMOC A LÉKAŘ"** (obě jsou zamčené).
6. **„Můj přehled" ZRUŠEN a rozdělen na dvě obrazovky:** **„Moje hodiny"** (⏱, měsíční hodiny,
   `GET /app/dochazka/moje-mesic`) a **„Moje volno"** (🌴, nárok a čerpání dovolené a sick days,
   `GET /app/dochazka/muj-prehled`). Tělo se dělilo 1:1, logika se neměnila.
7. **Sekce „PODMÍNKY & FINANCE" přejmenována na „MOJE PŘEHLEDY"** — obsahuje Moje hodiny,
   Moje volno, Moje podmínky, Moje finance; starý název seděl jen na dvě z nich.

## Pozor na názvy: „Moje volno" NENÍ „Moje absence"

**„Moje absence"** (sekce Moje docházka) = formulář žádosti o absenci + seznam žádostí.
**„Moje volno"** (sekce Moje přehledy) = nárok a čerpání. Jsou to **dvě různé obrazovky**
a záměna mate. Proto se nová obrazovka nesmí jmenovat „Moje absence" — rozhodl Jiří Honomichl.

## Past 1: `topbar()` si text escapuje sám

`topbar(title, …)` v `10_core.js` volá **`esc(title)`**. Funkce `_navJmeno()`
(v `74_claude27_render_init.js`) naopak vrací jméno **už escapované**, protože jde do
`navBtn`, který ho vkládá přes `innerHTML`. **Předat `_navJmeno()` přímo do `topbar()` =
dvojité escapování** — jméno s `&` nebo apostrofem by se zobrazilo rozsypané. Do `topbar()`
patří **syrová** hodnota z `window.__M2W.__domuStav.jmeno`.

## Past 2: zrušení obrazovky = prohledat i TEXTY PRO LIDI, a to i malými písmeny

Smazání obrazovky není jen kód. „Můj přehled" byl kromě dlaždice a registrací i v:
- **nápovědě docházky** a **v hlasovém průvodci** (výčet sekcí),
- **čtyřech hláškách**, které se ukážou, když se nepodaří zjistit zůstatek dovolené nebo
  sick days („zkontroluj si ho prosím v přehledu …") — tedy přesně ve chvíli, kdy je člověk
  zmatený a špatný odkaz ho zmate podruhé.

⚠️ **Hledej i varianty s malým písmenem.** Mluvený komentář průvodce říkal
„V sekci Podmínky a finance je **můj přehled**…" — při prvním průchodu unikl, protože
se hledalo jen „Můj přehled". Hledej `ILIKE`, ne přesnou shodu, a projdi i skloňované tvary.

## Kde to žije

Vše v `g2007.soubor`, dílky `10_core.js`, `48_hr_podminky_me.js`, `60_dochazka.js`,
`71_plan_prace_cinnosti.js`, `73_pref_poptavka.js`; po každém zápisu
`@@G2007PUBLISH apps/api/static_db/mobile.html`. Registrace nové obrazovky má čtyři místa —
viz [[doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026]] a
[[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]].

