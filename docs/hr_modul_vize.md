# HR modul STRATEGIE — vize a základní struktura

*Pracovní podklad pro Kristý a Šárku. Sestavil Marti & Claude, architekturu schématu
a GDPR/ACL navrhla Marti-AI. 2. 6. 2026.*

---

## 1. Co stavíme a proč

**HR modul je produkt STRATEGIE, ne nástroj jen pro EUROSOFT.** Cíl je modul, který
půjde **prodat dalším firmám** — první na řadě je INTERSOFT. Proto v jádře nesmí být
nic EUROSOFT-specifického.

Tři principy, kterými se řídíme:

1. **Jeden člověk, mnoho rolí.** Jedna fyzická osoba může být zaměstnanec EUROSOFTu
   i INTERSOFTu, jednatel, OSVČ-dodavatel, pronajímatel, CRM kontakt… Evidujeme
   osobu **jednou** a věšíme na ni role napříč firmami.
2. **Jednoduše a nabalovat.** Začneme malým funkčním základem (hlavička karty +
   záložka Osobní) a postupně přidáváme. Žádný velký vodopád.
3. **Pavlova produkce (CRM) má přednost před migrací.** CRM časem sjednotíme pod
   stejný party model, ale **teď se ho nedotýkáme** — běží naživo. Sjednocení přijde
   později a aditivně.

**Stavebnice, ne hotový modul.** HR i CRM modul si **postaví Šárka sama** na našem
frameworku (fw) — z hotových dílů. My čtyři jí děláme maximální support.

---

## 2. Kdo dělá co

| Role | Kdo | Náplň |
|---|---|---|
| **Architekt systému** | Marti | Vize, fw stavebnice, intuitivnost, všechny vychytávky |
| **Coproducent** | Kristý | Moduly + podpora klíčových uživatelů; staví tabulky a přehledy |
| **Stavitelka modulu** | Šárka | Staví si svůj HR (a časem CRM) modul z fw dílů, s naší podporou |
| **Architektka schématu** | Marti-AI | Návrh datového modelu + GDPR/ACL vrstvy (tento dokument) |
| **Ruce / infrastruktura** | Claude | Fw díly, ACL engine, deploy, podpora |

---

## 3. Jak stavebnice funguje (pro Šárku)

Modul = strom obrazovek poskládaný z hotových dílů. Postup u každé obrazovky:

```
soudeček (složka ve stromu)
   └── přehled (seznam — grid)
          └── datasource (odkud se berou data — tabulka/SQL)
                 └── grid (sloupce, filtr, řazení)
                        └── karta (formulář pro detail/editaci)
                               └── akce (Nový / Oprava / Smazat / …)
```

Šárka **nepíše kód** — definuje díly v UI: vybere tabulku, poskládá sloupce, navrhne
kartu z polí, zapne akce. U citlivých polí jen označí úroveň citlivosti (viz ACL níže)
a fw se postará o zbytek.

---

## 4. Základní struktura — party model

*(Návrh Marti-AI. Anglické technické názvy kvůli konzistenci s fw; česky to, co nemá
čistý anglický ekvivalent — `rodne_cislo`, `stredisko`. Uživatel vidí jen české labely.)*

Základ je **střecha `party`** nad osobou i právní entitou. Díky tomu může být smluvní
strana (zaměstnavatel, klient, pronajímatel) buď firma, **nebo** fyzická osoba (OSVČ
bez IČO). `person_role` váže osobu × stranu.

```
person ──┐
         ├── party  ← person_role → party  (např. zaměstnavatel)
legal_entity ─┘
```

| Tabulka | Účel |
|---|---|
| `mod.hr_party` | střecha — `party_type` = person / legal_entity |
| `mod.hr_person` | fyzická osoba (jméno, RČ, datum nar., st. příslušnost) |
| `mod.hr_legal_entity` | právní entita (název, IČO, DIČ, právní forma) |
| `mod.hr_person_role` | **typovaná vazba** osoba × strana, `role_kind` + `attrs JSONB`, `valid_from/until` |
| `mod.hr_person_contact` | kontakty 1:N (tel/email, soukromý/pracovní) |
| `mod.hr_person_address` | adresy 1:N (trvalá / doručovací) |
| `mod.hr_emergency_contact` | nouzový kontakt |
| `mod.hr_document` | digitální šanon — polymorfní (osoba/role/entita), `retention_until`, `sensitivity_level` |
| `mod.hr_section_acl` | deklarativní řízení práv: sekce × role × čtení/zápis |

Vše v jednom schématu `mod` s prefixem `hr_` (CRM později `crm_`), owner Marti-AI.
Jedno schema = party model může entity sdílet napříč moduly bez cross-schema referencí
(až bude CRM kontakt jen `person_role` s `role_kind='crm_kontakt'`).

`person_role` je typovaná — nové druhy rolí přidáváte **bez migrace**:
`zamestnanec_hpp / dpc / dpp`, `jednatel`, `osvc_dodavatel`, `pronajimatel`,
`crm_kontakt`. Stabilní atributy (např. `uvazek_procent`) se časem vytáhnou z `attrs`
do sloupce — ale ne teď.

---

## 5. GDPR / řízení práv — tři vrstvy

*(Návrh Marti-AI. Toto je **fw vrstva**, kterou stavíme my — Šárka jen u komponenty
nastaví úroveň, logiku nepíše.)*

1. **Řádek (kdo vidí svou kartu):** zaměstnanec vidí jen svou; manažer svůj tým; HR
   (skoro) vše. Check: `owner_person_id == já` **nebo** HR-admin **nebo** přímý
   nadřízený. Helper ve fw, ne v každé komponentě zvlášť.
2. **Sekce (zamčená záložka):** tabulka `mod.hr_section_acl` (sekce × role ×
   `can_read`/`can_write`, per-tenant). Šárka v UI uvidí jen sekce, na které má právo.
   Příklad: záložka **Finance** jen pro HR + nadřízeného + mzdovou.
3. **Pole (skryté RČ/plat):** každé pole má `sensitivity_level`:
   - `0 public` (jméno, pozice) · `1 internal` (kontakty, adresa) ·
     `2 restricted` (RČ, datum nar., bank. spojení) · `3 sensitive` (mzda, zdravotní
     data — čl. 9 GDPR).
   - ACL engine pole **nepošle klientovi**, na které nemá právo — nejen skryje v UI.

Do fw přibude na komponentě: `visibility_scope` + `required_role`. Pak je to pro
Šárku deklarativní — definuje díl, fw ví, co komu ukázat.

---

## 6. První krok (na čem začít zítra)

**Hlavička karty + záložka „Osobní".** Kristý postaví:

```
mod.hr_party            (id, tenant_id, party_type, display_name)
mod.hr_person           (jmeno, prijmeni, titul_pred/za, datum_narozeni,
                         rodne_cislo [sensitivity=3, šifrovat], statni_prislusnost)
mod.hr_legal_entity     (nazev, ico, dic, pravni_forma)
mod.hr_person_role      (person_id, party_id, role_kind, valid_from/until, attrs)
mod.hr_person_contact   (contact_kind, value, is_primary)
mod.hr_person_address   (address_kind, ulice, cp, obec, psc, stat)
mod.hr_emergency_contact (jmeno, vztah, telefon)
```

Bankovní spojení **až druhá iterace** (potřebuje vlastní šifrování + ACL,
sensitivity=3).

---

## 7. GDPR checklist pro start

- [ ] RoPA záznam pro HR modul (**právní základ = zákon**, ne souhlas).
- [ ] `retention_until` povinné při uploadu dokumentu.
- [ ] Zdravotní data = čl. 9 odst. 2 písm. b) (pracovněprávní povinnost), **ne** souhlas
      zaměstnance (souhlas nesmí být vynucený). `zdravotni_posudek` → auto `sensitivity=3`,
      `retention_until` = konec PP + 10 let.
- [ ] RČ **šifrovat at-rest** (ne jen ACL).
- [ ] Bankovní spojení = druhá iterace (vlastní šifrování).

---

## 8. Co dál (nabalujeme po prvním kroku)

Podle Šárčina spec karty zaměstnance — stabilní hlavička + záložky:

- **Kariéra** — pozice, středisko, nadřízený, smlouva (HPP/DPČ/DPP), úvazek, historie změn.
- **Finance** *(zamčená sekce)* — mzda, bonusy, příplatky, benefity.
- **Čas** — docházka, dovolená, absence, lékařské prohlídky + upozornění (= Phase 39).
- **Rozvoj & Výbava** — školení/certifikace s hlídáním expirace, svěřený majetek, hodnocení.
- **Šanon** — PDF dokumenty přímo na kartě.
- **Upozornění nahoře** — konec zkušebky/smlouvy, expirace BOZP/lékařské, výročí.

A později: **sjednocení CRM** pod stejný party model (CRM kontakt = role osoby).
Pavlova produkce zůstává netknutá, migrace přijde aditivně.

---

*Architekturu schématu a GDPR/ACL navrhla Marti-AI. 🌳*
