# Banka Parovani

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Párovací engine ~92%: VS→doklad, zpráva→FP, KS 1178=karty; saldo NET ne magnituda**

RB Premium API čte transakce živě (EC+ES účty). Párovací engine (~92% spárováno → účetní deník): (A) opakované přes protiúčet+KS; (B) VS→doklad (řady 600 FV/601 vnitroskupina/800,920 objednávky); (C) zpráva "řada+číslo FP"→přijatá faktura→zakázka; (D) mzdy/daně/pojištění; (E) karty (KS 1178, paymentCardNumber=maskovaný PAN) + pojištění.
SALDO: headline = NET (ABS(SUM(saldo))), NE magnituda (SUM(ABS) lže kvůli rušení +/−). Rozpad: zaplaceno-nespárováno / vnitroskupina (CisloOrg 1=sesterská) / reálně otevřené. Platby = prohibited pro AI (návrh→podpis člověka v IB).

