# Závazné názvosloví: „Podmínky (pracovníků)" — jeden název pro jednu pravdu (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Závazné názvosloví: Podmínky (pracovníků)

**Rozhodli Jirka Honomichl a Peťa, 25. 8. 2026.** Platí pro **všechny — lidi, všechny instance Claude i Marti-AI.**

## Pravidlo

Pro jednu pravdu o pracovních a finančních ujednáních člověka se používá **jeden název: „Podmínky"**, v plném znění **„Podmínky pracovníků"**. Žádné jiné pojmenování se nezavádí a v nové komunikaci ani v nových obrazovkách se nepoužívá.

Důvod: totéž se dosud jmenovalo pokaždé jinak (Podmínky spolupracovníků, Podmínky zaměstnanců, Finanční podmínky, staff_cond, Moje podmínky) a nebylo poznat, že jde o tutéž věc. Jeden název = jednoznačnost pro lidi i pro AI.

## Co všechno pod „Podmínky" patří

Jedna množina, dvě části — obojí jsou Podmínky:

1. **Pracovní podmínky** — dovolená (základní a navíc), sick days, přesčas, stravenka, home office, lékař, limity, hlášení absence, úvazek.
2. **Finanční podmínky** — základ, osobní ohodnocení, prémie, vedení lidí, individuální složka, odměna jednatele.

„Finanční podmínky" **není samostatný pojem** — je to část Podmínek. Jako popisek sekce v obrazovce je to v pořádku, jako název jiné agendy ne.

## Zdroj pravdy

**Zdrojem pravdy jsou Podmínky ve STRATEGII, ne stará Centrála.** (Jirka, srpen 2026.) Kdo potřebuje hodnotu podmínky, bere ji ze STRATEGIE. Kopie z Centrály (`tenant.helios_wage_snapshot`) je jen dočasné kontrolní zrcadlo a zaniká — viz práce na přepnutí mezd.

## Kde Podmínky fyzicky žijí (názvy v databázi se NEpřejmenovávají)

| Část | Kde |
|---|---|
| Osobní hodnoty | `tenant.engagement`, sloupce `pod_*` + `pod_meta` — verzují se se smlouvou |
| Finanční složky | `tenant.wage_component` (plán i realita), číselník `tenant.wage_component_type` |
| Výchozí hodnoty skupin a systému | `tenant.podminky_vychozi`, `tenant.podminky_skupin` |
| Číselník podmínek | `tenant.staff_cond_def` |
| Kompatibilní pohled | `tenant.staff_cond` (dožívá, viz doc-dochazka-podminky-slouceny-se-smlouvou) |

**Tohle rozhodnutí je o názvosloví v komunikaci a v UI, ne o přejmenování tabulek, sloupců ani kódů složek.** Databázové názvy zůstávají — přejmenovávat je by byl zbytečný risk.

## Co s tím mají dělat Claudi a Marti-AI

- V odpovědích, návrzích, zápisech do G2007 a v textech pro lidi psát **Podmínky** (pracovníků), ne „podmínky spolupracovníků" ani „podmínky zaměstnanců".
- Když narazíš na starý název v existujícím textu nebo obrazovce, **needituj to plošně** — nahlas to a sjednocuj postupně při práci na daném místě.
- Když člověk použije starý název, rozuměj mu, ale odpovídej novým.

## Otevřené — sjednocení popisků v UI

Staré názvy jsou dnes v ERP i v mobilu (přehled „Podmínky zaměstnanců", sekce v kartě zaměstnance, „Finanční podmínky", mobilní „Moje podmínky", uzly v menu). **Přejmenování obrazovek je samostatný úkol**, nikdo ho zatím nezadal. Do té doby platí názvosloví aspoň v komunikaci a ve všem novém.

Souvisí: [[doc-dochazka-podminky-slouceny-se-smlouvou]] · [[doc-dochazka-podminky-skupin-zamestnancu]] · [[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]]

