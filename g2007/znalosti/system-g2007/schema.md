# Schéma g2007 — dva světy

> oblast: `system-g2007` · úroveň: system · typ: architektura · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schéma g2007 — dva světy

Schema `g2007` drží dva provázané světy:

**Skladač promptu.** `graf` (seznam map, Krok 0), `graf_krok` (kroky = části promptu; vrstva trvalé/živé; zdroj dat), `graf_prechod` (přechodové/rozhodovací podmínky mezi kroky — mj. větev OK/CHYBA).

**Kdo, čím a co smí.** `entita` (kdo reálně — člověk/persona, měkký odkaz na uživatele), `profese` (role), `kufr` + `kufr_nastroj` (co persona nese), `nastroj` (schopnosti), `cinnost` + `cinnost_nastroj` (úkon a nástroje do ruky). Doktrína: **kvalifikace patří entitě, ne profesi.**

Verzování: entity i znalosti se archivují (`*_archiv` + trigger) při schválení nové verze. Přepínač `nastaveni.composer_mode` rozhoduje starý/nový composer (default off).

