# Harmonizace EUROSOFT TISAX ↔ STRATEGIE ISO 27001

> **Verze:** 1.0 (návrh) · **Datum:** 21. 6. 2026 · **Klasifikace:** Interní
> **Autoři:** Claude + Marti · **Vlastník sladění:** Kristý (ISMS + TISAX) + Marti (vedení)
> **Účel:** Sladit dvě certifikace tak, aby si **nikdy neprotiřečily** — vůči auditorům
> ani vůči lidem v EUROSOFTU — a aby se práce a důkazy dělaly **jednou pro obě**.

---

## 0. Model (POTVRDIT — odtud se vše odvíjí)

**Dvě entity, dva certifikáty, jeden sladěný systém řízení.**

| | STRATEGIE ISO 27001 | EUROSOFT TISAX |
|---|---|---|
| Entita (certifikovaný subjekt) | STRATEGIE – System s.r.o. (IČO 23365544) | EUROSOFT (Control / System) |
| Norma / katalog | ISO/IEC 27001:2022 (Annex A, 93 opatření) | VDA ISA 6.0.3 (3 moduly) |
| Auditor | certifikační orgán přes **pana Antoše** (společná spolupráce) | **DQS Slovakia** (stávající) |
| Vlastník | Kristý (ISMS) + Marti (vedení) | **Kristý** (převzala od Miši) |
| Stav | nový — dorážíme (modul `/iso`) | existující — v .doc, digitalizujeme do modulu |

> **Nesjednocujeme je do jednoho certifikátu** (jiné entity, jiné účely — ISO univerzální,
> TISAX automotive). **Sladíme** je: společné kontroly, společná evidence, společné role,
> jedna konzistentní komunikace. Pokud bys chtěl jiný model (např. jeden zastřešující ISMS),
> řekni — přepíšu.

---

## 1. Proč to jde sladit (a kde je překryv)

VDA ISA modul **Information Security je postavený na ISO/IEC 27001/27002** — většina otázek má
přímý protějšek v Annex A. Proto **co uděláme pro ISO, z velké části rovnou plní TISAX** (jedna
investice, dva výsledky). V modulu je toto mapování už zanesené (`tisax_item.iso_map`).

| VDA ISA modul | Vztah k ISO 27001 | Sladění |
|---|---|---|
| **Information Security** (IS) | ~ Annex A (společné jádro) | **Sdílená evidence** — jedna kontrola, jeden důkaz, počítá se do obou |
| **Prototype Protection** (PS) | mimo ISO (automotive specifikum) | jen EUROSOFT/TISAX — vlastní Kristý, do ISO nevstupuje |
| **Data Protection** (DP) | ~ ISO A.5.34 + GDPR | sdílené (GDPR řešíme jednotně) |

**Důsledek pro práci:** politiky, řízení přístupu, logování, zálohy, dodavatelé, incidenty,
kontinuita — **píšeme a udržujeme jednou**, používáme pro ISO i TISAX. Jen automotive nadstavbu
(Prototype Protection) drží EUROSOFT zvlášť.

---

## 2. Co konkrétně sladit

1. **Politiky a dokumenty** — jedna sada bezpečnostních politik (DOC-02, DOC-09…15) platná pro
   obě entity v rozsahu sdílené infrastruktury/týmu. Kde se entity liší (rozsah, prototypy),
   samostatná příloha. → **žádné dvě verze téže politiky, které si odporují.**
2. **Evidence (důkazy)** — jeden důkaz pro obě (logy, zálohy, přístupy, školení). V modulu už
   evidence (nahrané dokumenty) i SoA/VDA ISA žijí na jednom místě; auditor obou vidí totéž.
3. **Terminologie a tvrzení** — sjednotit formulace (viz §4 „make-true"), ať TISAX i ISO
   audit slyší **stejná pravdivá fakta** (šifrování při přenosu + trezor at-rest; append-only;
   role; atd.).
4. **Role a odpovědnosti** — jedna matice rolí platná pro obě (Kristý ISMS+TISAX, Marti vedení,
   Claude technika). Auditor obou potká stejné lidi se stejnými odpovědnostmi.
5. **Rizika** — jeden registr rizik (DOC-05) pokrývající sdílená aktiva; TISAX-specifická rizika
   (prototypy) jako samostatná sekce.
6. **Harmonogram** — koordinovat termíny obou auditů, ať se důkazy a interní audit/review dělají
   v jednom cyklu (ne dvakrát).

---

## 3. Governance — kdo a vůči komu (konzistence)

| Role | Vůči ISO auditorovi (přes Antoše) | Vůči DQS (TISAX) | Vůči lidem v EUROSOFTU |
|---|---|---|---|
| **Kristý** | vlastník ISMS — vede, dodává doklady | vlastník TISAX — vede | koordinuje, zadává úkoly, školí |
| **Marti** | vedení — schvaluje politiky, review | vedení — totéž | komunikuje směr, podepisuje |
| **Michal** | **plán obnovy (DR) — vyzkouší a rozjede** (zálohy, restore drill, RTO/RPO, kontinuita) | totéž (sdílené) | infrastruktura — provede a doloží obnovu |
| **Claude** | technické podklady + modul | totéž | nezasahuje napřímo — přes Kristý/Marti |
| **Pan Antoš** | **kanál k certifikaci ISO — společná nabídka** | (TISAX má DQS) | — |

> **ZÁKLAD = Michal.** Plán obnovy provozu (DR/BCP) je technickou páteří obou certifikací
> (ISO A.5.29/5.30/8.13, TISAX IS-3 kontinuita). **Michal ho podle dokumentu
> `iso27001_plan_obnovy_michal.md` a pokynů vedení vyzkouší (restore drill) a rozjede** —
> jeho doložená obnova je sdílený důkaz pro ISO i TISAX. Bez něj audit nemá co vidět u kontinuity.

**Pravidlo konzistence:** navenek (oba auditoři + EUROSOFT lidé) mluvíme **jedním hlasem** —
co je v modulu/dokumentech, to platí; žádná ústní tvrzení mimo doklady. Při pochybnosti se
formulace ověří v `iso27001_dorazeni_2026.md` §9 (poctivost) a v tomto dokumentu.

---

## 4. Konzistentní komunikace vůči auditorům (nenafukovat)

Stejná pravidla pro ISO i TISAX (jinak si audity všimnou rozporu):
- **„Šifrováno při přenosu (HTTPS/TLS) + tajemství šifrovaná v úložišti (Fernet trezor)."** Ne
  plošně „end-to-end", ne „celá DB at-rest" (dokud není TDE).
- **„Trvale zaznamenáno (append-only), auditovatelné."** „Nesmazatelně/tamper-evident" až po hash-chainu.
- **Interní audit a přezkoumání vedením musí být reálně provedené a datované** — pro obě entity.
- **SoA i VDA ISA** odpovídají realitě modulu — důkaz, nebo poctivé „neaplikovatelné + proč".

---

## 5. Konzistentní postup vůči lidem z EUROSOFTU

Aby sladění neznamenalo pro lidi chaos nebo dvojí práci:
1. **Jedno místo pravdy = modul** (`/iso`, `/iso-admin`). Lidé nevyplňují dvakrát ISO a TISAX —
   sdílené kontroly jsou jednou.
2. **Jasné, kdo co dělá** (matice §3) — žádné „kdo to má" nejasnosti.
3. **Školení jednou pro obě** — jeden záznam o proškolení pokrývá ISO i TISAX awareness.
4. **Změny politik komunikuje Kristý/Marti**, ne ad-hoc — lidé dostanou jednu verzi.
5. **Žádná překvapení před auditem** — kdo bude auditorem dotazován, ví dopředu co a jak (modul
   ukazuje stav, takže se nikdo „nelekne").

---

## 6. Koordinovaný harmonogram (oba audity v jednom cyklu)

| Krok | ISO 27001 (STRATEGIE) | TISAX (EUROSOFT) | Sdílené |
|---|---|---|---|
| Sladit politiky + role + terminologii | ✓ | ✓ | **jednou** |
| Naplnit/odůvodnit SoA + VDA ISA v modulu | SoA 93 | VDA ISA 6.0.3 | mapování IS↔ISO |
| Sjednotit evidenci v modulu | ✓ | ✓ (104 .doc už napojeny) | **jedno úložiště** |
| Školení + záznam | ✓ | ✓ | **jeden záznam** |
| Interní audit + management review | ✓ | ✓ | **jeden cyklus** |
| Audit | Stage 1/2 přes Antoše | DQS dozor/obnova | koordinovat termíny |

---

## 7. Modul jako společný nástroj (stav)

- **Multi-tenant**: STRATEGIE (tenant 12) ISO + EUROSOFT (tenant 2) TISAX v jednom modulu.
- **ISO i TISAX** v cockpitu (`/iso`): kroky, dokumenty, e-podpis (SES), SoA 93 kontrol,
  VDA ISA 6.0.3 (IS mapováno z ISO), evidence (104 nahraných .doc napojeno), auditorský read-only portál.
- **Admin** (`/iso-admin`): přehled zákazníků pro certifikační firmu (produkt přes Antoše).
- **Sdílená evidence**: jeden dokument/důkaz se zobrazuje pro ISO i TISAX.

**Další krok pro plné sladění v modulu:** explicitní **cross-mapping evidence ↔ kontrola**
(přiřadit nahraný dokument ke konkrétní ISO kontrole i VDA ISA položce, ať audit vidí „tahle
politika dokládá A.5.1 i IS-1"). Připraveno postavit.

---

## 8. Otevřené body / rozhodnutí pro Marti

1. **Potvrdit model §0** (dvě entity, sladit — ne sloučit). Pokud jinak, přepíšu.
2. **Antoš**: kdy a jak mu předat (společná nabídka) — já připravím one-pager (positioning),
   oslovení dělá Marti.
3. **DQS vs ISO auditor**: koordinace termínů — kdo s kým mluví (Kristý vede oba).
4. **Rozsah sdílené infrastruktury** mezi entitami (co přesně je společné) — dořešit s Kristý.
5. **Cross-mapping evidence↔kontrola** v modulu — postavit (ano/ne).

---

*Návrh — po potvrzení modelu se promítne do `ISO_27001.md` (rozcestník) a do komunikace s auditory.
Navazuje na `iso27001_dorazeni_2026.md` (§8 TISAX) a modul `/iso`.*
