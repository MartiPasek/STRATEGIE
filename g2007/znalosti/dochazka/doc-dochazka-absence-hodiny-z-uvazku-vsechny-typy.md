# Absence v mobilu berou hodiny z úvazku ve smlouvě — už všechny typy, ne jen sick day (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Absence v mobilu berou hodiny z úvazku — všechny typy (25. 8. 2026)

Zadal **Jirka Honomichl**, postavil Claude-28, schválila **Marti-AI** (msg 13700, oprava msg 13709).
Navazuje na [[doc-dochazka-uvazek-jediny-zdroj-smlouva]] a [[doc-dochazka-podminky-slouceny-se-smlouvou]].
Podnět je z e-mailového vlákna „Úvazek na dvou místech" (Šárka, Petra, Kristý, Jirka, 18.–21. 8. 2026);
Petra Šafránková tam 21. 8. formulovala pravidlo **„jedna funkce, kterou volají všechny vstupy,
ne pátá oprava na pátém místě"**.

## Výchozí stav

`att_denni_fond` (úvazek ze smlouvy děleno dny v týdnu, náhradní 8 h) je kanonický výpočet denního fondu.
V `att_absence` (zápis absence z mobilu) se ale volal **jen pro sick day** — ostatní typy měly natvrdo 8.
Nemoc, lékař, OČR a neplacené volno tedy dostaly **8 h bez ohledu na úvazek**.
Home office předává `None` (hodiny vznikají jinde), toho se to netýkalo.

## Co se změnilo — tři místa

1. **`att_absence`** (verze 17) — denní fond se počítá přes `att_denni_fond` pro **každý typ**.
2. **`att_absence_mine`** (verze 3) — měl **čtvrtou kopii téhož vzorce opsanou přímo v sobě**
   (týdenní úvazek děleno dny v týdnu, pak fond docházkové kategorie, pak 8). Nahrazena voláním
   `att_denni_fond`; kategorie i osmička zůstávají jako náhradní hodnota, jen se předají parametrem
   `default_h`, takže se chování nezměnilo.
3. **Mobil, dílek `apps/api/static/mobile_parts/71_plan_prace_cinnosti.js`** — formulář návrhu práce
   na den („Kolik hodin") předvyplňoval 8. Nově načte denní fond z `/app/attendance/absence/mine`
   (`fond_den`) — tentýž endpoint, který se o pár řádků níž už používal na půlden. Osmička zůstala
   jen jako záchrana, když se načtení nepovede, a hodnota se nepřepíše, když už do pole někdo psal.

## Čím je doloženo, že se nikomu nic nezměnilo

| Co | Důkaz |
|---|---|
| Existující data | letos tyto typy z mobilu **nezadal nikdo** — nemoc 611 záznamů, lékař 243, OČR 86, neplacené 81, všechny vznikly jinou cestou, z mobilu 0. Změna platí jen dopředu. |
| `att_absence_mine` | stará a nová cesta porovnány **u všech aktivních lidí, 0 rozdílů** (dotaz nad `engagement` a `att_kategorie`, spuštěný před zápisem) |
| Oba skripty | prošly kontrolou překladu (`compile`) po zápisu |
| Mobil | dílek uložen bytově přesně (otisk md5 sedí na znak), stránka složena a **ověřena na živé `/mobile`** — předvyplnění tam je, stará osmička zmizela |

⚠️ Při ověřování na živé `/mobile` vrátilo **první stažení starou verzi z mezipaměti**.
Poznalo se to až dotazem s náhodným parametrem navíc. Bez toho by vyšel falešný závěr „nenasadilo se".

## ⛔ Gotcha — systémová hodnota 40 v Podmínkách NENÍ mrtvá, nemazat

Vypadá jako zbytek po sjednocení úvazku (`tenant.podminky_skupin.pod_uvazek_h_tyden`, systémový řádek 40,
u všech 17 skupin prázdno) a hlavička `hr_conditions` k tomu ještě nedávno psala, že se
„už nikde nepoužívá a bude smazána samostatným krokem". **Čtou ji dva databázové spouštěče:**

- `tenant.engagement_pod_defaults` — doplní úvazek nové smlouvě, která ho sama nemá,
- `tenant.engagement_doplneni_pri_zarazeni` — doplní ho při **prvním zařazení člověka do skupiny**.

Kdyby se vyprázdnila, nové smlouvy by vznikaly bez úvazku a fond by spadl na náhradních 8 h.
Podrobněji [[doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty]].

**Poučení:** ověřovat v aplikační vrstvě (`g2007.python`, dílky mobilu) **nestačí** — hodnotu může
číst spouštěč v databázi, kterého se hledání v kódu vůbec nedotkne. Než něco označíš za mrtvé,
projdi i těla funkcí a spouštěčů.

## Gotcha — čtvrtou kopii vzorce hledání nenajde

`att_absence_mine` nemá v sobě slovo `att_denni_fond` ani nic, co by kopii prozradilo — vzorec je tam
opsaný. Našel se jen tím, že se přečetlo, **odkud mobil bere půlden**. Hledání podřetězce ukáže volající,
ne opisovače.

## Otevřené

- **Říct Petře Šafránkové.** Popis `att_denni_fond` do 25. 8. nesl podmínku, že změnu hodin
  u dovolené, nemoci, lékaře a OČR „musí odsouhlasit Petra" (mzdy). Změnu zadal Jirka a schválila
  Marti-AI; je v duchu Petřina požadavku z 21. 8., ale ona sama ji výslovně neodsouhlasila.
  Marti-AI doporučila dát jí to vědět jako informaci, ne jako zpětnou žádost o souhlas.
- Odkaz na znalost `doc-dochazka-sickday-po-hodinach` v popisu `att_denni_fond` byl **mrtvý**
  (taková znalost neexistuje) — nahrazen odkazem na tuto.

