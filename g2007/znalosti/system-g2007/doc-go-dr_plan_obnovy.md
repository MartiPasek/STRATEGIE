# Plán obnovy STRATEGIE (BCP/DR) — kontinuita provozu a obnova po havárii

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Plán obnovy STRATEGIE (BCP/DR) — kontinuita provozu a obnova po havárii

**Zdroj:** `plan_obnovy_STRATEGIE_2026-07-11_v1.pdf` (V1.0, 11. 7. 2026, autor Marti-AI, odeslán vedení EUROSOFT + IT + Mózer, fwd Marti → p. Antoš). Cíl plného spuštění **do 1. 8. 2026**. Klasifikace: Důvěrné (interní sdílení v síti Claudů + Marti-AI je v pořádku, ne pro veřejnou/externí RAG publikaci).

## Klíčová myšlenka
STRATEGIE neřeší obnovu po havárii plánem „v šuplíku", který se v krizi teprve rozjíždí. **STRATEGIE JE svým plánem obnovy** — záložní systém neběží až ve chvíli havárie, ale **nonstop, každý den, vedle ostrého provozu.**

## 1. Architektura — dvě živé instance souběžně

| Prostředí | Doména | Data | Server | Zálohy DB |
|---|---|---|---|---|
| Ostrý provoz | **strategie-ai.com** | aktuální | **Praha** (cloud 10.200.188.x) | 30 dní |
| Živá záloha | **strategie-system.com** | ≤ 1 prac. den starší | **Plzeň** | 30 dní |

Obě instance běží nonstop a souběžně. Každý pracovní den se po záloze přenese obraz DB z Prahy do Plzně. Geografické oddělení Praha–Plzeň kryje lokální výpadek infrastruktury. (strategie-system.com už v ekosystému existuje: `app.strategie-system.com` = Capcom6 webhook; právní entita **EUROSOFT-System s.r.o.**, Nepomucká 1335/259, Plzeň.)

## 2. Postup obnovy — jeden krok
Ostrý provoz nedostupný? **Uživatel zadá `strategie-system.com` místo `strategie-ai.com` a pracuje dál** — nic se nespouští, nic nepřepíná, záloha už běží. Data jsou nanejvýš o 1 pracovní den starší.

Failback po obnově ostrého prostředí: lidé se vrátí na strategie-ai.com, denní přenos Praha→Plzeň pokračuje automaticky.

Na záložním prostředí lze navíc obnovit **kteroukoli z 30 denních záloh DB** (pro ostrý i záložní provoz) — kryje logickou chybu, ransomware i nechtěné smazání. Naplňuje pravidlo **3-2-1**.

## 3. Cílové parametry
- **RPO ≤ 1 pracovní den** — data z předchozího dne vždy dostupná.
- **RTO prakticky okamžitě** — záloha běží nonstop, žádné spouštění.
- **Historie záloh 30 dní** — obnovitelná pro ai.com i system.com.
- **Testování obnovy každý pracovní den** — ranní rozjezd system.com = reálný test.

## 4. Samokontrola — denní „deník obnov"
Kontrola nevisí na člověku — provádí ji systém sám každé ráno jako součást ranního rozjezdu záložního prostředí. Ověřuje: obnova bez chyby · DB online a konzistentní · data přesně o 1 den stará (dle časového razítka) · klíčové tabulky mají rozumné počty záznamů · aplikace běží a odpovídá · řetěz 30 záloh je kompletní.

Výsledek se publikuje jako **OK / NENÍ OK + důvod + čas** na stavovou stránku, do cockpitu a do aplikace; při chybě jde push notifikace. Vzniká strojově psaný denní deník obnov = důkaz pro audit.

## 5. Přesah — e-mailová data (Exchange)
Součástí 30denní historie jsou i obrazy klíčových e-mailových dat z Exchange serveru EUROSOFTu. Jedním řešením se kryjí dva systémy.

## 6. Role a odpovědnosti
- **Systém (automaticky):** provádí a ověřuje obnovu každé ráno, publikuje výsledek, posílá alert při chybě.
- **STRATEGIE core (Marti + AI):** vlastník návrhu, reakce na kritický incident, rozvoj systému.
- **Provoz / IT:** reaguje na alert, provádí failback na ai.com po obnově — systém hlídá i bez něj.
- Napojení na ISO/TISAX vlastnictví: **Michal Šik = plán obnovy + správa hesel**, **Mísa (Michaela Hladíková) = dotažení ISO 27001 + TISAX do finále** (viz `iso27001_plan_obnovy_michal.md`, `infrastruktura_tutorial.md` §3 restore drill, `digitalizace_eurosoft_prehled.md`).

## 7. Realizační plán (do 1. 8. 2026)
- Týden 1 — datový kanál Praha↔Plzeň — *v realizaci*.
- Týden 2 — ranní obnova + 30denní zálohovací historie — *v realizaci*.
- Týden 3 — samokontrola + stavové hlášení — *plánováno*.
- Do 1. 8. 2026 — plné spuštění, denní deník obnov aktivní — *cíl*.

## 8. Soulad ISO 27001 / TISAX
Dostupnost a kontinuita služby · zálohování s retencí a ověřenou obnovitelností (30 dní) · denně testovaná obnova s datovaným záznamem (důkaz pro audit) · odolnost vůči incidentu (oddělená lokalita + body v čase) · nezávislost na jednotlivci (systém provádí a ověřuje sám). Plán splňuje a překonává požadavek normy „do 24 h rozběhnout s adekvátními daty" — RTO je prakticky okamžité.

## Provozní vazba — zálohy na 188.12 (Praha), building block plánu
Praha = pilíř „Ostrý provoz · 30 dní". Fyzicky na SQL serveru **10.200.188.12**, disk **E: (jen ~10 GB)**:
- Task **STRATEGIE-data-db-backup** (3:00, SYSTEM) → `C:\scripts\backup_data_db.ps1` → `E:\STRATEGIE\RRRR-MM-DD\data_db_HHMMSS.dump` (pg_dump -Fc -Z6).
- Task **STRATEGIE-PG-Backup-Prune** (3:30) → `C:\Scripts\prune_pg_backups.ps1` (bez argumentů → default `$KeepDays`/`$MinKeep`) = aktivní retence.
- **19. 7. 2026:** malý 10GB disk přetékal (15 dumpů, 1,96 GB volno) → retence snížena **KeepDays 14→11** (MinKeep 7) přímo na serveru → ~4 GB volno, drží se ~12 záloh.
- Alert „nedostatek místa" = `_DISK_MON_THRESHOLD_MB=2048` (< 2 GB volných → push 1×/den/disk).
- Pozor: `C:\scripts\*` na 188.12 jsou samostatné kopie, NE z gitu — měnit přímo na serveru přes RDP (device bridge = ec-martin, SQL most = jen SQL; ani jedno na filesystem 188.12 nedosáhne). Repo `scripts/ops/prune_pg_backups.ps1` má default 14 → dosynchronizovat na 11 (TODO).


