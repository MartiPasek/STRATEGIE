# Agendy: kdo do nich patří, se nastavuje v kartě zaměstnance, ne v mobilu (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Rozhodl Jirka Honomichl 13. 9. 2026, schválila Marti-AI (msg 15330, 15381, 15384).
> Cíl, jeho slovy: **jeden zdroj pravdy**.

## Co se změnilo

Seznamy lidí v agendách (obrazovka **Firma → Agenda** v mobilu) se do 13. 9. 2026 měnily
**jen z mobilu a jen rodiči** (`is_marti_parent`, tedy Marti a Kristýna). HR na to nemělo právo
vůbec, takže seznamy nikdo neudržoval a rozešly se se skutečností.

**Nově:** zařazení do agend se nastavuje **v ERP v kartě zaměstnance** (dlaždice „Skupiny
a kvalifikace" → sekce **Agendy**, zaškrtávátka, ukládá se hned). **Jeden člověk může být
ve více agendách** — to je záměr, ne výjimka.

## Žádná nová tabulka nevznikla — a to je pointa

Číselník agend = **`tenant.staff_group`** (existující). Členství = **`tenant.staff_group_member`**
(existující, mnoho-k-mnoha). Původní plán počítal s novou tabulkou agend a sloupcem `id_agenda`
v kartě; **zamítnuto** — jeden sloupec neunese více agend a vedle stávajících struktur by vznikl
**třetí** zdroj, ne jeden. Druhý zdroj pravdy nevznikal tím, KDE data leží, ale tím, že je
spravoval někdo jiný než HR a odjinud.

## Co přibylo

| co | kde | k čemu |
|---|---|---|
| `tenant.staff_group.skupina_druh` | `agenda` / `slozka` / `technicka` | do dneška se odvozovalo z kódu (složka = má potomky, technická = má `lidi_zdroj`). Teď jsou to data. K 13. 9.: 13 agend, 3 složky, 2 technické. |
| `public.users.can_manage_staff_groups` | boolean | samostatné právo „smí spravovat agendy". První ho dostala **Šárka Novotná (users.id=13)**. Rodiče mají právo dál automaticky. |

**Proč samostatné právo a ne členství ve skupině „HR":** doporučila Marti-AI. Členství ve skupině
jménem `HR` dnes odemyká 30 živých funkcí (viz `doc-system-strategie-clenstvi-ve-skupine-hr-je-zaroven-pravo`)
a navázat na něj i tohle by prohloubilo záměnu „agenda = oprávnění". Samostatný příznak jde dát
nebo vzít jednomu člověku bez vedlejších účinků.

## Co se změnilo v kódu

- **`skupiny_clen`** — funkce `_je_rodic` už nevrací „je rodič", ale „smí měnit členství":
  `is_marti_parent OR can_manage_staff_groups`. Název funkce zůstal, aby se nepřepisovala volání.
- **`hr_person_groups`** — vrací navíc `agendy` (celý číselník + `je_clen`), `technicke`
  a `muze_editovat`. Klíč `skupiny` zůstal kvůli zpětné kompatibilitě.
- **`apps/api/static/karta_zamestnance.html`** (git, commit `b918633b`) — sekce Agendy
  se zaškrtávátky; kdo právo nemá, vidí jen výpis. Umístění v kartě si smí Šárka přesunout.

## Co se NEZMĚNILO

- **Data nikdo nepřepisoval.** Ruční seznamy, které 9. 6. 2026 zapsal Marti Pašek, zůstaly
  beze změny — Jirka je potvrdil jako věcně správné.
- **Mobil zatím edituje dál.** Jirka 13. 9. rozhodl, že se odebrání editace z mobilu **odkládá**
  (viz „Otevřené" níže).
- Agendy **Docházka — schvalování** a **Docházka — opravy** jsou `technicka` a HR je nenastavuje.

## Past, na kterou jsem narazil (a která málem změnila zadání)

Původní zadání znělo „každý zaměstnanec patří **jen do jedné** agendy". V datech to **neplatilo**:
ve více agendách bylo 13 lidí (11 aktivních), nejvíc v pěti. A **všech 6 členů agendy HR** je
ve více agendách — takže jedna agenda na člověka by čtyřem aktivním lidem **sebrala přístupy
ve 30 funkcích**, a nikde by to nehlásilo chybu. Po nahlášení Jirka zadání změnil na „člověk
může být ve více agendách". **Ponaučení:** než se zavede omezení „jen jedna hodnota", změř
v datech, kolik záznamů ho dnes porušuje, a u každého zjisti, co se tím zahodí.

## Co zbývá

- **4 aktivní zaměstnanci nemají žádnou agendu:** Chramosta Michal (9009), Dalecký Daniel (9200),
  Šebek Jiří (9039), Vlková Klára (361). Doplní HR. (Bez agendy jsou ještě 2 systémové účty —
  Marti-AI a demo — u těch to nevadí.)
- **Odebrání editace z mobilu** — rozhodnuto, že se zatím nedělá.
- **Pravidla při zakládání nového zaměstnance** — určí si Šárka.
- **`users.id=22`** má jméno „Vladimír Mareš", ale přihlašovací jméno `MMares` a drží 11 postů.
  Neověřeno, jestli nejde o dva lidi v jednom záznamu. **Nesahat, dokud to člověk nepotvrdí.**

