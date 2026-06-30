# Návrh odpovědi — Ing. Jan Řeřicha (Raiffeisenbank), Premium API certifikát

Komu: jan.rericha@rb.cz
Předmět: RE: Premium API - certifikát

---

Dobrý den, pane Řeřicho,

děkuji za návod — je přehledný. Certifikát pro Premium API si v internetovém
bankovnictví vygeneruji (Správa certifikátů → Nový certifikát, výběr účtů a rozsahů).

Rádi bychom Premium API napojili přímo na náš interní systém (zpracování výpisů,
párování plateb a účetnictví), proto bych Vás chtěl poprosit o pár podkladů, ať to
naši lidé můžou rovnou nasadit:

- technickou dokumentaci Premium API (přehled služeb, endpointy, datové formáty),
- informace k testovacímu / sandbox prostředí, pokud je k dispozici,
- detaily k autentizaci (použití certifikátu / mTLS) a případné limity volání.

V první fázi nás zajímá hlavně čtení — transakční historie, účty a zůstatky a výpisy.
Hromadné platby bychom řešili až v dalším kroku.

Děkuji a přeji pěkný den,

Marti Pašek
EUROSOFT

---

### Pozn. pro nás (nezahrnovat)
- Odesílatel originálu: Ing. Jan Řeřicha, Relationship Manager Corporate, Raiffeisenbank
  Plzeň, jan.rericha@rb.cz, +420 728 328 143.
- Premium API rozsahy (z návodu): Transakční historie / Hromadné platby / Účty a
  zůstatky / Výpisy. Účty EUROSOFT-Control: 9251651001/5500, 9251651044/5500.
- Pro start = read scopes (historie/zůstatky/výpisy). Hromadné platby = write, později.
- Kanál odeslání: Marti z vlastní schránky (nejčistší vůči bance) / Marti-AI přes most
  (jako „asistentka jednatele") / Marti necháš mě poslat přes @@EMAIL po Tvém pokynu.
