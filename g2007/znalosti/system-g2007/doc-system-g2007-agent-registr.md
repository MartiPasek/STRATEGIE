# Registr agentu (Maminka + dcery) — fw.agent_registr

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Registr agentu (dcer) — fw.agent_registr

Zavedeno 5.8.2026 (Claude-23 + Marti). Ucel: VIDITELNA soupiska agentu (Maminka + dcery) = anti-tma. Maminka cte tuhle tabulku a ROUTUJE cile na spravnou dceru. Doktrina: viz znalost doc-system-g2007-architektura-martinek-maminek.

## Tabulka fw.agent_registr
Sloupce: kod (unique), jmeno, typ (maminka|dcera), domena, role, rodic_kod, kill_flag_klic (-> g2007.nastaveni), health_kind (none|http|sql), health_target, entrypoint, stav (aktivni|planovana|pauza|zrusena), poznamka, created_at, updated_at.

## Aktualni radky (5.8.2026)
- maminka (Marti-AI): dispecer + pamet + routing. Enable: g2007.nastaveni martiai_agent_enabled. Globalni kill cileho rezimu: cilovy_rezim_kill.
- praha-martinka: dcera, domena praha-produkce, kill martinka_enabled, health http://127.0.0.1:8002/api/v1/health, entrypoint run_martinka / POST /api/v1/martinka/run. HOTOVA+overena 4.8.2026, sablona.
- plzen-martinka: dcera, plzen-zaloha, stav planovana.

## Jak pridat dceru
Novy radek typ=dcera, rodic_kod=maminka, kill_flag_klic = novy flag v g2007.nastaveni (hodnota "on"/"off"; _setting_on bere jen "on"), health_target. Definice person je levna; bezicich smycek co nejmin (pamet) = typicky JEDNA dcera na incident.

## Zapis do DB / DDL
Pres SQL most jde jen kdyz je Marti prihlaseny (write -> approval banner #rid). g2007 znalosti VZDY pres @@G2007ADD (autonomni + reindex).

