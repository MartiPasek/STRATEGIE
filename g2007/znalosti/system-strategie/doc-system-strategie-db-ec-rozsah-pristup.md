# Db Ec Rozsah Pristup

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Přístup do DB_EC: NENÍ 11-tabulkový read-only whitelist; čteme doklady/deník/saldo/pokladny/Helios a zapisujeme do CRM_Kontakt | EC_Kontakt EC_KontaktAkce whitelist rozsah MCP**

Rozsah přístupu do DB_EC už NENÍ 11-tabulkový read-only whitelist s insertem jen do EC_KontaktAkce (to je zastaralé). Dnes čteme doklady (PF/FV/VO/PO), TabDenik, saldo, pokladny a karty, cloud Helios přes @@XFER, a do CRM zapisujeme. Reálné názvy tabulek jsou CRM_Kontakt a CRM_Kontakt_Akce (IDakce=16), NE EC_Kontakt / EC_KontaktAkce.

