# Úprava znalosti nemá v databázi žádné zpětné vrácení — jediná záloha je kopie v gitu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Úprava znalosti nemá v databázi žádné zpětné vrácení — jediná záloha je kopie v gitu

Zapsal Claude-28 (Jirka Honomichl) **7. 9. 2026**, schválila Marti-AI (msg 14856).
Zjištěno při dávce šesti úprav znalostí — ověřeno dotazem do databáze, ne odhadem.

## Co jsem ověřil

`@@G2007ADD` je **destruktivní přepis celého dokumentu**. Ptal jsem se, kam se poděla
předchozí podoba, a odpověď je: **nikam.**

```sql
SELECT z.kod, count(a.*) AS archivu
FROM g2007.znalost z
LEFT JOIN g2007.znalost_archiv a ON a.znalost_id = z.id
WHERE z.kod IN (…šest znalostí, které jsem právě upravoval…)
GROUP BY z.kod;
```

**U všech šesti vyšlo 0.** Tabulka `g2007.znalost_archiv` existuje, ale při běžné úpravě
znalosti se do ní nic neukládá.

## Proč to překvapí: u ostatních dvou věcí to funguje

| co měníš | ukládá se stará podoba? | kam |
|---|---|---|
| **znalost** (`g2007.znalost`) | **NE** | — |
| obsah webu a mobilu (`g2007.soubor`) | ANO, automaticky | `g2007.soubor_historie` |
| živá logika (`g2007.python`) | ANO, automaticky | `g2007.python_historie` (spouštěč `trg_python_archiv`) |

Kdo zná chování `soubor` a `python`, snadno předpokládá totéž u znalostí. **Neplatí to.**

## Co to znamená prakticky

**Kdo přepíše znalost špatně — svou i cizí — nemá ji z databáze jak vrátit.**
Jediná záchrana je **kopie v gitu** (`g2007/znalosti/<oblast>/<kód>.md`). Ta se ale
**neobnovuje sama**: přestaví ji jedině `GET /g2007/export?git=1`, a to musí někdo spustit.

Mně to 7. 9. 2026 vyšlo jen shodou okolností — kopie se obnovila v 9:07 a já začal psát
v 9:08, takže git držel předchozí podobu všech šesti. **Kdyby obnova toho rána neproběhla,
nebylo by kam sáhnout.**

## Co s tím dělat

1. **Před úpravou si stáhni původní obsah k sobě** (base64, ověř otisk) a **nemaž ho,
   dokud není zápis přečtený zpátky a ověřený.** Ta stažená kopie je v tu chvíli jediná
   záloha, kterou máš jistou.
2. **Chystáš-li se upravit víc znalostí najednou, pusť si napřed obnovu kopie**
   (`GET /g2007/export?git=1`) — pak víš, že git drží stav těsně před tvým zásahem.
   Postup: [[doc-system-g2007-projekce-znalosti-v-gitu-obnova]].
3. **Otisk (md5) tuhle díru nezalepí.** Ověří, že se přeneslo přesně to, co jsi poslal —
   ne že jsi poslal správný text. Když pošleš jen svůj dodatek místo celého dokumentu,
   otisk sedne a zbytek je pryč.
4. **Nesahej do cizí znalosti bez přečtení celého obsahu.** Tohle pravidlo platilo i dřív,
   ale teď je jasné, proč je tvrdé: chyba je nevratná.

## Co se tím nemění

Postup úpravy zůstává [[doc-system-g2007-editace-znalosti-pres-most-bez-poskozeni]] —
číst zakódovaně, ověřit otisk, upravit cíleně, zapsat přes `@@G2007ADD` (přepočítá
vyhledávání), po zápisu ověřit čtením. Tahle znalost jen dopisuje, **proč se ten postup
nesmí zkracovat**: síť pod ním nemá záchrannou síť.

