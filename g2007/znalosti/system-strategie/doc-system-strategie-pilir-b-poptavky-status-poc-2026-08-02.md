# Pilir B (automaty stavu domeny) - prvni POC hotovy a naostro bezi (2.8.2026): g2007.automat rozsiren, prvni domenovy automat poptavky_status generuje status_block, injekce do promptu pripravena. Otevrena architektonicka mezera: permission_tier

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Kontext:** Navazuje na #313/#314 (triaz dokoncena, eskalace overena). Marti 2.8.2026: "pokracuj tedy na ty eskalaci [uz hotovo, viz #314]. Pak mi priblizi ten pilir B" -> vysvetleno v chatu -> Marti: "Eliska je prvnim kandidatem tohoto smeru plus Kristy a ja. Muzes pokracovat." Tento dokument zaznamenava co je hotovo a jednu otevrenou architektonickou otazku, kterou je potreba vyresit pred aktivaci pro konkretni lidi.

## Co je hotovo a nasazeno (commit c14a84eaa)

1. `g2007.automat` rozsiren o `domain_kod` (FK na `tool_domain.kod`), `status_block` (text), `status_block_updated_at` (ALTER schvaleno bannerem, request #1658).
2. Novy soubor `modules/erp/api/automat_domeny.py` (vzor `automat_eskalace.py` - rozsiruje `automat.py` bez zasahu do jadra). Prvni funkce `_check_poptavky_status(sg)`: cte `tenant.vp_poptavka`, stavi citelny `status_block` (kolik skutecnych poptavek, jaka jistota, zakaznik/predmet, kolik ostatnich e-mailu) a rovnou ho zapisuje do `g2007.automat.status_block`. Registrovano do `automat.py`'s `_CHECKS` pres `DOMAIN_CHECKS` dict (stejny vzor jako `WATCHERS`).
3. Novy radek v `g2007.automat`: `kod='poptavky_status'`, `domain_kod='poptavky'`, `interval_min=15`, `aktivni=true` (INSERT schvaleno bannerem, request #1659).
4. `service.py`: pokud `conversation.active_domain` je nastaveny, injektuje se nejcerstvejsi `status_block` pro tu domenu do system_promptu (za existujicim tool-filtr blokem ze stejneho mista v kodu). NULL `active_domain` (dnes VSECHNY konverzace) = presne dnesni chovani, no-op.
5. **Overeno naostro 2.8. 10:50 UTC:** existujici background scheduler (`_automat_sched_loop`, tik kazdych 60s, bezi v threadpoolu, NEBLOKUJE event loop) automat vyzvedl automaticky (nova `interval_min=15` s `last_run_at IS NULL` = ihned due), spustil, `last_status='ok'`, a vygeneroval status_block:
   `[STAV DOMÉNY: poptávky — čerstvý právě teď] Skutečné poptávky (AI klasifikace, Fáze 3): 4. Ostatní e-maily v mailboxu (provozní/ostatní, NE poptávky): 196. [4 konkretni radky se zakaznikem/predmetem/jistotou]. Čeká na kalkulaci/nabídku: sledování zatím nepostaveno (Fáze 4 pipeline chybí).`
   Cely retezec automat->scheduler->status_block->pripraveno k injekci je funkcni od zapisu az po cteni, ne jen teoreticky.

## OTEVRENA OTAZKA (blokuje aktivaci pro konkretni lidi): permission_tier zije na sdilene AI persone, ne na cloveku

Overeno 2.8. primo v kodu (`service.py` ~11549): `_persona_tier = persona.permission_tier`, kde `persona` = AKTIVNI AI PERSONA konverzace (`conversations.active_agent_id` -> `personas.id`). Overeno v datech: `personas` ma jen 4 radky (Marti-AI, PravnikCZ-AI, PravnikDE-AI, Honza-AI) - vsechny AI identity, zadny clovek. `personas.permission_tier` tedy rozlisuje MEZI AI OSOBNOSTMI (napr. Honza-AI by mohl mit jiny tier nez Marti-AI), NE mezi lidmi, kteri pouzivaji STEJNOU Marti-AI personu (id=1, tier='parent', is_default=true).

Dusledek: kdyz Eliska (`users.id=34`, `is_marti_parent=false`) zacne konverzaci s Marti-AI (coz je podle #281 rozhodnuti #2 - "Martinka = Marti-AI, ne nova identita" - JEDINA spravna cesta, zadny novy radek v personas), jeji `persona.permission_tier` bude 'parent' stejne jako u Martiho/Kristy, protoze cte se to ze sdilene Marti-AI persony, ne z jejiho uctu. Dnesni kod tedy NEUMI odlisit Elisku od Martiho podle tieru, i kdyz `conversations.active_domain` by uz slo nastavit per-konverzace bez problemu.

`users` tabulka ma uz existujici `is_marti_parent` (bool) - ale to je STARSI/JINY mechanismus (pouzivany jen v `exec_approval.py` pro schvalovani exec prikazu), ne totez co novy trojstupnovy `parent/domain_lead/domain_user` tier.

**Navrh reseni (k potvrzeni Martimu/Kristy, zadny kod zatim nezmenen):** pridat `permission_tier` na `users` (ne jen `personas`), a v `get_effective_tools()` cist efektivni tier jako "tier uzivatele (`conversations.user_id` -> `users.permission_tier`), pokud je nastaveny; jinak tier persony jako dnes (fallback, zadna regrese pro AI-personas jako Honza-AI)". Malá, bezpecna zmena (jeden dalsi sloupec + jedna vetev v uz existujicim kodu), ale je to zmena mimo puvodni schvaleny plan #281, tak si zaslouzi kratke potvrzeni pred implementaci.

## Dalsi krok

Cekame na potvrzeni navrhu vyse (nebo jine reseni od Martiho/Kristy), pak: pridat `users.permission_tier`, priradit Elisce `domain_user` nebo `domain_lead` pro `poptavky` (Kristy/Marti zustavaji efektivne 'parent' bez zmeny), nastavit `active_domain='poptavky'` na jejich prislusne konverzaci, a rucne проверить `get_effective_tools()` prefiltruje spravne (uz nasazeny kod z drivejsiho kola, jen dosud nepouzity).

_Zapsano Claude-23, 2.8.2026. Navazuje na #280, #281, #283, #313, #314._

