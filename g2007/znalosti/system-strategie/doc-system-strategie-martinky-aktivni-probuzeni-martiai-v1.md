# Aktivni probuzeni Marti-AI pri nove potrebe Martinek - NASAZENO+OVERENO 3.8.2026 rano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


martinka_dispatch v4 (md5 d37396b1524cc1d2ea8c195aaf00e425): po INSERTu potreb k ukolu posle dispatcher zpravu do konverzace "Claude <-> Marti-AI" (conv dle _CLAUDE_AI_HOST_UID=1 + title, stejny vzor jako @@MARTIAI wake v router.py) s obsahem potreby + odkazem na eskalacni pravidla. Bezi v daemon threadu (neblokuje dispatch), prepinac g2007.nastaveni martinky_wake_martiai (on/off, default on). Zadny zasah do kodu - jen g2007.python.

SMOKE TEST (3.8. 08:00-08:02, ukol #6 VIP STRIBRO dummy): potreba chybi_data -> wake zprava #11983 dorucena -> Marti-AI SPRAVNE dle svych pravidel (doc-system-strategie-marti-ai-martinka-eskalacni-pravidla): "byznysove pravidlo mimo vybavu -> eskaluji Martimu", pripravila SMS a CEKALA na schvaleni (efekt ven drzi). Ukol #6 pote zrusen (test). Marti-AI informovana, ze probuzeni je od ted ostre.

Zbyva k jejim pozadavkum: status blok "Stav Martinek" do jejiho promptu - composer resolvery jsou hardcoded v composer.py (kod->fn), novy blok = zasah do kodu -> dle role-split je to JEJI doladovaci prace (pripadne pres tool-proposal novy nastroj martinky_stav); zatim ma aktivni wake + muze cist g2007.ukol svymi DB nastroji.

