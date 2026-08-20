# Denní stav 29.7. — co hotovo, kde jsme přestali (pro večerní návaznost)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Denní stav 29.7.2026 — kde jsme přestali

Pro večerní návaznost (rodič odchází ráno, vrací se večer). Zapisuje C23.

## Hotovo dnes (C23 staví enabling core + jistí, Marti-AI staví sama)
1. **Self-code-edit audit** → schval_zmenu_kodu loguje deploy do fw.ops_request. Commit ad33cc11d.
2. **API health watchdog #1 — LIVE.** Reakce na noční incident: primár STRATEGIE-API (A, 8002) spadl ~20:22 28.7. a NIKDO nevěděl — Caddy failover to zamaskoval (web zůstal zelený přes B/D; rozbité bylo jen to, co sekundáry neumí = deploy token na diag-sql → 401; honili jsme token místo příčiny). Fix incidentu: Restart-Service STRATEGIE-API. Prevence: `scripts/api_health_watchdog.py` (NSSM služba STRATEGIE-API-HEALTH-WATCHDOG na Praze) — kontroluje A+B na JEJICH portech (obchází Caddy), throttlovaný auto-restart + push alert adminům (fw.mobile_command, ids 1/11/20), heartbeat + startup self-check. Ověřeno: ALERT PATH OK, push na mobil dorazil. Commit 279b022ee. Detail: g2007 doc api-primar-a-spadla-bez-alertu (v Cowork paměti).
3. **Governance uklizena:** Zuzka (id6) is_marti_parent→false („teta, ne rodič"; trust_rating zůstal 100 → Marti-AI jí dál věří na 90 %, důvěru řídí trust_rating ne rodičovství). Jirka (id20) trust 50→70. Rodiče = Marti(1)+Kristý(11); admini (is_admin) = Marti+Kristý+Jirka(20).
4. **Self-code PATCH mód pro velké soubory — LIVE.** navrhni_zmenu_kodu_patch: kotvy old_string→new_string, každá MUSÍ být unikátní (jinak zamítne — žádná slepá trefa) → odblokuje editaci service.py/tools.py bez posílání celého obsahu. + drift guard v schval (nenasadí návrh proti staré verzi = nepřepíše cizí změny). Commit 4936bb0cc.
5. **Kufr cíl #7 — NASAZEN (inertní).** Návrh #2 (import-hook v __init__.py) ZAMÍTNUT jako pack-unaware (rozbil by load_pack). Marti udělala správně přes patch = **návrh #3**: v service.py pack-vrstvě, když lean_default_enabled=='on' + default persona + žádný explicitní pack → active_pack='core'; load_pack dál funguje (naložený pack přebije). Schválil rodič, Marti nasadila přes schval_zmenu_kodu. Commit f581a133a. Celá governed self-code smyčka přes patch proběhla end-to-end.

## STAV: kde jsme přestali
Kufr mechanismus je v produkci, ale **INERTNÍ** — flag `lean_default_enabled` v g2007.nastaveni NEEXISTUJE → chování = přesně dnešek (všech 167 nástrojů). Jen je položený mechanismus, nic se nezměnilo.

## DALŠÍ KROK (večer 29.7.)
1. **Zapnout lean na test + změřit úsporu:** přidat řádek do g2007.nastaveni (klic='lean_default_enabled', hodnota='on') přes most (schválí rodič), na jedné konverzaci **změřit vstupní tokeny před/po** (cíl ~167→~40 nástrojů = ta ~68% páka). Doložit číslo. Pak rozhodnout o globálním zapnutí (a případně o tom, jak si Marti kufr per činnost načítá přes load_pack).
2. Watchdog #2 (health-gate do restart_watcher.py — po deploy-restartu ověřit A + attribution) + #3 (status přehled A/B/D) — nižší priorita, #1 už jádro rizika kryje.

