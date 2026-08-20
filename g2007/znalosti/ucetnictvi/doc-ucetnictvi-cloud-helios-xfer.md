# Cloud Helios Xfer

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Cloud Helios (mssql188 UCTO_EC/ES) plněný z office přes @@XFER; JEN účetnictví, žádné doklady**

Cloud Helios = MSSQL na 188.12 (DB UCTO_EC / UCTO_ES), nový účetní systém. Most db=mssql188 (pyodbc, legacy ovladač {SQL Server}, port 1433 default instance). Přenos z kancelářského Heliosu (DB_EC) přes @@XFER <src> <dst> <Tabulka> (1:1 vč. původních id, IDENTITY_INSERT). ES čti cross-db přes DB_EC: [DB_IS].dbo.
Cloud Helios drží JEN účetnictví (TabDenik), ŽÁDNÉ doklady (Helios upgrade zakládá FK → padá na dangling; doklady vyprázdnit/NULL). Migrační hub /zrcadla. Účetní přes Guacamole (prohlížeč→RDP, bez VPN).

