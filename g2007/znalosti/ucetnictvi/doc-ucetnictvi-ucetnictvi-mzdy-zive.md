# Ucetnictvi Mzdy Zive

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Účetnictví JE živé: tenant.ucetni_denik (537 zápisů) + Systém C mzdy (c_smlouva/c_vyplatnice, /mzdy-c); NENÍ plánováno | ucetni denik mzdy System C cloud Helios XFER**

Účetnictví není "plánováno" — je živé. tenant.ucetni_denik má 537 zápisů (~50,9 mil Kč, real-time engine + jistota + audit). Mzdy jedou přes Systém C: tenant.c_smlouva + tenant.c_vyplatnice, stránka /mzdy-c (v přehledech někdy chybí — doplnit). Cloud Helios (UCTO_EC/UCTO_ES na mssql188) plněný přes @@XFER také běží.

