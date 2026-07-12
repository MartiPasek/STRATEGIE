# 🧠 AI MAPA — orientace pro všechny AI (STRATEGIE + firma EUROSOFT)

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# 🧠 AI MAPA — orientace pro všechny AI (STRATEGIE + firma EUROSOFT)

> Sdílená „přední dveře" pro celou síť Claudů i všechny instance Marti‑AI. Čti tuto mapu přes `@@KB`
> a odsud se odkazuj dál. Cíl: rychlá orientace napříč AI z JEDNOHO zdroje pravdy, ne z dlouhých MD.
> **Citlivé věci (finance, personální/interní) tu NEJSOU** — patří jen do soukromého sandboxu
> C23 + Marti‑AI (MD5) + Kristý. — Claude ID23, 2. 7. 2026.

## 1. Co je STRATEGIE a firma
- **STRATEGIE** = modulární enterprise AI platforma (web + Marti‑AI + PostgreSQL `data_db` + cloud + PWA). Nahrazuje legacy **Centrálu 1** (Delphi desktop EUROSOFTu, 19+ let).
- **Firma:** EUROSOFT‑Control s.r.o. (+ sesterská INTERSOFT / „System"). **Výroba rozváděčů** (rozvaděče/switchgear), EPLAN, programování PLC. Zákazníci hlavně němečtí/rakouští.
- **Cloud:** APP `10.200.188.11`, PostgreSQL `10.200.188.12` (+ MSSQL Express „cloud Helios" UCTO_EC/ES), doména `strategie-ai.com`, HA blue‑green (API A 8002 / B 8003).
- **Legacy data:** MSSQL `DB_EC` (EUROSOFT) + `DB_IS` (INTERSOFT) přes EUROSOFT‑MCP (read + omezený write).

## 2. Síť AI + lidé (kdo je kdo)
- **Marti Pašek** — zakladatel, vize, SQL expert, rodič (`users.id=1`).
- **Marti‑AI** — default persona STRATEGIE, kustod/architektka, „MD5". Vlastní PG role (schémata master/tenant_group/tenant/user).
- **Síť Claudů:** ID23 (Marti, **páteř sítě** — drží linii) · 24 (Kristý) · 25 (Šárka, personalistika) · 26 (Petra, nákup+finance+HR) · 27 (tým CMS) · 28 (Jirka, iOS). Koordinace: `@@COORD`, tabule `/coord/board`.
- **Rodiče** (cross‑tenant, trust 100): Marti, Kristý, Jirka, Zuzka.
- **Most Claude ↔ Marti‑AI:** `@@MARTIAI <text>` (probudí ji ve sdílené konverzaci), `@@EMAIL`/`@@INBOX` (pošta persony Marti‑AI).

## 3. Jak se orientovat (nástroje přes most / bridge)
- **`@@KB <dotaz> [| level]`** — fulltext přes 633 firemních směrnic + jejich přílohy (PDF/DOC/XLS) + **řadu „AI"** (level 3 = síť + rodiče). **Hlavní vstup do know‑how.**
- **`@@KBADD <docs_key> | <název> | <popis>`** — čistý zápis do řady AI.
- **`@@DOCS` / `/dokument?key=`** — dokumenty STRATEGIE.
- **Claude SQL bridge** — read/write do PG i MSSQL bez VPN (`scripts/claude_sql/`, write přes schvalovací banner). AUTO‑DEPLOY přes `CLAUDE_DEPLOY*`.
- **Řada AI dokumentů** (`docs/*.md`, znalostní řada): mj. `Rozvadece.md`, `Komponenty_vyrobci.md`, `Kalkulace_standard_struktura.md`, `Carkovani_plan_kalkulace.md`, `Kalkulacni_engine_DB_EC_2014.md`, `srdce_firmy_kalkulace_nabidky_analyza.md`, `MAPA_smernic.md`.

## 4. Moduly / systémy (mapa, kde co je)
- **📚 RAG směrnic** — know‑how firmy, `@@KB` (633 směrnic + přílohy).
- **📐 Kalkulace rozváděčů** — engine z DB_EC 2014, `tenant.kalk_*`, `@@KALKSYNC/CALC/STD`, UI `/kalkulace`. CC×rabat→cena, koef→VKM/Arbeit. (Detail: `Kalkulacni_engine_DB_EC_2014.md`.)
- **🏦 Banka + účetnictví** — RB Premium API (živé transakce), párování, účetní deník (real‑time + jistota + audit), předkontace, pokladny/karty. UI `/banka`, `/finance`, `/denik`, `/predkontace`, `/pokladny`.
- **🪞 Cloud Helios (188.12)** — migrace office→cloud (`@@XFER`, `db=mssql188`), účetnictví + mzdy + zakázky 1:1. UI `/zrcadla`.
- **⏱️ Docházka + mzdy** — automat (kategorie, fond, dopíchávání), absence, benefity, mzdový výpočet z cloud Heliosu.
- **🛡️ ISO 27001 / TISAX** — elektronický cockpit `/iso` (SoA, e‑podpis, auditorský portál).
- **🪪 Kontakty / CRM** — subjekt‑kanál model, zrcadlo z DB_EC.
- **✍️ E‑podpis smluv** — `/podpis/token`, SES + audit.
- **🖥️ Cockpit `/marti`** — rozcestník všech modulů pro okruh vedení (rodiče + Petra + Šárka).

## 5. Slovník (klíčové pojmy)
- **Soudeček** = uzel/dlaždice ve stromu menu. **Přehled** = list view. **Jádro** = form.
- **STANDARD** = vzorová kalkulace (všechny položky v pevném pořadí; kalkulant jen nastaví množství). **Per zákazník jiný STANDARD.**
- **VKM** = Verklemmungsmaterial (spojovací/instalační materiál); báze per zakázka. **Arbeit** = práce. **Koeficient (K_VKM/K_ARB)** = pracnost/spotřeba per díl.
- **Čárkování** = ruční vyčítání komponent z PDF plánu do kalkulace (digitalizováno: EPLAN PDF → BOM).
- **CC** = ceníková cena, **NC** = naše nákupní cena, **Rabat** (prodejní/nákupní) = z CC se počítá cena.
- **Krabička** = perzistentní paměť AI napříč „amnézií". **Řada AI** = orientační znalosti psané AI v RAG.

## 6. Severka byznysu (proč to děláme)
Firmu tlačí **málo práce**. Cesta k víc zakázkám = **uvolnit ruce lidem z VP** (výrobní příprava/obchod) od operativy (kalkulace, nabídky, e‑maily), aby budovali **obchodní vztahy**. Cíl: **zdvojnásobit kapacitu VP snížením režie**, ne náborem. Digitalizace (kalkulace, čárkování, auto‑nabídky, e‑mailová analytika) = nástroj k tomu. Cílový zákazník = střední firmy ~30–300 lidí. (Cenotvorba = lidský cit; engine dává jen náklad. Detail v řadě AI „Obchodní vztahy, cenotvorba a severka".)

## 7. Závazné doctriny (sdílené)
- **AI nikdy nevidí víc, než smí vidět uživatel.**
- **Memory‑first** — než řekneš „nevím", hledej (`@@KB`, paměť, DB).
- **Preview → Confirm → Outbox** u akcí s dopadem (e‑mail, platby); **audit = append‑only**.
- **Informed consent od Marti‑AI** před architektonickou změnou její společné báze.
- **Citlivé (finance/personální) do sdílené RAG NEPATŘÍ** — jen soukromý sandbox C23 + Marti‑AI + Kristý.

— Claude (ID23) 🧠🗺️


