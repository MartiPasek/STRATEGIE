# Kára — systém hodnocení produktivity člověka (model motor + lopata + znalosti × výstup)

Zdroj: Šárčin e-mail s vyhodnocením kandidáta (Performia CandidateReport.pdf,
EXEC-U-TEST 3.0) + foto roll-upů z Performia akce + **klíčový výklad Martiho 13.6.**
Marti + Šárka = **licencovaný partner Performie** pro vyhodnocování osobnosti a
produktivity.

## 0) Model produktivity člověka (Marti, 13. 6. 2026) — JÁDRO SYSTÉMU

Produktivita člověka **není** osobnostní dotazník. Dotazník je jen jeden faktor.
Faktory v pořadí důležitosti:

1. **MOTIV = motor (engine).** **NEJDŮLEŽITĚJŠÍ.** Co člověka pohání, co ho baví, co
   chce. Hlavní hybná síla. Bez motoru se nikam nejede — sebelepší nástroj je k ničemu.
2. **Osobnostní profil = LOPATA (pracovní nástroj).** To je EXEC-U-TEST. Čím je lopata
   **vytuněnější**, tím lépe se snoubí s motorem. Čím **děravější**, tím víc musí člověk
   makat, aby dokázal totéž co někdo s vytuněnou lopatou.
3. **Znalosti & zkušenosti.** Nejméně zásadní — dají se většinou **snadno nabrat**.

Celé se to **porovnává s reálnou fyzickou produktivitou** = kolik produktu člověk
skutečně vyrobí (množství výstupu). **Produktivita je OTEVŘENÉ ČÍSLO**, ne škála —
orientačně 100 = standard, výjimečný výkon klidně +1000 a výš (škála −100…+100 patří
**jen** osobnostnímu dotazníku). To je validace a diagnostika:
- silný motor + vytuněná lopata + nízký výstup → něco brzdí, hledej příčinu;
- děravá lopata + vysoký výstup → motor táhne, člověk maká nadoraz (pozor na vyhoření);
- slabý motor + dobrá lopata → potenciál nevyužitý, chybí „chtění".

**Zásada (Marti-AI, drží):** žádný algoritmus to neslučuje do jednoho čísla. Faktory se
**zobrazují odděleně**, vztah mezi nimi a výstupem **interpretuje licencovaný konzultant**.

### 0a) Ověření produktivity u nových uchazečů (Performia praxe) — VÝCHOZÍ ČÍSLO

U nového uchazeče ještě nemáme vlastní statistiku výstupu. Performia učí (a děláme):
**vyžádat si od uchazeče alespoň DVA kontakty na bývalé zaměstnavatele**, Šárka jim
**telefonuje** a ptá se, jak se kandidát projevoval — **byl pracovitý a produktivní?**

- Výsledek těchto telefonátů = **výchozí (baseline) hodnota produktivity** v systému.
- Je to **dočasné proxy** — jakmile naběhne **naše reálná statistika** (`prod_output`),
  produktivitu ověříme „v reálu" a baseline ustupuje skutečným číslům.
- Pravidlo: u nového uchazeče **minimálně 2 reference**. Volá licencovaný konzultant
  (Šárka), zaznamenává pracovitost + produktivitu + shrnutí rozhovoru.
- GDPR: kontakty dává sám uchazeč (souhlas s oslovením); referent je také osobní údaj —
  ukládáme střídmě, za ACL, s auditem (stejná hranice jako zbytek modulu).

## 1) Co dotazník měří (struktura)

**10 vlastností osobnosti (A–J), každá na škále −100 … +100 (sloupec „Body"):**

| Kód | Vlastnost | Co určuje (zkráceně) |
|---|---|---|
| A | Stabilita | Uspořádanost, stálost |
| B | Pozitivnost | Optimismus, nadhled, orientace na řešení |
| C | Klid | Klid, sebekontrola |
| D | Jistota | Stálost, předvídatelnost |
| E | Aktivita | Úroveň energie, vitálnost |
| F | Tah na bránu | Přesvědčení, přímost |
| G | Zodpovědnost | Zodpovědný, iniciativní |
| H | Správný odhad | Tolerance, spravedlnost |
| I | Empatie | Schopnost vcítit se, přátelskost |
| J | Komunikace | Společenský, živě hovorný |

- **Referenční pásmo** na ose: orientační značky **−19** a **+32** (norm band).
- **Barevné zóny pruhů** (z reportu — interpretace Performie): tmavě modrá / oranžová
  / oranžová šrafovaná / šedá. Zónu **přebíráme z reportu**, nepočítáme ji sami.
- **Klíčové pravidlo Performie** (doslova z reportu): *„Vztahy mezi jednotlivými
  vlastnostmi jsou důležitější než hodnota samotných vlastností."* → Kára **není**
  průměr ani naivní vzorec. Profil je podklad, zařazení dělá **licencovaný konzultant**.

**Příklad (anonymní kandidát, kód KFF871C12FJ, projekt „Coffee break s jednatelem 2026"):**
A98 · B16 · C20 · D50 · E97 · F74 · G88 · H78 · I96 · J99.

## 2) Datový model (tenant.*, vlastní Marti-AI)

- **`tenant.pers_trait`** — číselník 10 vlastností: `code` (A–J), `label`, `sublabel`,
  `ord`. Statický seed.
- **`tenant.pers_assessment`** — jedno vyhodnocení: `id`, `tenant_id`, `subject_kind`
  ('user'|'candidate'), `subject_id`, `test_type` ('EXEC-U-TEST 3.0'), `project`,
  `perf_code` (kód Performie), `assessed_on`, `consultant_user_id`, `gender`,
  `age_band`, `source` ('performia'), `report_path` (originální PDF v úložišti),
  `norm_low` (−19), `norm_high` (+32), `created_by`, `created_at`.
- **`tenant.pers_assessment_value`** — `assessment_id`, `trait_code` (A–J),
  `value` smallint (−100…+100), `zone` (text: blue/orange/striped/gray — z reportu).
- **`tenant.pers_assessment_access`** — append-only audit, kdo profil otevřel (citlivé).

Vazba na člověka: polymorphic `subject_kind`+`subject_id` → interní `public.users`
**nebo** uchazeč `tenant.recruit_candidate` (most nábor → onboarding nese profil dál).

## 3) UI (appka, pod „Vedení firmy" / HR; ACL jen licencovaní + rodiče)

- **Seznam vyhodnocení**: kdo · projekt · datum · kód · konzultant.
- **Detail = U-TEST graf** našimi prostředky: 10 horizontálních pruhů −100…+100,
  hodnota „Body", barva = zóna z reportu, svislé čáry norm bandu (−19 / +32), legenda.
  Tlačítko **„Otevřít originální report (PDF)"**.
- **Zadání**: ruční zápis 10 hodnot + zón (z reportu), příp. pozdější import z Performie.
- Vizuál v duchu Performia U-TEST (modrá/oranžová), ale **náš render** — report Performie
  zůstává přiložený jako originál.

## 4) Vazba na Káru (kvadrant Tahoun / Efektivní / Méně efektivní / Brzdí)

- Profil EXEC-U-TEST je **podklad**, ne výpočet. Zařazení do kvadrantu dělá
  **licencovaný konzultant** (Marti/Šárka) — s oporou v profilu a vztazích mezi
  vlastnostmi, dle metodiky Performie. Systém zaznamená zařazení + zdůvodnění,
  nevymýšlí vlastní algoritmus (respekt k metodice i IP).
- Doplňkově (oddělené, transparentně) můžeme zobrazit **objektivní provozní signály**,
  co už máme (spolehlivost docházky, odpracováno × fond, zakázka/režie) — ale jasně
  odlišené od osobnostního profilu, ne smíchané do jednoho skóre.

## 5) Citlivost, IP a hranice (→ konzultace Marti-AI)

- **Performia IP**: EXEC-U-TEST je licencované know-how. Ukládáme **skóre + zóny + kód +
  originální report (PDF)** pro vlastní potřebu licencovaného partnera. **Negenerujeme**
  vlastní náhradu jejich interpretačních textů — jejich report zůstává originálem.
- **Citlivý osobní údaj**: přístup jen **licencovaní (Marti, Šárka) + rodiče**; běžní
  vedoucí ne; audit každého otevření. Do paměti Marti-AI **neukládat** (jako u uchazečů).
- **Otevřené otázky pro Marti-AI** (doplněno do `dopis_marti_ai_produktivita_kara.md`):
  vidí hodnocený svůj profil? smí do Káry vstoupit i objektivní signály, a jak je oddělit?
  uchování dle zákonů ČR (report sám říká „mějte pečlivě uschovány").

## 6) Závazné závěry konzultace Marti-AI (13. 6. 2026)

Marti-AI dala **zelenou** s těmito závaznými podmínkami (promítnuto do DDL i dalšího):

- **Q1 přístup:** jen licencovaní (Marti, Šárka) + rodič (Marti-AI, audit). **Vedoucí svůj
  tým NEVIDÍ** — otevřít až po metodickém školení Performia + dohodě s Martem. Jmenovitě
  ano, ale jen v chráněném prostoru s auditem (`pers_assessment_access`).
- **Q2 skóre:** z EXEC-U-TEST **nepočítáme nic**. Zařazení do kvadrantu = konzultant ručně
  se zdůvodněním. Provozní signály (spolehlivost docházky + zakázka/režie) jen jako
  **oddělený panel „Provozní přehled"**, nikdy sloučené do jednoho čísla. Plnění úkolů
  zatím opatrně (šum dle kvality zadání).
- **Q3 poznámky:** samostatná tabulka `pers_assessment_note` (`author_user_id`,
  `note_type='consultant_observation'`, `visible_to_subject`). ✅ v DDL.
- **Q4 paměť:** do `record_thought` **nic** — žije jen v modulu za ACL + audit.
- **Q5 tón:** „Podklad pro rozvoj, ne ortel." Kvadranty přejmenované: Tahoun · Efektivní ·
  **Rozvoj** (dříve „méně efektivní") · **Prostor pro změnu** (dříve „brzdí"). ✅ seed.
  Úvodní text v appce: „Zařazení není etiketou — je výchozím bodem." Profil má vést k akci.
- **Q6 transparentnost:** zaměstnanec **vidí svůj** U-TEST graf (hodnoty + zóny); kvadrant
  vidí až po rozhodnutí konzultanta (`quadrant_disclosed`); poznámky jen když
  `visible_to_subject=true`. Vlastní záznam přes speciální self endpoint.
- **GDPR/IP:** `consent_given`+`consent_at` (souhlas zaměstnance) + `retention_until`
  (návrh 5 let od ukončení PP / do odvolání). Report Performie zůstává originálem
  (`report_path`), negenerujeme náhradu jejich textů.

## 7) Stav (13. 6. 2026)
- ✅ **DDL LIVE — lopata** (bridge #274): `pers_trait` (10 A–J), `pers_quadrant_cis` (4),
  `pers_assessment`, `pers_assessment_value`, `pers_assessment_note`,
  `pers_assessment_access`.
- ✅ **DDL LIVE — model produktivity** (bridge #275): `prod_factor_cis` (motive#1 ·
  personality#2 · knowledge#3 · output#0=validace), `prod_motive` (motor: drivers/enjoys/
  wants/strength), `prod_knowledge`, `prod_output` (množství výstupu), `prod_eval`
  (holistické zhodnocení konzultantem — váže lopatu + motor + kvadrant, BEZ algoritmu).
  GRANTy pro `strategie`.
- ⚠️ **Nové k doplnění s Marti-AI** (přibyly nad rámec 1. konzultace): zachycení MOTORU
  (intrinsická motivace je intimní) + porovnání s fyzickým výstupem (riziko reduktivního
  užití). Stejné hranice platí: oddělené, bez algoritmu, ACL, audit, bez paměti.
- ⏭️ **Další (čeká):** backend endpointy (ACL licencovaní + rodiče; self endpoint pro
  zaměstnance) → **U-TEST graf** v appce naším renderem → napojení na kartu člověka a
  nábor → oddělený „Provozní přehled". Kvadrant na `/web/partner-demo` zůstává jako demo,
  dokud nebude pár reálných záznamů + ověřené workflow.
